# XSave 2.0 Android test APK

Download [XSave-debug.apk](XSave-debug.apk) using GitHub’s **Download raw file** button.

Android 10+; debug-signed for sideload testing. Extracts public X video options directly on the phone and saves MP4 files to Android Downloads. **No backend server or server settings required.**

This build has a different debug signing certificate from the previous checked-in APK. Uninstall the old test app before installing 2.0; Android will reject an in-place update signed with a different key. No release signing key is included in the repository.

Frontend tests, native parser/URL tests, APK assembly, signature validation, and a mobile browser UI smoke check passed. Live X extraction and Android DownloadManager behavior on a physical device have not been verified: cloud requests to X’s syndication service are blocked. Test with a public video you own or may download before relying on it. Only public progressive MP4 videos exposed by X’s public embed service are supported. See [validation](../docs/VALIDATION.md).

Version code: `2`; package: `com.xsave.downloader`; minimum Android: `10`; target SDK: `35`.

SHA-256: `4591de78d3e09b7b0a723f8889accc316ca245334c5a149d08a408546db8652f`.
