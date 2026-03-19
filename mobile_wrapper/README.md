# Mobile wrapper (Capacitor)

1. Publish the Django app first, preferably on PythonAnywhere with HTTPS enabled.
2. Edit `capacitor.config.ts` and replace `https://YOUR-APP.pythonanywhere.com` with your real URL.
3. Then run:

```bash
npm install
npx cap add android
npx cap sync android
npx cap open android
```

This wrapper points to the hosted PWA. It is the fastest path to Android packaging.
For true offline solo gameplay inside the APK, the next step is moving the solo round logic fully client-side.
