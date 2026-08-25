import os
import urllib.request
import json
import yt_dlp

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def fetch_quick_info(url):
    """Fetch title, thumbnail, and author instantly (<0.4s) via oEmbed for immediate UI preview."""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return {
                "title": data.get("title", "Video"),
                "thumbnail": data.get("thumbnail_url", ""),
                "uploader": data.get("author_name", "YouTube"),
                "url": url,
            }
    except Exception:
        return None

def format_bytes(bytes_num):
    if not bytes_num or bytes_num <= 0:
        return "Unknown size"
    if bytes_num >= 1024 * 1024 * 1024:
        return f"{bytes_num / (1024**3):.1f} GB"
    return f"{bytes_num / (1024**2):.1f} MB"

def calculate_format_sizes(info):
    duration = info.get("duration") or 0
    formats = info.get("formats", [])
    
    # Calculate best audio size
    audio_sizes = [
        f.get("filesize") or f.get("filesize_approx") or ((f.get("tbr") or 0) * 125 * duration)
        for f in formats
        if (f.get("vcodec") == "none" or not f.get("vcodec")) and f.get("acodec") != "none"
    ]
    best_audio_sz = max([sz for sz in audio_sizes if sz > 0], default=0)
    
    sizes_map = {}
    for target_h in [2160, 1440, 1080, 720, 480, 360, 240, 144]:
        v_sizes = [
            f.get("filesize") or f.get("filesize_approx") or ((f.get("tbr") or 0) * 125 * duration)
            for f in formats
            if f.get("height") and abs(f.get("height") - target_h) <= 30
        ]
        v_sz = max([sz for sz in v_sizes if sz > 0], default=0)
        if v_sz > 0:
            sizes_map[target_h] = format_bytes(v_sz + best_audio_sz)
        else:
            sizes_map[target_h] = "N/A"
        
    sizes_map["audio"] = format_bytes(best_audio_sz) if best_audio_sz > 0 else "Unknown size"
    return sizes_map

def fetch_video_info(url):
    """Optimized video info & format size extraction."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "check_formats": False,
        "youtube_include_hls_manifest": False,
        "youtube_include_dash_manifest": False,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        sizes = calculate_format_sizes(info)
        return {
            "title": info.get("title", "Video"),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", info.get("channel", "Unknown Channel")),
            "view_count": info.get("view_count", 0),
            "sizes": sizes,
            "url": url,
        }

def download_media(url, mode, height=None, progress_callback=None, tag="Best", output_dir=None):
    if not output_dir:
        output_dir = SCRIPT_DIR
        
    out_template = os.path.join(output_dir, f"%(title)s [{tag}].%(ext)s")
    
    def hook(d):
        if progress_callback:
            status = d.get("status", "")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                pct = (downloaded / total) * 100 if total > 0 and downloaded > 0 else 0
                speed = d.get("_speed_str", "0 KB/s").strip()
                eta = d.get("_eta_str", "--:--").strip()
                progress_callback({
                    "status": "downloading",
                    "pct": min(max(pct / 100.0, 0.0), 1.0),
                    "pct_str": f"{pct:.1f}%",
                    "speed": speed,
                    "eta": eta,
                })
            elif status == "finished":
                progress_callback({
                    "status": "finished",
                    "pct": 1.0,
                    "pct_str": "100%",
                    "speed": "--",
                    "eta": "00:00",
                })

    if mode == "mp3":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "noplaylist": True,
            "progress_hooks": [hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    elif mode == "m4a":
        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": out_template,
            "noplaylist": True,
            "progress_hooks": [hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }],
        }
    else:  # video mode
        if height:
            format_str = (
                f"bestvideo[height<={height}][vcodec^=avc]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={height}][vcodec^=avc]+bestaudio/"
                f"bestvideo[height<={height}]+bestaudio/"
                f"best[height<={height}]/best"
            )
        else:
            format_str = (
                "bestvideo[vcodec^=avc]+bestaudio[ext=m4a]/"
                "bestvideo[vcodec^=avc]+bestaudio/"
                "bestvideo+bestaudio/best"
            )
        ydl_opts = {
            "format": format_str,
            "merge_output_format": "mp4",
            "outtmpl": out_template,
            "noplaylist": True,
            "progress_hooks": [hook],
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
