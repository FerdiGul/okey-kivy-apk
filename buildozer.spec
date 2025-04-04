
[app]

title = Okey 101 Yardımcı
package.name = okeyyardimci
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy
orientation = portrait
fullscreen = 1
android.archs = arm64-v8a,armeabi-v7a
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1


android.build_tools_version = 30.0.3
android.api = 33
android.ndk = 23b
