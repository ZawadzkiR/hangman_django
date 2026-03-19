# Django Hangman Mobile + VS

Projekt zawiera:
- tryb solo bez reloadu strony
- automatyczne przełączanie interfejsu oraz wymuszenie języka po wyborze języka gry
- popupy wygranej i przegranej
- zapis wyniku dopiero po przegranej
- tryb multiplayer VS z kodem pokoju
- host/join, licznik czasu, polling AJAX co 1 sekundę
- to samo słowo w różnych językach dzięki `translation_key`
- GUI pod telefon i tablet

## Uruchomienie

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_words
python manage.py runserver
```

## Multiplayer

- Host tworzy pokój i ustawia czas na słowo
- Gracze dołączają kodem pokoju
- Host uruchamia rundę
- Każdy widzi to samo hasło w swoim języku
- Punkty sumują się po kolejnych rundach
- Host może uruchamiać kolejne rundy

## Uwaga

To multiplayer oparty na prostym pollingu HTTP, więc działa bez WebSocketów i dodatkowych bibliotek.


Production-style multiplayer additions:
- room cap: 10 players
- ready check before host can start
- host config: seconds per word, max rounds, target score
- auto-finish match at round limit or score target
- reconnect by session token in browser session
- final standings modal

Note: this package still uses AJAX polling every second, not WebSockets.


## PWA and PythonAnywhere

This project now includes:
- `/manifest.webmanifest`
- `/sw.js`
- PWA icons in `game/static/game/icons/`
- offline fallback page at `/offline/`
- `mobile_wrapper/` with a Capacitor shell for Android

### PythonAnywhere quick steps

1. Upload the project and create a Django web app.
2. Set `STATIC_ROOT` and run:
   `python manage.py collectstatic`
3. Map `/static/` to the `staticfiles` directory in the Web tab.
4. Enable HTTPS.
5. After deploy, visit the site once, then install it as a PWA from the browser.

### Czech language

Czech UI is included. Czech gameplay is enabled with keyboard support and a fallback chain to Slovak/English when a Czech word pair is still missing. You can extend Czech words later in `game/data/words_seed.json`.
