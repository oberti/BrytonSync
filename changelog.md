# Changelog

All notable changes to this project will be documented in this file.

---

# v2.0.0 - 2026-06-18

## Added

### Bryton Activities

* Automatic login to Bryton Active
* Download recent activities
* Direct FIT download support
* Activity detail retrieval
* Automatic FIT filename generation

### Intervals.icu

* Upload activities to Intervals.icu
* Duplicate detection using External ID
* Automatic athlete integration

### Dropbox

* Dropbox OAuth PKCE authentication
* Refresh token support
* Automatic FIT upload
* Configurable destination folder

### Planned Workouts

* Download planned workouts from Intervals.icu
* Upload workouts to Bryton Active
* Support for power-based workouts
* Support for heart-rate-based workouts
* Repeat interval conversion
* Workout FIT generation

### Applications

* Desktop GUI (Flet)
* Android APK
* Command Line Interface (CLI)

## Improved

* Deleted Bryton activities are automatically skipped
* Better handling of Bryton FIT downloads
* Improved logging
* Better sync status reporting
* Automatic duplicate prevention

## Fixed

* Direct FIT download handling (`application/octet-stream`)
* Dropbox authentication issues
* Android browser launch for Dropbox OAuth
* Android UI refresh after sync operations
* Workout conversion for heart-rate targets
* Workout FIT generation compatibility with Bryton devices

---

# v1.0.0

Initial public release.

## Features

* Bryton activity download
* Intervals.icu upload
* Dropbox upload
* Android APK
* Dropbox OAuth support
