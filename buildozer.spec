[app]
title = 算术麻将简单版
package.name = suanshumahjong
package.domain = org.jetfirex

source.dir = .
source.include_exts = py,png,ico,ttf,ttc
source.exclude_dirs = .git,.idea,.venv,venv,env,build,dist,__pycache__,.pytest_cache,test

version = 0.1.0
requirements = python3,kivy==2.3.1
orientation = portrait
fullscreen = 0

icon.filename = pictures/app_icon.png

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.api = 35
android.minapi = 23
android.archs = arm64-v8a, armeabi-v7a
android.permissions =
android.gradle_dependencies =

[ios]

