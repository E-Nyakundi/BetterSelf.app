# LifeApp — Capacitor mobile shell

This wraps the existing Django site in a thin native app shell so it can be
installed from the Play Store / App Store, with real native plugins for
things the browser can't do well (camera, status bar, etc).

It does **not** rebuild the UI. The native app just opens a WebView pointed
at your live Django site — same templates, same CSS, same JS you already
have. You keep developing the Django app exactly as before; this folder is
only the packaging layer.

## 0. Prerequisites

- Node.js LTS (18+) and npm
- Android: Android Studio (includes the SDK)
- iOS: a Mac with Xcode (Apple doesn't allow building iOS apps elsewhere)
- Your Django site reachable over the network — for real testing it needs
  to be on **HTTPS** eventually (Play Store/App Store both expect it), but
  for local development you can point at your machine's LAN IP over plain
  HTTP (see step 2).

## 1. Install dependencies

```
cd mobile
npm install
```

## 2. Point the app at your Django server

Open `capacitor.config.json` and set `server.url` to wherever Django is
actually reachable:

- **Local dev, testing on a physical phone on the same Wi-Fi:**
  run `python manage.py runserver 0.0.0.0:8000` on your PC, find your PC's
  LAN IP (`ipconfig` on Windows), and set:
  ```json
  "server": {
    "url": "http://192.168.1.50:8000",
    "androidScheme": "http",
    "cleartext": true
  }
  ```
  Also add that IP to Django's `ALLOWED_HOSTS` in `settings.py`.

- **Local dev, using an Android emulator only:** the emulator can reach your
  host machine at `http://10.0.2.2:8000` instead of your LAN IP.

- **Production:** once you deploy Django somewhere with a real domain and
  HTTPS, switch back to:
  ```json
  "server": {
    "url": "https://yourdomain.com",
    "androidScheme": "https",
    "cleartext": false,
    "allowNavigation": ["yourdomain.com"]
  }
  ```
  Also add `yourdomain.com` to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
  in Django's settings.

Login sessions and CSRF work exactly like they do in a mobile browser tab —
the WebView just stores cookies the normal way, nothing special to wire up.

## 3. Add the native platforms

```
npx cap add android
npx cap add ios     # Mac only
npx cap sync
```

This generates `android/` and `ios/` folders (gitignored — they're
regenerated from this config, not hand-edited).

## 4. Camera & microphone permissions

`@capacitor/camera` is already in `package.json`. After `npx cap sync`,
Android's permissions are added automatically. For iOS you must add two
strings manually (Capacitor can't do this part for you):

Open `ios/App/App/Info.plist` and add:

```xml
<key>NSCameraUsageDescription</key>
<string>LifeApp uses the camera to attach photos to journal entries and inventory items.</string>
<key>NSMicrophoneUsageDescription</key>
<string>LifeApp uses the microphone to record audio journal entries.</string>
```

## 5. Run it

```
npx cap open android   # opens Android Studio — press Run
npx cap open ios       # opens Xcode — press Run (Mac only)
```

Whenever you change `capacitor.config.json` or add/remove a native plugin,
re-run `npx cap sync` before building again. Plain Django/template/CSS/JS
changes need nothing here at all — just refresh, since the app is loading
your live site.

## What changed on the Django side for this

- `static/media-capture.js`: photo capture now checks for the Capacitor
  runtime (`window.Capacitor.isNativePlatform()`). Inside the wrapped app,
  it calls the native Camera plugin directly — full resolution, normal
  orientation, the phone's actual camera UI. In a regular mobile/desktop
  browser (no Capacitor), it falls back to the in-page live camera preview
  as before, now requesting a higher resolution and without the incorrect
  mirroring that made the back camera preview feel backwards.
- `static/design-system.css`: the top bar now pads itself for the status
  bar / notch (`env(safe-area-inset-top)`), a no-op on regular browsers.

## Known limitation

Video and audio recording still use the in-browser widget (getUserMedia /
MediaRecorder) even inside the wrapped app — there's no official Capacitor
plugin for those yet. This works fine since both Android's and iOS's
WebViews support those APIs natively, but it doesn't get the same
"native camera app" treatment that photos now do. A community plugin like
`capacitor-voice-recorder` could close that gap later if it becomes
worth the extra dependency.

## Icons & splash screen (not done yet)

Once you have a final logo, generate all the platform-specific icon and
splash sizes with:

```
npm install @capacitor/assets --save-dev
npx capacitor-assets generate
```

pointing it at a single source image (1024×1024 icon, 2732×2732 splash).
