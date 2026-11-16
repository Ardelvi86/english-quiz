[app]
title = English Quiz
package.name = englishquiz
package.domain = org.arturodelvillar
source.dir = .
source.include_exts = py,kv,png,jpg,mp3,wav,ttf,txt
version = 1.0
requirements = python3,kivy,plyer
orientation = portrait
fullscreen = 0
android.permissions = RECORD_AUDIO, INTERNET
android.api = 33
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
