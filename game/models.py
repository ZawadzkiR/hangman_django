from django.db import models

LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('pl', 'Polski'),
    ('sk', 'Slovenčina'),
    ('cs', 'Čeština'),
    ('de', 'Deutsch'),
    ('fr', 'Français'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('nl', 'Nederlands'),
    ('pt', 'Português'),
    ('sv', 'Svenska'),
]

RESULT_CHOICES = [
    ('won', 'Wygrana'),
    ('lost', 'Przegrana'),
]

ROOM_STATUS = [
    ('waiting', 'Waiting'),
    ('playing', 'Playing'),
    ('round_over', 'Round over'),
    ('finished', 'Finished'),
]

PLAYER_STATUS = [
    ('idle', 'Idle'),
    ('playing', 'Playing'),
    ('won', 'Won'),
    ('lost', 'Lost'),
    ('timeout', 'Timeout'),
]


class Player(models.Model):
    username = models.CharField(max_length=32, unique=True)
    total_score = models.IntegerField(default=0)
    games_played = models.PositiveIntegerField(default=0)
    games_won = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class Word(models.Model):
    text = models.CharField(max_length=64)
    normalized_text = models.CharField(max_length=64, db_index=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    category = models.CharField(max_length=64)
    hint = models.CharField(max_length=128, blank=True)
    difficulty = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    translation_key = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        unique_together = ('language', 'text')
        ordering = ['language', 'category', 'text']

    def __str__(self):
        return f'{self.text} ({self.language})'


class GameSession(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='sessions')
    word = models.ForeignKey(Word, on_delete=models.SET_NULL, null=True, blank=True)
    word_text = models.CharField(max_length=64)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    guessed_letters = models.TextField(blank=True)
    mistakes = models.PositiveSmallIntegerField(default=0)
    max_mistakes = models.PositiveSmallIntegerField(default=11)
    score_delta = models.IntegerField(default=0)
    result = models.CharField(max_length=4, choices=RESULT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.player.username} - {self.word_text} - {self.result}'


class MultiplayerRoom(models.Model):
    code = models.CharField(max_length=8, unique=True)
    host_name = models.CharField(max_length=32)
    host_session = models.CharField(max_length=64, db_index=True)
    host_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    status = models.CharField(max_length=16, choices=ROOM_STATUS, default='waiting')
    turn_seconds = models.PositiveIntegerField(default=45)
    max_players = models.PositiveIntegerField(default=999999)
    mistake_mode = models.CharField(max_length=16, default='medium')
    difficulty_mode = models.CharField(max_length=16, default='random')
    category_mode = models.CharField(max_length=64, default='random')
    max_rounds = models.PositiveIntegerField(default=10)
    target_score = models.PositiveIntegerField(default=120)
    round_number = models.PositiveIntegerField(default=0)
    current_translation_key = models.CharField(max_length=64, blank=True)
    current_word_text = models.CharField(max_length=64, blank=True)
    current_word_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    current_category = models.CharField(max_length=64, blank=True)
    winner_name = models.CharField(max_length=32, blank=True)
    turn_started_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code


class MultiplayerParticipant(models.Model):
    room = models.ForeignKey(MultiplayerRoom, on_delete=models.CASCADE, related_name='participants')
    session_token = models.CharField(max_length=64, db_index=True)
    nickname = models.CharField(max_length=32)
    order_no = models.PositiveIntegerField(default=1)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    score = models.IntegerField(default=0)
    is_ready = models.BooleanField(default=False)
    guessed_letters = models.TextField(blank=True)
    mistakes = models.PositiveSmallIntegerField(default=0)
    round_status = models.CharField(max_length=16, choices=PLAYER_STATUS, default='idle')
    current_word_text = models.CharField(max_length=64, blank=True)
    current_category = models.CharField(max_length=64, blank=True)
    current_hint = models.CharField(max_length=128, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('room', 'session_token')
        ordering = ['order_no', 'joined_at']

    def __str__(self):
        return f'{self.room.code}:{self.nickname}'
