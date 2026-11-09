# Validation in this workspace

Performed on 2026-11-09.

## Passed

* Backend: **37 tests passed**, including strict post URL normalization, domain restrictions, private DNS answers, redirect guard rejection, direct connection rebinding rejection, mocked extraction, real yt-dlp download/progress handling through a controlled in-memory HTTP transport, ownership checks, file delivery, cancellation, failure states, process timeout/reaping, path escape rejection, expiry cleanup, request size and rate limits. The controlled transport uses fixture bytes, not a playable live X video.
* Frontend: **6 tests passed** for the mobile input, actual returned quality options, API error recovery, SSE-driven completion/save availability, server URL restrictions, and theme switching.
* TypeScript and production Vite build passed.
* Chromium: phone viewport 390×844 and desktop viewport 1440×1000, no horizontal overflow. Phone startup and the deployed API-error flow had no JavaScript runtime errors. Screenshots: `mobile-screen.png`, `mobile-dark.png`, `desktop-screen.png`.
* Docker: frontend/backend images built with TLS verification and session CA trust supplied through temporary BuildKit secrets. Both services started and became healthy. Nginx returned HTTP 200 for the app, health returned `{"status":"ok","ffmpeg":true}`, and an internal-address input returned HTTP 422.
* Android: Gradle `assembleDebug` passed (115 tasks executed). APK signature verified with apksigner (v2 signature). Manifest checked with aapt: app ID `com.xsave.downloader`, minimum SDK 29 (Android 10), target SDK 35. Debug APK copied to `/workspace/artifacts/XSave-debug.apk` (about 9.2 MB).

APK SHA-256: `b958e27028bfe86729306aabb561d5ddcc9264dc21fb59b43e487800371e631f`.

## Not verified / external prerequisites

* **Live X extraction and video download:** attempted using a public NASA post from yt-dlp's test cases. This environment cannot resolve X destinations in the sandbox; a separate proxied request to `api.x.com` received CONNECT HTTP 403. No successful live download is claimed. Add the X destinations listed in DEPLOYMENT.md to the environment's network settings and re-test with authorized content on the deployment server. Do not disable DNS or TLS protections.
* **Physical Android device/emulator:** not run. The Java plugin compiled, but DownloadManager completion, playback, Android navigation, and device-specific behavior need a phone test.
* **Hosted HTTPS backend:** not provisioned. The APK has no hardcoded server; open Settings and connect your deployed HTTPS origin. Local Docker service addresses cannot be used from a phone without reachable HTTPS hosting.
* **Release signing / Play Store publication:** not performed. This is a debug-signed test build.
* **Reusable cloud settings draft:** attempted to save installation and startup instructions; the tool returned an error that saving could not be confirmed. Publication and fresh-task restoration were not verified. Repository documentation is available independently.

## Deliberate scope

Public progressive MP4 streams are supported, including streams where X does not label the audio codec. HLS and separate audio/video formats are excluded. No merge or upscaling is performed; FFmpeg is present but is not invoked on remote media. Jobs and private tokens are held in server memory and expire; they do not survive a server restart. Closing/restarting the app loses access to an in-progress job; the backend still expires and cleans it up.
