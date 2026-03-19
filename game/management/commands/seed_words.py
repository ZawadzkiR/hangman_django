from pathlib import Path
import json

from django.core.management.base import BaseCommand
from game.models import Word
from game.services import normalize_word


class Command(BaseCommand):
    help = 'Rebuilds the multilingual hangman word database from the bundled JSON seed file.'

    def handle(self, *args, **options):
        seed_file = Path(__file__).resolve().parents[2] / 'data' / 'words_seed.json'
        with seed_file.open('r', encoding='utf-8') as f:
            payload = json.load(f)

        Word.objects.all().delete()

        created = 0
        for item in payload:
            Word.objects.create(
                text=item['text'],
                normalized_text=normalize_word(item['text']),
                language=item['language'],
                category=item['category'],
                hint=item.get('hint', ''),
                difficulty=item.get('difficulty', 2),
                is_active=item.get('is_active', True),
                translation_key=item.get('translation_key', ''),
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {created} words from {seed_file.name}.'))
