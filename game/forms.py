from django import forms
from .models import LANGUAGE_CHOICES

DIFFICULTY_CHOICES = [
    ('random', 'Random'),
    ('easy', 'Easy'),
    ('medium', 'Medium'),
    ('hard', 'Hard'),
]

MISTAKE_MODE_CHOICES = [
    ('easy', 'Easy'),
    ('medium', 'Medium'),
    ('hard', 'Hard'),
]

ROOM_MODE_CHOICES = [
    ('vs', 'VS'),
    ('coop', 'Co-op'),
]


class StartGameForm(forms.Form):
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES, label='Game language')
    difficulty = forms.ChoiceField(choices=DIFFICULTY_CHOICES, initial='random')
    category = forms.ChoiceField(choices=[('random', 'Random')], initial='random')
    mistake_mode = forms.ChoiceField(choices=MISTAKE_MODE_CHOICES, initial='medium')


class SaveScoreForm(forms.Form):
    username = forms.CharField(max_length=32, required=False, label='Username')

    def clean_username(self):
        value = self.cleaned_data['username'].strip()
        if value and len(value) < 2:
            raise forms.ValidationError('Username must have at least 2 characters.')
        return value


class CreateRoomForm(forms.Form):
    nickname = forms.CharField(max_length=32, required=False)
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES)
    difficulty = forms.ChoiceField(choices=DIFFICULTY_CHOICES, initial='random')
    category = forms.ChoiceField(choices=[('random', 'Random')], initial='random')
    turn_seconds = forms.IntegerField(min_value=15, max_value=180, initial=45)
    max_rounds = forms.IntegerField(min_value=3, max_value=30, initial=10)
    target_score = forms.IntegerField(min_value=20, max_value=500, initial=120)
    mistake_mode = forms.ChoiceField(choices=MISTAKE_MODE_CHOICES, initial='medium')
    mode = forms.ChoiceField(choices=ROOM_MODE_CHOICES, initial='vs')


class JoinRoomForm(forms.Form):
    room_code = forms.CharField(max_length=8)
    nickname = forms.CharField(max_length=32, required=False)
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES)
