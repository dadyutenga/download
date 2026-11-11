# XSave · simple X video downloader for Android

Paste a public X/Twitter post, choose an available MP4 quality, and save directly to Android Downloads. The Android app extracts public video options on the device through X’s public syndication service and downloads through Android DownloadManager. **No XSave backend, server address, or account is required on Android.**

The React/TypeScript interface is packaged with Capacitor. The responsive website retains the separate FastAPI/yt-dlp backend workflow below.

## Android direct downloads

Install the test APK from [downloads](downloads/README.md) on Android 10+. Paste an HTTPS post link, tap **Find my video**, choose quality, and tap **Download to Android**. Watch progress in the app or Android’s download notification. Files go straight to Downloads; there is no second server-to-phone transfer. Downloads continue if the app closes, but in-app progress is not restored after restarting the app; use Android Downloads to check completion.

Only public posts exposed through X’s public embed/syndication service and progressive MP4 variants are supported. The first embedded video is shown. Private/restricted posts, live streams, HLS, and separate audio/video streams are not supported. X can deny or change its public service. No cookies, login bypass, or third-party extraction server is used. Only save content you own or have permission to download.

To build: install Node 22+, JDK 21 and Android SDK platform 35/build-tools 34.0.0; then run `cd frontend && npm ci && npm test && npm run android:sync`, followed by `cd android && ./gradlew testDebugUnitTest assembleDebug`. APK: `frontend/android/app/build/outputs/apk/debug/app-debug.apk`.

## Linux development

Python 3.12+, Node 22+, FFmpeg on PATH:

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
cd backend
../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

In a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

Vite proxies `/api` to port 8000. Only one backend process is supported. No credentials are needed for public content; X can still deny requests from a server IP. Do not add account cookies to bypass restrictions.

## Windows development

Install Python 3.12+, Node 22+, and FFmpeg, then open PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\pip install -r backend/requirements-dev.txt
cd backend
..\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
# New terminal, from repository root:
cd frontend
npm ci
npm run dev
```

For Android install Android Studio with SDK 35 and JDK 21, then follow the direct-download build instructions above. For Docker on Windows use Docker Desktop with Linux containers.

## Tests and builds

```sh
.venv/bin/pytest -q -c backend/pytest.ini backend/tests
cd frontend
npm test
npm run build
npm run android:sync
cd android
./gradlew assembleDebug
# Windows: gradlew.bat assembleDebug
```

[API reference](docs/API.md) · [Deployment, Android signing, and limitations](docs/DEPLOYMENT.md) · [Validation evidence](docs/VALIDATION.md)

Configuration variables are documented in `.env.example`. For local backend development export variables in your shell; `.env` is loaded by Docker Compose, not automatically by Uvicorn. DATA_DIR defaults to the OS temporary directory `/tmp/x-video-downloader` on Linux; set DATA_DIR to a writable directory on Windows. VITE_API_URL is an optional build-time default, overridden by the app's Settings. API secrets remain in memory and are not persisted to local storage. Only the selected server origin and theme are stored.

The website backend supports progressive public MP4 videos with embedded audio. The app shows actual source resolutions; it never upscales or fabricates qualities. Live X access and phone verification must be checked separately from fixture tests. See validation evidence for the precise checks performed in this workspace.
