from django.contrib import admin
from .models import Player, Word, GameSession


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('username', 'total_score', 'games_played', 'games_won', 'created_at')
    search_fields = ('username',)


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('text', 'language', 'category', 'difficulty', 'is_active')
    list_filter = ('language', 'category', 'difficulty', 'is_active')
    search_fields = ('text', 'hint', 'category')


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('player', 'language', 'result', 'score_delta', 'mistakes', 'created_at')
    list_filter = ('language', 'result')
    search_fields = ('player__username', 'word_text')
