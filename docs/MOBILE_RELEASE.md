# Mobile Release Guide (Flutter → Android → distribution)

Three release paths, in order of complexity:

| Path | Best for | Cost | Per-build effort |
|---|---|---|---|
| A — Direct APK install | Day-1 testing on team phones | $0 | one command |
| B — Firebase App Distribution | Sharing with up to 100 testers, versioned, auto-update | $0 | one command |
| C — Google Play Internal Testing | Official store listing | one-time $25 | a few minutes |
| D — iOS TestFlight | iOS users | $99/yr Apple Dev | needs a Mac |

**Recommended for this project:** A for development, B for the demo / submission. Skip C and D unless you specifically need them.

---

## Setup once: Generate an upload keystore

You only do this once per app. **Save the keystore — losing it locks you out of updating the published app forever.**

```
keytool -genkey -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

Move the file to `mobile/android/app/upload-keystore.jks` (already gitignored).

Create `mobile/android/key.properties` (also gitignored):
```
storePassword=<password from above>
keyPassword=<password from above>
keyAlias=upload
storeFile=upload-keystore.jks
```

Edit `mobile/android/app/build.gradle`:
```gradle
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

android {
    ...
    signingConfigs {
        release {
            keyAlias = keystoreProperties['keyAlias']
            keyPassword = keystoreProperties['keyPassword']
            storeFile = keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
            storePassword = keystoreProperties['storePassword']
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.release
            minifyEnabled = false
        }
    }
}
```

**Back up the keystore + `key.properties` to a private repo or 1Password vault.**

---

## Path A — Direct APK install (free, day-1)

```
cd mobile
flutter clean && flutter pub get
flutter build apk --release
```

Output:
```
build/app/outputs/flutter-apk/app-release.apk
```

Upload to Google Drive, share the link. On any Android phone:
1. Settings → Apps → Special access → Install unknown apps → enable Drive.
2. Tap the link → "Install".

---

## Path B — Firebase App Distribution (free, professional)

### One-time Firebase setup

1. https://console.firebase.google.com → Add project → name it (e.g., `uet-signlang`).
2. Add an Android app:
   - Package name: `pk.uet.signlang` (must match `applicationId` in `mobile/android/app/build.gradle`).
   - Download `google-services.json` → place in `mobile/android/app/`.
3. Install Firebase CLI on your laptop:
   ```
   npm install -g firebase-tools
   firebase login
   ```
4. In `mobile/`:
   ```
   firebase init appdistribution
   ```
5. In Firebase console → App Distribution → "Testers & Groups" → create group `testers` → add tester emails.

### Per-release commands

```
cd mobile
flutter build apk --release
firebase appdistribution:distribute build/app/outputs/flutter-apk/app-release.apk \
  --app <FIREBASE_APP_ID> \
  --release-notes "Sprint N: tutor screen polish" \
  --groups "testers"
```

Testers receive an email with an install link. App auto-updates on subsequent
distributions.

---

## Path C — Google Play Internal Testing (one-time $25)

1. Pay $25 once at https://play.google.com/console.
2. Build an **App Bundle** (`.aab`), not an APK:
   ```
   cd mobile
   flutter build appbundle --release
   # output: build/app/outputs/bundle/release/app-release.aab
   ```
3. Play Console → Create app → Internal testing → Create new release → upload `.aab` → fill in store listing → Roll out.
4. Add tester emails or a Google Group. Send them the opt-in URL — they install via Play Store.

---

## Path D — iOS TestFlight (needs Mac + $99/yr)

Skip unless someone on the team has a Mac and Apple Dev membership. The
high-level steps:

1. On a Mac: `cd mobile && flutter build ios --release`.
2. Open `mobile/ios/Runner.xcworkspace` in Xcode → set up signing → Archive → Distribute → upload to App Store Connect.
3. App Store Connect → TestFlight → add internal testers.

---

## Build version bumps

Before every release, bump the version in `mobile/pubspec.yaml`:
```yaml
version: 0.1.1+2     # name+code (Android requires +N to be strictly increasing)
```

---

## Common Android build failures

| Symptom | Fix |
|---|---|
| `Execution failed for task ':app:processReleaseGoogleServices'` | `google-services.json` missing or wrong package — re-download from Firebase. |
| `App not installed` on the phone | Mixing debug+release signing. Always rebuild with `flutter clean` between modes. |
| Camera silently fails | Check `AndroidManifest.xml` has `<uses-permission android:name="android.permission.CAMERA"/>` AND the runtime asks via `permission_handler`. |
| HTTPS only, plain HTTP fails | `android:usesCleartextTraffic="true"` is set, but for production set `GATEWAY_URL` to https and remove this flag. |
| Build size > 100 MB | Run `flutter build apk --release --split-per-abi` to ship per-ABI APKs. |

---

## Demo-day phone checklist

- [ ] APK installed on at least 2 phones (in case one fails)
- [ ] Both phones charged + power bank
- [ ] Personal hotspot tested (don't trust venue Wi-Fi)
- [ ] `GATEWAY_URL` in the bundled `.env` points to the **deployed** gateway
- [ ] Pre-recorded 2-min demo video on USB as backup
