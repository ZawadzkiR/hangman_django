import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .forms import CreateRoomForm, DIFFICULTY_CHOICES, JoinRoomForm, SaveScoreForm, StartGameForm
from .models import GameSession, MultiplayerParticipant, MultiplayerRoom, Player, Word
from .services import (
    UI_LANGUAGE_CHOICES,
    all_ready,
    calculate_word_score,
    choose_word,
    current_stats,
    get_max_mistakes,
    deserialize_guessed,
    ensure_session_token,
    finalize_room_if_needed,
    generate_room_code,
    get_equivalent_letters,
    normalize_word,
    player_round_stats,
    resolve_ui_language,
    room_state,
    room_seconds_left,
    serialize_guessed,
    start_room_round,
    sync_participant_word,
    t,
)

SESSION_KEY = 'hangman_game'
LAST_PLAYER_KEY = 'hangman_last_player'
ROOM_KEY = 'hangman_room_code'


def category_choices(language=None):
    qs = Word.objects.filter(is_active=True)
    lang = language or 'en'
    if lang:
        qs = qs.filter(language=lang)
    if not qs.exists() and lang == 'cs':
        qs = Word.objects.filter(is_active=True, language='sk')
    cats = sorted(set(qs.values_list('category', flat=True)))
    return [('random', 'Random')] + [(c, c) for c in cats]


def _base_context(request):
    ui_lang = resolve_ui_language(request)
    return {'ui_lang': ui_lang, 'tr': t(ui_lang), 'ui_language_choices': UI_LANGUAGE_CHOICES}


def _make_game_state(language, difficulty='random', category='random', mistake_mode='medium', score=0, streak=0, rounds=0, used_word_ids=None):
    used_word_ids = used_word_ids or []
    word = choose_word(language, difficulty, category, used_word_ids)
    return {
        'word_id': word.id,
        'word': word.text,
        'language': language,
        'category': word.category,
        'hint': word.hint,
        'difficulty': difficulty,
        'selected_category': category,
        'mistake_mode': mistake_mode,
        'mistakes': 0,
        'max_mistakes': get_max_mistakes(mistake_mode),
        'guessed_letters': '',
        'status': 'playing',
        'score_delta': 0,
        'run_score': score,
        'streak': streak,
        'rounds_cleared': rounds,
        'used_word_ids': used_word_ids + [word.id],
        'saved': False,
    }


def _default_nickname(room):
    return f'Player {room.participants.count() + 1}'


def _get_participant(request, room):
    token = ensure_session_token(request)
    participant = room.participants.filter(session_token=token).first()
    if participant:
        return participant
    nickname = _default_nickname(room)
    return MultiplayerParticipant.objects.create(room=room, session_token=token, nickname=nickname, order_no=room.participants.count() + 1, language=resolve_ui_language(request))


def home(request):
    ui_lang = resolve_ui_language(request)
    default_game_lang = ui_lang if ui_lang in {code for code, _ in UI_LANGUAGE_CHOICES} else 'en'
    context = _base_context(request)
    start = StartGameForm(initial={'language': default_game_lang, 'difficulty': 'random', 'mistake_mode': 'medium'})
    start.fields['category'].choices = category_choices(default_game_lang)
    create = CreateRoomForm(initial={'language': default_game_lang, 'difficulty': 'random', 'turn_seconds': 45, 'max_rounds': 10, 'target_score': 120, 'mistake_mode': 'medium'})
    create.fields['category'].choices = category_choices(default_game_lang)
    join = JoinRoomForm(initial={'language': default_game_lang})
    context.update({'form': start, 'create_form': create, 'join_form': join, 'last_player': request.session.get(LAST_PLAYER_KEY, '')})
    return render(request, 'game/home.html', context)


@require_POST
def api_set_ui_language(request):
    language = request.POST.get('language', 'en')
    if language not in {code for code, _ in Word._meta.get_field('language').choices}:
        language = 'en'
    request.session['ui_lang'] = language
    request.session.modified = True
    return JsonResponse({'ok': True})


@require_GET
def api_categories(request):
    language = request.GET.get('language', 'en')
    if language not in {code for code, _ in Word._meta.get_field('language').choices}:
        language = 'en'
    return JsonResponse({'ok': True, 'categories': [{'value': v, 'label': l} for v, l in category_choices(language)]})


@require_POST
def start_game(request):
    form = StartGameForm(request.POST)
    form.fields['category'].choices = category_choices(request.POST.get('language'))
    if not form.is_valid():
        return redirect('home')
    language = form.cleaned_data['language']
    request.session[SESSION_KEY] = _make_game_state(language, form.cleaned_data['difficulty'], form.cleaned_data['category'], form.cleaned_data['mistake_mode'])
    request.session.modified = True
    return redirect('play')


@require_POST
def create_room(request):
    form = CreateRoomForm(request.POST)
    form.fields['category'].choices = category_choices(request.POST.get('language'))
    if not form.is_valid():
        return redirect('home')
    language = form.cleaned_data['language']
    token = ensure_session_token(request)
    code = generate_room_code()
    while MultiplayerRoom.objects.filter(code=code).exists():
        code = generate_room_code()
    nickname = form.cleaned_data['nickname'].strip() or 'Player 1'
    room = MultiplayerRoom.objects.create(
        code=code, host_name=nickname, host_session=token, host_language=language, turn_seconds=form.cleaned_data['turn_seconds'],
        max_rounds=form.cleaned_data['max_rounds'], target_score=form.cleaned_data['target_score'], difficulty_mode=form.cleaned_data['difficulty'], category_mode=form.cleaned_data['category'], mistake_mode=form.cleaned_data['mistake_mode'], max_players=999999,
    )
    MultiplayerParticipant.objects.create(room=room, session_token=token, nickname=nickname, order_no=1, language=language, is_ready=True)
    request.session[ROOM_KEY] = room.code
    return redirect('room', code=room.code)


@require_POST
def join_room(request):
    form = JoinRoomForm(request.POST)
    if not form.is_valid():
        return redirect('home')
    code = form.cleaned_data['room_code'].strip().upper()
    room = get_object_or_404(MultiplayerRoom, code=code)
    token = ensure_session_token(request)
    language = form.cleaned_data['language']
    request.session['ui_lang'] = language
    nickname = form.cleaned_data['nickname'].strip() or _default_nickname(room)
    participant, _ = MultiplayerParticipant.objects.get_or_create(room=room, session_token=token, defaults={'nickname': nickname, 'order_no': room.participants.count() + 1, 'language': language, 'is_ready': False})
    participant.nickname = nickname or participant.nickname
    participant.language = language
    if room.current_translation_key:
        sync_participant_word(room, participant)
    participant.save()
    request.session[ROOM_KEY] = room.code
    return redirect('room', code=room.code)


def play(request):
    game = request.session.get(SESSION_KEY)
    if not game:
        return redirect('home')
    context = _base_context(request)
    context.update({'game': game, 'stats': current_stats(game), 'save_form': SaveScoreForm(initial={'username': request.session.get(LAST_PLAYER_KEY, '')})})
    return render(request, 'game/play.html', context)


def room(request, code):
    room_obj = get_object_or_404(MultiplayerRoom, code=code.upper())
    participant = _get_participant(request, room_obj)
    context = _base_context(request)
    context.update({'room': room_obj, 'participant': participant, 'state': room_state(room_obj, participant, resolve_ui_language(request)), 'is_host': participant.session_token == room_obj.host_session})
    return render(request, 'game/room.html', context)


@require_POST
def api_guess(request):
    game = request.session.get(SESSION_KEY)
    if not game:
        return JsonResponse({'ok': False, 'redirect': '/'}, status=400)
    if game['status'] != 'playing':
        return JsonResponse({'ok': True, 'game': game, 'stats': current_stats(game)})
    raw_letter = request.POST.get('letter', '').strip()
    if not raw_letter:
        return JsonResponse({'ok': False, 'error': 'Missing letter'}, status=400)
    guessed_letters = deserialize_guessed(game['guessed_letters'])
    normalized = normalize_word(raw_letter)
    if not normalized:
        return JsonResponse({'ok': False, 'error': 'Invalid letter'}, status=400)
    letter = normalized[0]
    equivalents = get_equivalent_letters(letter, game['language'])
    word_norm = normalize_word(game['word'])
    already_used = bool(guessed_letters & equivalents)
    hit = False
    if not already_used:
        guessed_letters |= equivalents
        hit = any(ch in equivalents for ch in word_norm)
        if not hit:
            game['mistakes'] += 1
        game['guessed_letters'] = serialize_guessed(guessed_letters)
    stats = current_stats(game)
    modal = None
    if stats['won']:
        gained = calculate_word_score(game['word'], game['mistakes'], True)
        game['score_delta'] = gained
        game['run_score'] += gained
        game['streak'] += 1
        game['rounds_cleared'] += 1
        game['status'] = 'round_won'
        modal = 'won'
    elif stats['lost']:
        game['score_delta'] = 0
        game['status'] = 'lost'
        modal = 'lost'
    request.session[SESSION_KEY] = game
    request.session.modified = True
    return JsonResponse({'ok': True, 'hit': hit, 'already_used': already_used, 'game': game, 'stats': stats, 'modal': modal})


@require_POST
def api_save_score(request):
    game = request.session.get(SESSION_KEY)
    if not game or game.get('status') != 'lost':
        return JsonResponse({'ok': False, 'error': 'No finished run'}, status=400)
    if game.get('saved'):
        return JsonResponse({'ok': True, 'saved': True, 'message': t(resolve_ui_language(request))['saved_ok']})
    form = SaveScoreForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
    username = form.cleaned_data['username']
    if not username:
        game['saved'] = 'skipped'
        request.session[SESSION_KEY] = game
        request.session.modified = True
        return JsonResponse({'ok': True, 'saved': False, 'message': t(resolve_ui_language(request))['saved_skip']})
    player, _ = Player.objects.get_or_create(username=username)
    player.total_score += game['run_score']
    player.games_played += 1
    if game['streak'] > 0:
        player.games_won += 1
    player.save()
    request.session[LAST_PLAYER_KEY] = username
    GameSession.objects.create(player=player, word_id=game['word_id'], word_text=game['word'], language=game['language'], guessed_letters=game['guessed_letters'], mistakes=game['mistakes'], max_mistakes=game['max_mistakes'], score_delta=game['run_score'], result='lost')
    game['saved'] = True
    request.session[SESSION_KEY] = game
    request.session.modified = True
    return JsonResponse({'ok': True, 'saved': True, 'message': t(resolve_ui_language(request))['saved_ok']})


@require_POST
def api_new_round(request):
    game = request.session.get(SESSION_KEY)
    if not game:
        return JsonResponse({'ok': False}, status=400)
    language = game['language']
    reset_score = game.get('status') == 'lost'
    new_game = _make_game_state(language, game.get('difficulty', 'random'), game.get('selected_category', 'random'), game.get('mistake_mode', 'medium'), 0 if reset_score else game.get('run_score', 0), 0 if reset_score else game.get('streak', 0), 0 if reset_score else game.get('rounds_cleared', 0), [] if reset_score else game.get('used_word_ids', []))
    request.session[SESSION_KEY] = new_game
    request.session.modified = True
    return JsonResponse({'ok': True, 'game': new_game, 'stats': current_stats(new_game)})


@never_cache
@require_GET
def api_room_state(request, code):
    room = get_object_or_404(MultiplayerRoom, code=code.upper())
    participant = _get_participant(request, room)
    return JsonResponse({'ok': True, 'state': room_state(room, participant, resolve_ui_language(request))})


@require_POST
def api_room_ready(request, code):
    room = get_object_or_404(MultiplayerRoom, code=code.upper())
    participant = _get_participant(request, room)
    participant.is_ready = not participant.is_ready
    participant.save(update_fields=['is_ready'])
    return JsonResponse({'ok': True, 'state': room_state(room, participant, resolve_ui_language(request))})


@require_POST
def api_room_start(request, code):
    room = get_object_or_404(MultiplayerRoom, code=code.upper())
    participant = _get_participant(request, room)
    if participant.session_token != room.host_session:
        return JsonResponse({'ok': False}, status=403)
    if room.participants.count() < 2:
        return JsonResponse({'ok': False, 'message': t(resolve_ui_language(request))['need_players']}, status=400)
    if not all_ready(room):
        return JsonResponse({'ok': False, 'message': t(resolve_ui_language(request))['need_ready']}, status=400)
    start_room_round(room)
    return JsonResponse({'ok': True, 'state': room_state(room, participant, resolve_ui_language(request))})


@require_POST
def api_room_next_round(request, code):
    room = get_object_or_404(MultiplayerRoom, code=code.upper())
    participant = _get_participant(request, room)
    if participant.session_token != room.host_session:
        return JsonResponse({'ok': False}, status=403)
    if room.status == 'finished':
        return JsonResponse({'ok': True, 'state': room_state(room, participant, resolve_ui_language(request))})
    if room.status != 'round_over':
        return JsonResponse({'ok': False}, status=400)
    for p in room.participants.all():
        p.is_ready = True
        p.save(update_fields=['is_ready'])
    start_room_round(room)
    return JsonResponse({'ok': True, 'state': room_state(room, participant, resolve_ui_language(request))})


@require_POST
def api_room_guess(request, code):
    room = get_object_or_404(MultiplayerRoom, code=code.upper())
    participant = _get_participant(request, room)
    finalize_room_if_needed(room)
    room.refresh_from_db()
    if room.status != 'playing' or participant.round_status != 'playing':
        return JsonResponse({'ok': True, 'state': room_state(room, participant, resolve_ui_language(request))})
    raw_letter = request.POST.get('letter', '').strip()
    normalized = normalize_word(raw_letter)
    if not normalized:
        return JsonResponse({'ok': False, 'error': 'Invalid letter'}, status=400)
    letter = normalized[0]
    guessed = deserialize_guessed(participant.guessed_letters)
    equivalents = get_equivalent_letters(letter, participant.language)
    already_used = bool(guessed & equivalents)
    hit = False
    if not already_used:
        guessed |= equivalents
        hit = any(ch in equivalents for ch in normalize_word(participant.current_word_text))
        if not hit:
            participant.mistakes += 1
        participant.guessed_letters = serialize_guessed(guessed)
        stats = player_round_stats(participant)
        if stats['won']:
            participant.round_status = 'won'
            participant.score += calculate_word_score(participant.current_word_text, participant.mistakes, True, room_seconds_left(room))
        elif stats['lost']:
            participant.round_status = 'lost'
        participant.save()
    finalize_room_if_needed(room)
    return JsonResponse({'ok': True, 'hit': hit, 'already_used': already_used, 'state': room_state(room, participant, resolve_ui_language(request))})


@require_POST
def api_room_leave(request, code):
    room = get_object_or_404(MultiplayerRoom, code=code.upper())
    token = ensure_session_token(request)
    room.participants.filter(session_token=token).delete()
    if not room.participants.exists():
        room.delete()
    else:
        first = room.participants.order_by('order_no', 'joined_at').first()
        if first and room.host_session == token:
            room.host_session = first.session_token
            room.host_name = first.nickname
            room.save(update_fields=['host_session', 'host_name'])
    request.session.pop(ROOM_KEY, None)
    return JsonResponse({'ok': True, 'redirect': '/'})




@require_GET
def manifest(request):
    payload = {
        'id': '/',
        'name': 'Wisielec',
        'short_name': 'Wisielec',
        'description': 'Multilingual hangman game',
        'start_url': '/',
        'scope': '/',
        'display': 'standalone',
        'background_color': '#1e7b57',
        'theme_color': '#1e7b57',
        'icons': [
            {'src': static('game/icons/icon-192.png'), 'sizes': '192x192', 'type': 'image/png'},
            {'src': static('game/icons/icon-512.png'), 'sizes': '512x512', 'type': 'image/png'},
            {'src': static('game/icons/maskable-512.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    }
    return HttpResponse(json.dumps(payload), content_type='application/manifest+json')


@require_GET
def service_worker(request):
    js = f"""
const CACHE_NAME = 'hangman-shell-v2';
const URLS = [
  '/',
  '/leaderboard/',
  '/history/',
  '/offline/',
  '{static('game/css/style.css')}',
  '{static('game/js/app.js')}',
  '{static('game/icons/icon-192.png')}',
  '{static('game/icons/icon-512.png')}',
  '/manifest.webmanifest'
];

self.addEventListener('install', (event) => {{
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(URLS)).then(() => self.skipWaiting()));
}});

self.addEventListener('activate', (event) => {{
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
}});

self.addEventListener('fetch', (event) => {{
  if (event.request.method !== 'GET') return;
  if (event.request.mode === 'navigate') {{
    event.respondWith(fetch(event.request).catch(() => caches.match(event.request)).then((resp) => resp || caches.match('/offline/') || caches.match('/')));
    return;
  }}
  event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request).then((response) => {{
    const copy = response.clone();
    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
    return response;
  }}).catch(() => caches.match('{static('game/icons/icon-192.png')}'))));
}});
"""
    return HttpResponse(js, content_type='application/javascript')


@require_GET
def offline(request):
    return render(request, 'game/offline.html', _base_context(request))

def leaderboard(request):
    context = _base_context(request)
    context['players'] = Player.objects.order_by('-total_score', '-games_won', 'username')[:50]
    return render(request, 'game/leaderboard.html', context)


def history(request):
    context = _base_context(request)
    context['sessions'] = GameSession.objects.select_related('player')[:100]
    return render(request, 'game/history.html', context)
