# 📱 NDownloader - Android APK Build Guide

Sleek, White Theme, Ad-Free YouTube Video & Audio Downloader Android App.

---

## ⚡ How to Get the `.apk` File for Your Android Phone

### Method 1: 1-Click Automated APK Build via GitHub Actions (Recommended)
You don't need Flutter or Android Studio installed on your PC.

1. Push this workspace folder to your GitHub repository (`git push origin main`).
2. Open your GitHub repository in your browser and click on the **Actions** tab.
3. You will see **"Build NDownloader APK"** running automatically (takes ~2 minutes).
4. Click on the completed run and download **NDownloader-APK.zip** under **Artifacts**.
5. Extract the `.apk` file, transfer it to your Android phone, and tap to install!

---

### Method 2: Build Locally via Flet CLI

If you have Flutter SDK installed on your PC:

```bash
# 1. Install dependencies
pip install flet yt-dlp

# 2. Compile APK
flet build apk
```

The output file `NDownloader.apk` will be saved in `build/apk/`.

---

## 💻 Preview White Theme on PC

Run on your computer:
```bash
python app.py
```
