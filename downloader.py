#!/usr/bin/env python3
import os
import sys
import yt_dlp
from downloader_core import fetch_video_info, download_media

QUALITY_OPTIONS = {
    "1": ("144p", 144, "video", "144p"),
    "2": ("240p", 240, "video", "240p"),
    "3": ("360p", 360, "video", "360p"),
    "4": ("480p", 480, "video", "480p"),
    "5": ("720p (HD)", 720, "video", "720p"),
    "6": ("1080p (Full HD)", 1080, "video", "1080p"),
    "7": ("1440p (2K)", 1440, "video", "1440p 2K"),
    "8": ("2160p (4K)", 2160, "video", "2160p 4K"),
    "9": ("Best available video", None, "video", "Best"),
    "10": ("Audio Only (MP3)", "MP3", "mp3", "MP3"),
    "11": ("Audio Only (M4A)", "M4A", "m4a", "M4A"),
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def choose_quality(url=None):
    sizes = {}
    if url:
        print("\n🔍 Fetching video details & estimating data sizes...")
        try:
            info = fetch_video_info(url)
            sizes = info.get("sizes", {})
            print(f"🎬 Title: {info.get('title')}\n")
        except Exception:
            pass

    print("Select download format / quality:")
    for key, (label, height_or_tag, mode, tag) in QUALITY_OPTIONS.items():
        if mode == "video":
            sz_str = sizes.get(height_or_tag, "") if height_or_tag else ""
        else:
            sz_str = sizes.get("audio", "")
        
        size_display = f" [~{sz_str}]" if sz_str and sz_str != "Unknown size" else ""
        print(f"  {key:>2}. {label}{size_display}")
        
    choice = input("\nEnter choice (1-11): ").strip()
    if choice not in QUALITY_OPTIONS:
        print("Invalid choice, defaulting to Best available video.")
        choice = "9"
    return QUALITY_OPTIONS[choice]

def progress_hook(d):
    if d["status"] == "downloading":
        pct = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "").strip()
        print(f"\r{pct} at {speed}", end="")
    elif d["status"] == "finished":
        print("\nDownload finished, processing output...")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python downloader.py <video_url>")
        sys.exit(1)
    video_url = sys.argv[1]
    label, height_or_tag, mode, tag = choose_quality(video_url)
    print(f"\nDownloading in: {label}\n")
    download_media(video_url, mode, height=height_or_tag if mode == "video" else None, tag=tag)