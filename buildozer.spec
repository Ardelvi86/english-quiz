[app]
title = English Quiz
package.name = englishquiz
package.domain = org.arturodelvillar
source.dir = .
source.include_exts = py,kv,png,jpg,mp3,wav,ttf,txt
version = 1.0
requirements = python3,kivy==2.3.1,pyjnius
orientation = portrait
fullscreen = 0
android.permissions =
android.api = 29
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.ndk = 28c
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1