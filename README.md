# XSave · simple X video downloader for Android

Paste a public X/Twitter post, choose an available quality, download, and save to Android Downloads. React/TypeScript mobile UI packaged with Capacitor; FastAPI and yt-dlp do the extraction on a separate server. Light/dark themes, real SSE progress, cancellation, private expiring file links. Also runs as a responsive website.

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

For Android install Android Studio with SDK 35 and JDK 21, then follow [deployment instructions](docs/DEPLOYMENT.md). For Docker on Windows use Docker Desktop with Linux containers.

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

Only progressive public MP4 videos with embedded audio are currently supported. The app shows actual source resolutions; it never upscales or fabricates qualities. Live X access and phone verification must be checked separately from fixture tests. See validation evidence for the precise checks performed in this workspace.
