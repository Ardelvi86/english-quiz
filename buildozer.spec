[app]
title = English Quiz
package.name = englishquiz
package.domain = org.arturodelvillar
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,mp3,wav,ttf,txt
version = 1.1
requirements = python3,kivy==2.3.1,pyjnius,pillow,openssl,certifi
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.ndk = 28c
android.permissions = RECORD_AUDIO,INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1