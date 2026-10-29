[app]

# Tên ứng dụng
title = Alarm Controller
package.name = alarmapp
package.domain = org.example

# Version
version = 1.0.0
version.code = 1

# Kivy requirements
requirements = python3,kivy==2.2.1,pyjnius==1.5.0,android==1.0

# Permissions
android.permissions = INTERNET,FOREGROUND_SERVICE,POST_NOTIFICATIONS,WAKE_LOCK,RECEIVE_BOOT_COMPLETED

# Service
services = AlarmService:alarm_service.py

# Foreground service
android.foreground = True
android.foreground.service = AlarmService

# API Level
android.api = 33
android.minapi = 21
android.targetapi = 33

# Build
android.ndk = 23b
android.sdk = 33

# Orientation
android.orientation = portrait

# WakeLock
android.wakelock = True

# Gửi hook để sửa manifest
p4a.hook = hook.py

# Assets
android.add_src = alarm_sound.mp3

# Icon
android.icon = assets/icon.png

# Gradle dependencies
android.gradle_dependencies = 'androidx.core:core:1.9.0','androidx.media:media:1.6.0'

# Presplash
# android.presplash = assets/presplash.png

# Debug
android.debug = True
android.logcat_filters = *:S python:D