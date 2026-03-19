import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.example.hangmanpwa',
  appName: 'Wisielec',
  webDir: 'web',
  bundledWebRuntime: false,
  server: {
    url: 'https://YOUR-APP.pythonanywhere.com',
    cleartext: false,
  },
};

export default config;
