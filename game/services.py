import random
import re
import string
import unicodedata
from typing import Dict, Optional, Set

from django.utils import timezone

from .models import MultiplayerRoom, Word, LANGUAGE_CHOICES

MISTAKE_LIMITS = {'easy': 11, 'medium': 6, 'hard': 4}
DEFAULT_MISTAKE_MODE = 'medium'

LETTER_GROUPS = {
    'en': {},
    'pl': {'a': {'a', 'ą'}, 'c': {'c', 'ć'}, 'e': {'e', 'ę'}, 'l': {'l', 'ł'}, 'n': {'n', 'ń'}, 'o': {'o', 'ó'}, 's': {'s', 'ś'}, 'z': {'z', 'ź', 'ż'}},
    'sk': {'a': {'a', 'á', 'ä'}, 'c': {'c', 'č'}, 'd': {'d', 'ď'}, 'e': {'e', 'é'}, 'i': {'i', 'í'}, 'l': {'l', 'ĺ', 'ľ'}, 'n': {'n', 'ň'}, 'o': {'o', 'ó', 'ô'}, 'r': {'r', 'ŕ'}, 's': {'s', 'š'}, 't': {'t', 'ť'}, 'u': {'u', 'ú'}, 'y': {'y', 'ý'}, 'z': {'z', 'ž'}},
    'cs': {'a': {'a', 'á'}, 'c': {'c', 'č'}, 'd': {'d', 'ď'}, 'e': {'e', 'é', 'ě'}, 'i': {'i', 'í'}, 'n': {'n', 'ň'}, 'o': {'o', 'ó'}, 'r': {'r', 'ř'}, 's': {'s', 'š'}, 't': {'t', 'ť'}, 'u': {'u', 'ú', 'ů'}, 'y': {'y', 'ý'}, 'z': {'z', 'ž'}},
    'de': {'a': {'a', 'ä'}, 'o': {'o', 'ö'}, 'u': {'u', 'ü'}, 's': {'s', 'ß'}},
    'fr': {'a': {'a', 'à', 'â', 'æ'}, 'c': {'c', 'ç'}, 'e': {'e', 'é', 'è', 'ê', 'ë'}, 'i': {'i', 'î', 'ï'}, 'o': {'o', 'ô', 'œ'}, 'u': {'u', 'ù', 'û', 'ü'}, 'y': {'y', 'ÿ'}},
    'es': {'a': {'a', 'á'}, 'e': {'e', 'é'}, 'i': {'i', 'í'}, 'n': {'n', 'ñ'}, 'o': {'o', 'ó'}, 'u': {'u', 'ú', 'ü'}},
    'it': {'a': {'a', 'à'}, 'e': {'e', 'è', 'é'}, 'i': {'i', 'ì'}, 'o': {'o', 'ò'}, 'u': {'u', 'ù'}},
    'nl': {'a': {'a', 'ä'}, 'e': {'e', 'é', 'è', 'ë'}, 'i': {'i', 'ï'}, 'o': {'o', 'ö'}, 'u': {'u', 'ü'}},
    'pt': {'a': {'a', 'á', 'à', 'â', 'ã'}, 'c': {'c', 'ç'}, 'e': {'e', 'é', 'ê'}, 'i': {'i', 'í'}, 'o': {'o', 'ó', 'ô', 'õ'}, 'u': {'u', 'ú'}},
    'sv': {'a': {'a', 'å', 'ä'}, 'o': {'o', 'ö'}},
}

KEYBOARDS = {
    'en': list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    'pl': list('AĄBCĆDEĘFGHIJKLŁMNŃOÓPRSŚTUWYZŹŻ'),
    'sk': list('AÁÄBCČDĎEÉFGHIÍJKLĹĽMNŇOÓÔPRSŠTŤUÚVWXYÝZŽ'),
    'cs': list('AÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ'),
    'de': list('AÄBCDEFGHIJKLMNOÖPQRSßTUÜVWXYZ'),
    'fr': list('ABCDEFGHIJKLMNOPQRSTUVWXYZÇ'),
    'es': list('ABCDEFGHIJKLMNÑOPQRSTUVWXYZ'),
    'it': list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    'nl': list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    'pt': list('ABCDEFGHIJKLMNOPQRSTUVWXYZÇ'),
    'sv': list('AÅÄBCDEFGHIJKLMNOÖPQRSTUVWXYZ'),
}

DIFFICULTY_MAP = {'easy': 1, 'medium': 2, 'hard': 3}

UI_LANGUAGE_CHOICES = list(LANGUAGE_CHOICES)
LANGUAGE_FALLBACKS = {'cs': ['sk', 'en']}

TRANSLATIONS = {
    'pl': {
        'app_title': 'Wisielec', 'tagline': 'Gra na telefon, tablet i komputer', 'new_game': 'Nowa gra', 'leaderboard': 'Ranking', 'history': 'Historia',
        'start_title': 'Wybierz tryb gry', 'start_desc': 'Solo zapisuje serię zwycięstw do momentu przegranej. VS pozwala grać z innymi na kod pokoju.', 'game_language': 'Język gry',
        'start_button': 'Graj', 'player': 'Gracz', 'category': 'Kategoria', 'hint': 'Podpowiedź', 'used_letters': 'Użyte', 'mistakes': 'Pudła', 'remaining': 'Pozostało',
        'score': 'Wynik', 'streak': 'Seria', 'none': 'brak', 'save_optional': 'Login wpisujesz dopiero po przegranej. Możesz też pominąć zapis.', 'save_score': 'Zapisz wynik',
        'skip_save': 'Pomiń', 'continue_game': 'Dalej', 'play_again': 'Nowa seria', 'username_placeholder': 'Twój login', 'won_title': 'Brawo!', 'lost_title': 'Koniec gry',
        'won_text': 'Odgadłeś słowo.', 'lost_text': 'Tym razem się nie udało.', 'next_word': 'Losuję kolejne słowo...', 'final_word': 'Szukane słowo', 'saved_ok': 'Wynik zapisany.',
        'saved_skip': 'Wynik pominięty.', 'already_used': 'Ta litera już była', 'hit_msg': 'Dobrze', 'miss_msg': 'Pudło', 'table_player': 'Gracz', 'table_score': 'Wynik',
        'table_games': 'Gry', 'table_wins': 'Wygrane', 'table_result': 'Rezultat', 'table_word': 'Słowo', 'table_date': 'Data', 'history_empty': 'Brak zapisanych gier.',
        'country_note': 'Na górze strony możesz zmieniać język interfejsu niezależnie od języka gry.', 'login_optional': 'Login opcjonalny', 'solo_mode': 'Solo', 'vs_mode': 'Multiplayer VS',
        'create_room': 'Stwórz pokój', 'join_room': 'Dołącz do pokoju', 'room_code': 'Kod pokoju', 'nickname': 'Nick', 'nickname_placeholder': 'np. Gracz', 'turn_seconds': 'Sekundy na słowo',
        'waiting_room': 'Poczekalnia', 'room_players': 'Gracze', 'start_match': 'Start rundy', 'next_round_host': 'Następna runda', 'leave_room': 'Wyjdź', 'copy_code': 'Udostępnij kod',
        'timer': 'Czas', 'round': 'Runda', 'status_waiting': 'Czekamy na start hosta', 'status_playing': 'Runda trwa', 'status_round_over': 'Runda zakończona', 'host': 'Host',
        'you': 'Ty', 'room_hint': 'Każdy widzi to samo hasło w wybranym przez siebie języku.', 'ready_up': 'Gotowy', 'not_ready': 'Niegotowy', 'match_finished': 'Mecz zakończony', 'match_winner': 'Zwycięzca', 'final_table': 'Tabela końcowa', 'max_rounds': 'Maks. rund', 'target_score': 'Cel punktowy', 'players_ready': 'Gotowi gracze', 'need_players': 'Potrzeba co najmniej 2 graczy.', 'need_ready': 'Wszyscy gracze muszą być gotowi.',
        'your_status': 'Twój status', 'status_won': 'Odgadnięte', 'status_lost': 'Brak prób', 'status_timeout': 'Koniec czasu', 'status_idle': 'Gotowy', 'mobile_ready': 'Wygodne sterowanie na telefonie i tablecie.',
        'share_label': 'Kod do znajomych', 'host_controls': 'Sterowanie hosta', 'player_list': 'Lista graczy', 'how_vs_works': 'Host zakłada pokój, ustawia czas i filtry słów, a gracze dołączają kodem.',
        'ui_language': 'Język interfejsu', 'difficulty': 'Poziom', 'difficulty_random': 'Losowy', 'difficulty_easy': 'Łatwy', 'difficulty_medium': 'Średni', 'difficulty_hard': 'Trudny',
        'mistake_mode': 'Tryb błędów', 'mistake_easy': 'Łatwy (11)', 'mistake_medium': 'Średni (6)', 'mistake_hard': 'Trudny (4)',
        'category_random': 'Losowa kategoria', 'word_filters': 'Filtry słów', 'save_filters': 'Te ustawienia dotyczą całej serii.', 'room_unlimited': 'Bez limitu graczy',
    },
    'sk': {
        'app_title': 'Obesenec', 'tagline': 'Hra pre telefón, tablet a počítač', 'new_game': 'Nová hra', 'leaderboard': 'Rebríček', 'history': 'História',
        'start_title': 'Vyber režim hry', 'start_desc': 'Solo ukladá sériu výhier až do prehry. VS umožní hrať s ostatnými cez kód miestnosti.', 'game_language': 'Jazyk hry',
        'start_button': 'Hrať', 'player': 'Hráč', 'category': 'Kategória', 'hint': 'Pomôcka', 'used_letters': 'Použité', 'mistakes': 'Chyby', 'remaining': 'Zostáva', 'score': 'Skóre',
        'streak': 'Séria', 'none': 'nič', 'save_optional': 'Meno zadáš až po prehre. Uloženie môžeš preskočiť.', 'save_score': 'Uložiť skóre', 'skip_save': 'Preskočiť',
        'continue_game': 'Ďalej', 'play_again': 'Nová séria', 'username_placeholder': 'Tvoje meno', 'won_title': 'Výborne!', 'lost_title': 'Koniec hry', 'won_text': 'Slovo je uhádnuté.',
        'lost_text': 'Tentoraz to nevyšlo.', 'next_word': 'Losujem ďalšie slovo...', 'final_word': 'Hľadané slovo', 'saved_ok': 'Skóre uložené.', 'saved_skip': 'Skóre nebolo uložené.',
        'already_used': 'Toto písmeno už bolo použité', 'hit_msg': 'Správne', 'miss_msg': 'Chyba', 'table_player': 'Hráč', 'table_score': 'Skóre', 'table_games': 'Hry', 'table_wins': 'Výhry',
        'table_result': 'Výsledok', 'table_word': 'Slovo', 'table_date': 'Dátum', 'history_empty': 'Žiadne uložené hry.', 'country_note': 'Hore na stránke môžeš meniť jazyk rozhrania nezávisle od jazyka hry.',
        'login_optional': 'Meno je voliteľné', 'solo_mode': 'Solo', 'vs_mode': 'Multiplayer VS', 'create_room': 'Vytvoriť miestnosť', 'join_room': 'Pripojiť sa', 'room_code': 'Kód miestnosti',
        'nickname': 'Prezývka', 'nickname_placeholder': 'napr. Hráč', 'turn_seconds': 'Sekúnd na slovo', 'waiting_room': 'Čakáreň', 'room_players': 'Hráči', 'start_match': 'Spustiť kolo',
        'next_round_host': 'Ďalšie kolo', 'leave_room': 'Odísť', 'copy_code': 'Zdieľať kód', 'timer': 'Čas', 'round': 'Kolo', 'status_waiting': 'Čaká sa na hostiteľa', 'status_playing': 'Kolo prebieha',
        'status_round_over': 'Kolo skončilo', 'host': 'Hostiteľ', 'you': 'Ty', 'room_hint': 'Každý vidí rovnaké slovo vo svojom jazyku.', 'ready_up': 'Pripravený', 'not_ready': 'Nepripravený', 'match_finished': 'Zápas skončil', 'match_winner': 'Víťaz', 'final_table': 'Konečné poradie', 'max_rounds': 'Max. kolá', 'target_score': 'Cieľové skóre', 'players_ready': 'Pripravení hráči', 'need_players': 'Treba aspoň 2 hráčov.', 'need_ready': 'Všetci hráči musia byť pripravení.',
        'your_status': 'Tvoj stav', 'status_won': 'Uhádnuté', 'status_lost': 'Bez pokusov', 'status_timeout': 'Vypršal čas', 'status_idle': 'Pripravený', 'mobile_ready': 'Pohodlné ovládanie na mobile aj tablete.',
        'share_label': 'Kód pre známych', 'host_controls': 'Ovládanie hostiteľa', 'player_list': 'Zoznam hráčov', 'how_vs_works': 'Hostiteľ vytvorí miestnosť, nastaví čas a filtre slov, ostatní sa pripoja kódom.',
        'ui_language': 'Jazyk rozhrania', 'difficulty': 'Obtiažnosť', 'difficulty_random': 'Náhodná', 'difficulty_easy': 'Ľahká', 'difficulty_medium': 'Stredná', 'difficulty_hard': 'Ťažká',
        'mistake_mode': 'Režim chýb', 'mistake_easy': 'Ľahký (11)', 'mistake_medium': 'Stredný (6)', 'mistake_hard': 'Ťažký (4)',
        'category_random': 'Náhodná kategória', 'word_filters': 'Filtre slov', 'save_filters': 'Tieto nastavenia platia pre celú sériu.', 'room_unlimited': 'Bez limitu hráčov',
    },
    'en': {
        'app_title': 'Hangman', 'tagline': 'Built for phone, tablet, and desktop', 'new_game': 'New game', 'leaderboard': 'Leaderboard', 'history': 'History',
        'start_title': 'Choose a game mode', 'start_desc': 'Solo stores your streak until you lose. VS lets players join with a room code.', 'game_language': 'Game language', 'start_button': 'Play',
        'player': 'Player', 'category': 'Category', 'hint': 'Hint', 'used_letters': 'Used', 'mistakes': 'Misses', 'remaining': 'Left', 'score': 'Score', 'streak': 'Streak', 'none': 'none',
        'save_optional': 'Enter a login only after you lose, or skip saving.', 'save_score': 'Save score', 'skip_save': 'Skip', 'continue_game': 'Continue', 'play_again': 'New run', 'username_placeholder': 'Your login', 'won_title': 'Nice!', 'lost_title': 'Game over',
        'won_text': 'You solved the word.', 'lost_text': 'Not this time.', 'next_word': 'Rolling the next word...', 'final_word': 'Target word', 'saved_ok': 'Score saved.', 'saved_skip': 'Score skipped.',
        'already_used': 'That letter was already used', 'hit_msg': 'Hit', 'miss_msg': 'Miss', 'table_player': 'Player', 'table_score': 'Score', 'table_games': 'Games', 'table_wins': 'Wins', 'table_result': 'Result', 'table_word': 'Word', 'table_date': 'Date', 'history_empty': 'No saved games yet.',
        'country_note': 'You can switch the interface language at the top independently from the game language.', 'login_optional': 'Login optional', 'solo_mode': 'Solo', 'vs_mode': 'Multiplayer VS',
        'create_room': 'Create room', 'join_room': 'Join room', 'room_code': 'Room code', 'nickname': 'Nickname', 'nickname_placeholder': 'e.g. Player', 'turn_seconds': 'Seconds per word',
        'waiting_room': 'Lobby', 'room_players': 'Players', 'start_match': 'Start round', 'next_round_host': 'Next round', 'leave_room': 'Leave', 'copy_code': 'Share code', 'timer': 'Timer', 'round': 'Round', 'status_waiting': 'Waiting for host', 'status_playing': 'Round in progress', 'status_round_over': 'Round over', 'host': 'Host', 'you': 'You',
        'room_hint': 'Everyone gets the same word translated into their chosen language.', 'ready_up': 'Ready', 'not_ready': 'Not ready', 'match_finished': 'Match finished', 'match_winner': 'Winner', 'final_table': 'Final table', 'max_rounds': 'Max rounds', 'target_score': 'Target score', 'players_ready': 'Ready players', 'need_players': 'At least 2 players are required.', 'need_ready': 'All players must be ready.',
        'your_status': 'Your status', 'status_won': 'Solved', 'status_lost': 'Out of tries', 'status_timeout': 'Time over', 'status_idle': 'Ready', 'mobile_ready': 'Comfortable on phone and tablet.',
        'share_label': 'Code to share', 'host_controls': 'Host controls', 'player_list': 'Player list', 'how_vs_works': 'The host creates a room, sets time and word filters, and others join with the code.',
        'ui_language': 'Interface language', 'difficulty': 'Word difficulty', 'difficulty_random': 'Random', 'difficulty_easy': 'Easy', 'difficulty_medium': 'Medium', 'difficulty_hard': 'Hard',
        'mistake_mode': 'Mistake mode', 'mistake_easy': 'Easy (11)', 'mistake_medium': 'Medium (6)', 'mistake_hard': 'Hard (4)',
        'category_random': 'Random category', 'word_filters': 'Word filters', 'save_filters': 'These settings stay active for the whole run.', 'room_unlimited': 'Unlimited players',
    },
}



TRANSLATIONS['cs'] = {
    **TRANSLATIONS['sk'],
    'app_title': 'Oběšenec',
    'tagline': 'Hra pro telefon, tablet a počítač',
    'leaderboard': 'Žebříček',
    'history': 'Historie',
    'start_title': 'Vyber režim hry',
    'start_desc': 'Solo ukládá sérii výher až do prohry. VS umožní hrát s ostatními přes kód místnosti.',
    'game_language': 'Jazyk hry',
    'start_button': 'Hrát',
    'player': 'Hráč',
    'category': 'Kategorie',
    'hint': 'Nápověda',
    'used_letters': 'Použité',
    'mistakes': 'Chyby',
    'remaining': 'Zbývá',
    'score': 'Skóre',
    'save_optional': 'Jméno zadáš až po prohře. Uložení můžeš přeskočit.',
    'save_score': 'Uložit skóre',
    'skip_save': 'Přeskočit',
    'continue_game': 'Další',
    'play_again': 'Nová série',
    'username_placeholder': 'Tvé jméno',
    'won_title': 'Výborně!',
    'lost_title': 'Konec hry',
    'won_text': 'Slovo je uhádnuté.',
    'lost_text': 'Tentokrát to nevyšlo.',
    'final_word': 'Hledané slovo',
    'saved_ok': 'Skóre uloženo.',
    'saved_skip': 'Skóre nebylo uloženo.',
    'already_used': 'Toto písmeno už bylo použito',
    'hit_msg': 'Správně',
    'miss_msg': 'Chyba',
    'table_date': 'Datum',
    'country_note': 'Nahoře na stránce můžeš měnit jazyk rozhraní nezávisle na jazyku hry.',
    'login_optional': 'Jméno je volitelné',
    'create_room': 'Vytvořit místnost',
    'join_room': 'Připojit se',
    'room_code': 'Kód místnosti',
    'nickname': 'Přezdívka',
    'nickname_placeholder': 'např. Hráč',
    'turn_seconds': 'Sekund na slovo',
    'waiting_room': 'Čekárna',
    'room_players': 'Hráči',
    'start_match': 'Spustit kolo',
    'next_round_host': 'Další kolo',
    'leave_room': 'Odejít',
    'copy_code': 'Sdílet kód',
    'timer': 'Čas',
    'round': 'Kolo',
    'status_waiting': 'Čeká se na hostitele',
    'status_round_over': 'Kolo skončilo',
    'host': 'Hostitel',
    'room_hint': 'Každý vidí stejné slovo ve svém jazyce.',
    'ready_up': 'Připraven',
    'not_ready': 'Nepřipraven',
    'match_finished': 'Zápas skončil',
    'match_winner': 'Vítěz',
    'final_table': 'Konečné pořadí',
    'max_rounds': 'Max. kol',
    'target_score': 'Cílové skóre',
    'players_ready': 'Připravení hráči',
    'need_players': 'Je potřeba alespoň 2 hráčů.',
    'need_ready': 'Všichni hráči musí být připraveni.',
    'your_status': 'Tvůj stav',
    'status_won': 'Uhádnuto',
    'status_lost': 'Bez pokusů',
    'status_timeout': 'Vypršel čas',
    'status_idle': 'Připraven',
    'mobile_ready': 'Pohodlné ovládání na mobilu i tabletu.',
    'share_label': 'Kód pro přátele',
    'host_controls': 'Ovládání hostitele',
    'player_list': 'Seznam hráčů',
    'how_vs_works': 'Hostitel vytvoří místnost, nastaví čas a filtry slov, ostatní se připojí kódem.',
    'ui_language': 'Jazyk rozhraní',
    'difficulty': 'Obtížnost',
    'difficulty_random': 'Náhodná',
    'difficulty_easy': 'Lehká',
    'difficulty_medium': 'Střední',
    'difficulty_hard': 'Těžká',
    'mistake_mode': 'Režim chyb',
    'mistake_easy': 'Lehký (11)',
    'mistake_medium': 'Střední (6)',
    'mistake_hard': 'Těžký (4)',
    'category_random': 'Náhodná kategorie',
    'word_filters': 'Filtry slov',
    'save_filters': 'Tato nastavení platí pro celou sérii.',
    'room_unlimited': 'Bez limitu hráčů',
}

def get_max_mistakes(mode: str) -> int:
    return MISTAKE_LIMITS.get(mode or DEFAULT_MISTAKE_MODE, MISTAKE_LIMITS[DEFAULT_MISTAKE_MODE])


def t(language: str) -> Dict[str, str]:
    return TRANSLATIONS.get(language, TRANSLATIONS['en'])


def normalize_word(text: str) -> str:
    return (text or '').strip().lower()


def strip_accents_keep_base(text: str) -> str:
    return ''.join(ch for ch in unicodedata.normalize('NFKD', text) if not unicodedata.combining(ch))


def serialize_guessed(letters: Set[str]) -> str:
    return ''.join(sorted(letters))


def deserialize_guessed(value: str) -> Set[str]:
    return set(value or '')


def get_equivalent_letters(letter: str, language: str) -> Set[str]:
    letter = normalize_word(letter)[:1]
    mapping = LETTER_GROUPS.get(language, {})
    if letter in mapping:
        return set(mapping[letter])
    for base, group in mapping.items():
        if letter in group:
            return set(group)
    return {letter}


def mask_word(word: str, guessed_letters: Set[str], language: str) -> str:
    masked = []
    for char in word:
        normalized = normalize_word(char)
        if char.isalpha():
            equivalents = get_equivalent_letters(normalized, language)
            masked.append(char.upper() if guessed_letters & equivalents else '_')
        else:
            masked.append(char)
    return ' '.join(masked)


def apply_word_filters(queryset, difficulty='random', category='random'):
    if difficulty in DIFFICULTY_MAP:
        queryset = queryset.filter(difficulty=DIFFICULTY_MAP[difficulty])
    if category and category != 'random':
        queryset = queryset.filter(category=category)
    return queryset


def choose_word(language: str, difficulty='random', category='random', exclude_ids=None):
    exclude_ids = exclude_ids or []
    queryset = Word.objects.filter(language=language, is_active=True).exclude(id__in=exclude_ids)
    queryset = apply_word_filters(queryset, difficulty, category)
    word = queryset.order_by('?').first()
    if not word:
        queryset = Word.objects.filter(language=language, is_active=True)
        queryset = apply_word_filters(queryset, difficulty, category)
        word = queryset.order_by('?').first()
    if not word:
        word = Word.objects.filter(language=language, is_active=True).order_by('?').first()
    return word


def is_word_guessed(word: str, guessed_letters: Set[str], language: str) -> bool:
    for char in word:
        normalized = normalize_word(char)
        if normalized and char.isalpha():
            if not guessed_letters & get_equivalent_letters(normalized, language):
                return False
    return True


def word_unique_letters(word: str, language: str) -> Set[str]:
    letters: Set[str] = set()
    for char in normalize_word(word):
        if char.isalpha():
            eq = get_equivalent_letters(char, language)
            if eq:
                letters.add(sorted(eq)[0])
    return letters


def calculate_word_score(word: str, mistakes: int, won: bool, seconds_left: int = 0) -> int:
    if not won:
        return 0
    base = max(5, len(word_unique_letters(word, 'en')) * 2)
    bonus = max(0, (get_max_mistakes(DEFAULT_MISTAKE_MODE) - mistakes) * 3)
    time_bonus = max(0, min(seconds_left, 15))
    return base + bonus + time_bonus


def current_stats(game: Dict) -> Dict:
    guessed_letters = deserialize_guessed(game.get('guessed_letters', ''))
    language = game['language']
    word = game['word']
    return {
        'masked_word': mask_word(word, guessed_letters, language),
        'guessed_letters': sorted(guessed_letters),
        'won': is_word_guessed(word, guessed_letters, language),
        'lost': game['mistakes'] >= game['max_mistakes'],
        'remaining': max(game['max_mistakes'] - game['mistakes'], 0),
        'keyboard': KEYBOARDS.get(language, KEYBOARDS['en']),
    }


def resolve_ui_language(request) -> str:
    allowed = {code for code, _ in UI_LANGUAGE_CHOICES}
    preferred = request.session.get('ui_lang')
    return preferred if preferred in allowed else 'en'


def ensure_session_token(request) -> str:
    token = request.session.get('player_token')
    if not token:
        token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        request.session['player_token'] = token
    return token


def generate_room_code() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def get_translation_word(translation_key: str, language: str, fallback_language: str = 'en') -> Optional[Word]:
    candidates = [language] + LANGUAGE_FALLBACKS.get(language, []) + ([fallback_language] if fallback_language not in LANGUAGE_FALLBACKS.get(language, []) else [])
    for lang in candidates:
        word = Word.objects.filter(translation_key=translation_key, language=lang, is_active=True).first()
        if word:
            return word
    return None


def room_seconds_left(room: MultiplayerRoom) -> int:
    if not room.turn_started_at or room.status != 'playing':
        return room.turn_seconds
    elapsed = int((timezone.now() - room.turn_started_at).total_seconds())
    return max(room.turn_seconds - elapsed, 0)


def sync_participant_word(room: MultiplayerRoom, participant):
    word = get_translation_word(room.current_translation_key, participant.language, room.current_word_language)
    if not word:
        word = Word.objects.filter(language=room.current_word_language, translation_key=room.current_translation_key).first()
    if word:
        participant.current_word_text = word.text
        participant.current_category = word.category
        participant.current_hint = word.hint


def start_room_round(room: MultiplayerRoom):
    candidates = Word.objects.filter(language=room.host_language, is_active=True).exclude(translation_key='').exclude(translation_key__isnull=True)
    candidates = apply_word_filters(candidates, room.difficulty_mode, room.category_mode)
    selected = candidates.order_by('?').first()
    if not selected:
        selected = choose_word(room.host_language, room.difficulty_mode, room.category_mode)
    room.round_number += 1
    room.current_translation_key = selected.translation_key or f'{selected.language}:{selected.normalized_text}'
    room.current_word_text = selected.text
    room.current_word_language = selected.language
    room.current_category = selected.category
    room.turn_started_at = timezone.now()
    room.status = 'playing'
    room.save()

    for participant in room.participants.all():
        participant.guessed_letters = ''
        participant.mistakes = 0
        participant.round_status = 'playing'
        sync_participant_word(room, participant)
        participant.save()


def player_round_stats(participant) -> Dict:
    guessed = deserialize_guessed(participant.guessed_letters)
    return {
        'masked_word': mask_word(participant.current_word_text, guessed, participant.language),
        'guessed_letters': sorted(guessed),
        'won': is_word_guessed(participant.current_word_text, guessed, participant.language),
        'lost': participant.mistakes >= get_max_mistakes(getattr(participant.room, 'mistake_mode', DEFAULT_MISTAKE_MODE)),
        'remaining': max(get_max_mistakes(getattr(participant.room, 'mistake_mode', DEFAULT_MISTAKE_MODE)) - participant.mistakes, 0),
        'keyboard': KEYBOARDS.get(participant.language, KEYBOARDS['en']),
    }


def maybe_finish_match(room: MultiplayerRoom):
    participants = list(room.participants.all())
    if not participants:
        return
    leader = sorted(participants, key=lambda p: (-p.score, p.order_no))[0]
    if room.round_number >= room.max_rounds or leader.score >= room.target_score:
        room.status = 'finished'
        room.winner_name = leader.nickname
        room.save(update_fields=['status', 'winner_name'])


def finalize_room_if_needed(room: MultiplayerRoom):
    participants = list(room.participants.all())
    if room.status != 'playing' or not participants:
        return
    seconds_left = room_seconds_left(room)
    if seconds_left <= 0:
        for p in participants:
            if p.round_status == 'playing':
                p.round_status = 'timeout'
                p.save(update_fields=['round_status'])
        room.status = 'round_over'
        room.save(update_fields=['status'])
        maybe_finish_match(room)
        return
    if all(p.round_status in {'won', 'lost', 'timeout'} for p in participants):
        room.status = 'round_over'
        room.save(update_fields=['status'])
        maybe_finish_match(room)


def all_ready(room: MultiplayerRoom) -> bool:
    participants = list(room.participants.all())
    return bool(participants) and all(p.is_ready for p in participants)


def waiting_summary(room: MultiplayerRoom):
    participants = list(room.participants.all())
    return {
        'player_count': len(participants),
        'ready_count': sum(1 for p in participants if p.is_ready),
        'all_ready': all_ready(room),
        'max_players': None,
    }


def room_state(room: MultiplayerRoom, participant, ui_lang: str) -> Dict:
    finalize_room_if_needed(room)
    participant.refresh_from_db()
    room.refresh_from_db()
    stats = player_round_stats(participant)
    waiting = waiting_summary(room)
    ranking = sorted(room.participants.all(), key=lambda p: (-p.score, p.order_no))
    return {
        'room': {
            'code': room.code, 'status': room.status, 'round_number': room.round_number, 'turn_seconds': room.turn_seconds, 'seconds_left': room_seconds_left(room),
            'host_name': room.host_name, 'current_category': participant.current_category or room.current_category, 'max_rounds': room.max_rounds, 'target_score': room.target_score,
            'winner_name': room.winner_name, 'difficulty_mode': room.difficulty_mode, 'category_mode': room.category_mode, 'mistake_mode': room.mistake_mode, 'max_mistakes': get_max_mistakes(room.mistake_mode), **waiting,
        },
        'you': {
            'nickname': participant.nickname, 'language': participant.language, 'score': participant.score, 'mistakes': participant.mistakes, 'status': participant.round_status,
            'is_ready': participant.is_ready, 'stats': stats, 'current_hint': participant.current_hint,
        },
        'players': [
            {'nickname': p.nickname, 'score': p.score, 'status': p.round_status, 'is_host': p.session_token == room.host_session, 'is_you': p.id == participant.id, 'is_ready': p.is_ready}
            for p in ranking
        ],
        'final_ranking': [{'nickname': p.nickname, 'score': p.score, 'status': p.round_status} for p in ranking],
        'labels': {
            'won': t(ui_lang)['status_won'], 'lost': t(ui_lang)['status_lost'], 'timeout': t(ui_lang)['status_timeout'], 'idle': t(ui_lang)['status_idle'], 'playing': t(ui_lang)['status_playing'],
        }
    }
