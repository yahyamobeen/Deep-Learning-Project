# Mobile App (Flutter)

Flutter client for the Sign Language Translator & Tutor. Same backend as the
web app — phone records → uploads to FastAPI → renders the response.

## Prerequisites

- Flutter SDK ≥ 3.22 (https://docs.flutter.dev/get-started/install)
- Android Studio (for Android emulator + SDK)
- A real Android phone for E2E testing (recommended) — emulator camera is fake

Verify install:
```
flutter doctor
```

## First run (Windows)

```
cd mobile
copy .env.example .env       # then edit GATEWAY_URL
flutter pub get
flutter run                  # picks up an emulator or a USB-attached phone
```

For the **Android emulator**, leave `GATEWAY_URL=http://10.0.2.2:4000`
(this is the emulator's loopback to your laptop's localhost).
For a **physical phone**, set it to your laptop's LAN IP, e.g.
`http://192.168.1.42:4000`.

## Build a release APK (for direct install / Firebase distribution)

```
flutter build apk --release
# output: build/app/outputs/flutter-apk/app-release.apk
```

See `docs/MOBILE_RELEASE.md` (project root) for app signing and Firebase
App Distribution steps.

## Project layout

```
lib/
├── main.dart
├── theme.dart
├── api/api_client.dart           # dio instance + JWT interceptor
├── widgets/
│   ├── camera_recorder.dart      # 3-sec capped MP4 recorder
│   └── clip_player.dart          # serial network-clip player
└── screens/
    ├── home_screen.dart
    ├── sign_to_text_screen.dart
    ├── text_to_sign_screen.dart
    ├── speech_to_sign_screen.dart
    └── tutor_screen.dart
```

## Backend contract used by this app

| Method | Path | Sends | Returns |
|---|---|---|---|
| POST | `/api/translate/sign-to-text`   | multipart `file=mp4` | `{gloss, sentence, confidence, top5}` |
| POST | `/api/translate/text-to-sign`   | json `{text}`        | `{gloss[], clips[]}` |
| POST | `/api/translate/speech-to-sign` | multipart `file=m4a` | `{transcript, gloss[], clips[]}` |
| GET  | `/api/tutor/lessons`            | —                    | `[{id, label, video, level}]` |
| POST | `/api/tutor/score`              | multipart `lesson_id, file` | `{score, hint, passed}` |
