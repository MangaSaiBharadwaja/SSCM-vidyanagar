[app]
title = sscm
package.name = templesscm
package.domain = org.sscm
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,db,txt,html,css,js
version = 1.0

requirements = python3,kivy,kivymd,flask,flask-sqlalchemy,flask-login,flask-wtf,werkzeug,python-dotenv,sqlalchemy,openpyxl,pandas
bootstrap = sdl2
android.api = 30

[app:android]
orientation = portrait
fullscreen = 0
permissions = INTERNET
arch = armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
