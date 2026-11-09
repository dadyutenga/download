# Deployment

1. Install Docker Engine and Compose v2 on a Linux host with public DNS and outbound HTTPS to X.
2. Copy `.env.example` to `.env`, review resource limits, run `docker compose up -d --build`.
3. Place an HTTPS reverse proxy or load balancer in front of `127.0.0.1:8080`. Point your domain at this host, provision a valid certificate, and proxy all paths. Disable access logging of query strings at every proxy, CDN, and monitoring layer. Disable response buffering for `/api/v1/downloads/*/events` and allow at least 240 seconds for requests.
4. Verify `/api/v1/health`, then set the HTTPS origin in Android Settings. The Android WebView origin `https://localhost` must remain in CORS_ORIGINS. Native Android uses real OS DownloadManager to save files to the public Downloads folder and notify on completion.
5. Test with a public video you own or have permission to save. Check progress, cancel, quality, downloaded playback, and expired link denial on an actual phone before distributing.

This service intentionally has **one API process** with bounded child download processes. Do not run multiple Uvicorn workers or replicas against the same data directory: job ownership and state are in memory. Restart invalidates all references/tokens and clears retained files. Horizontal scaling requires shared persistent job state and a proper queue as a separate change. Downloads do not resume after server/app restarts. Partial files are removed on error/cancellation. Data resides in a bounded tmpfs in Compose; adjust its size together with memory/worker limits.

## Outbound policy

Permit HTTPS to `x.com`, `www.x.com`, `api.x.com`, `twitter.com`, `www.twitter.com`, `mobile.twitter.com`, `api.twitter.com`, `syndication.twitter.com`, `cdn.syndication.twimg.com`, `video.twimg.com`, `pbs.twimg.com`, `abs.twimg.com`. The application rejects other hosts and insecure/credentialed/nonstandard-port URLs, checks DNS, pins direct connections to public IPs, and revalidates every redirect. A configured outbound proxy is an administrator trust boundary: it must enforce public-only destination resolution itself to prevent DNS rebinding at the proxy. No user cookies, login tokens, DRM bypass, or private-account access are supported.

The app currently offers progressive MP4 with included audio only; HLS and separate audio/video streams are excluded. FFmpeg is included for future local processing, but no remote media is passed to FFmpeg. This limits supported posts and formats intentionally; it does not synthesize missing qualities.

## Android release

Requirements: JDK 21, Android SDK platform 35/build tools 34.0.0 (AGP default), Node 22+, accepted Android SDK licenses. `cd frontend; npm ci; npm run android:sync; cd android; ./gradlew assembleDebug`. Set ANDROID_HOME to your SDK, or create ignored `android/local.properties` with `sdk.dir=...`.

Debug APK: `frontend/android/app/build/outputs/apk/debug/app-debug.apk` (Android 10+). A debug APK is for sideload testing, not Play Store release. For distribution, use your own private signing key via Android Studio's Generate Signed Bundle/APK flow; never commit keystores or signing passwords. Use `bundleRelease` for a signed Play Store AAB. Verify content rights, privacy disclosures, and store rules before distribution. There is no hosted backend provisioned by this repository: configure your own HTTPS server in app Settings.

## Cloud build note

This workspace stores Android tooling outside the checkout under `/workspace/android-sdk` and Gradle under `/workspace/gradle/gradle-8.11.1`. When reusing this prepared machine, set JAVA_HOME to `/workspace/android-sdk/jdk/jdk-21.0.9`, ANDROID_HOME to `/workspace/android-sdk`, ANDROID_USER_HOME to `/workspace/android-sdk/user-home`, and GRADLE_USER_HOME to `/workspace/android-sdk/gradle-home`. The cloud home directory is read-only. Java tooling also needs the inherited proxy translated into `http.proxyHost`, `http.proxyPort`, `https.proxyHost`, and `https.proxyPort` system properties, plus `javax.net.ssl.trustStore=/workspace/android-sdk/java-cacerts` (store password `changeit`, a public CA truststore, not a credential). Keep TLS verification enabled. These cloud-specific overrides are not needed for a normal Android Studio installation.
