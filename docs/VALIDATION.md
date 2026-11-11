# Android 2.0 validation

Performed on 2026-11-11 against the direct-on-device implementation.

## Passed

- Frontend: 17 tests (6 existing website tests, 8 post URL validation tests, 3 native UI flow tests). Direct extraction/quality selection/download completion, cancellation, error recovery, and absence of backend fetches covered with a mocked native bridge.
- Native JVM tests: 7 passed (4 syndication parser fixtures, 2 trusted MP4 URL/quality tests, 1 existing template test). Parser supports `mediaDetails[].video_info.variants` and legacy `video.variants`, excludes HLS/other hosts, deduplicates URLs, rejects unavailable/video-free posts.
- TypeScript check, Vite production build, Capacitor Android sync, and Gradle `:app:assembleDebug :app:testDebugUnitTest` passed.
- Chromium mobile UI at 390×844: direct Android screen loaded with no horizontal overflow or JavaScript runtime errors. This is a browser UI smoke check, not a native plugin/device test.
- APK signature verified with apksigner (v2); manifest checked with aapt: package `com.xsave.downloader`, version `2.0`/code `2`, minimum SDK 29, target SDK 35.
- APK SHA-256: `4591de78d3e09b7b0a723f8889accc316ca245334c5a149d08a408546db8652f`.

## Limitations and device checks still required

A proxied request to `cdn.syndication.twimg.com` was denied by cloud network policy (CONNECT 403). No live X extraction or video download success is claimed. On an Android phone with Internet access, verify a permitted public post, quality options, MP4 playback/audio, progress, cancellation, and background download notification/completion. X can restrict posts or change its public endpoint. No authentication cookies or restriction bypass is implemented.

This build is debug-signed with a different certificate from the earlier APK. Uninstall the old test app before installing. Release signing and store distribution are not performed. A physical device/emulator was not run (this environment has no `/dev/kvm`).

The app tracks downloads in memory; after an app/process restart use Android Downloads or its notification for completion. Only the first embedded video and progressive MP4 formats are offered. The browser website still uses the existing backend; the Android app does not.

---

# Historical validation (1.0)

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
