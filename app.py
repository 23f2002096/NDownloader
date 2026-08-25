import flet as ft
import threading
import os
from downloader_core import fetch_video_info, fetch_quick_info, download_media

BASE_QUALITY_OPTIONS = [
    ("1080p (Full HD)", 1080, "video", "1080p"),
    ("720p (HD)", 720, "video", "720p"),
    ("2160p (4K Ultra)", 2160, "video", "2160p 4K"),
    ("1440p (2K Quad HD)", 1440, "video", "1440p 2K"),
    ("480p", 480, "video", "480p"),
    ("360p", 360, "video", "360p"),
    ("Best Video Available", None, "video", "Best"),
    ("Audio Only (MP3)", "MP3", "mp3", "MP3"),
    ("Audio Only (M4A)", "M4A", "m4a", "M4A"),
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(SCRIPT_DIR, "assets", "logo.png")

def main(page: ft.Page):
    page.title = "NDownloader"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#ffffff"  # Clean White Theme
    page.padding = 24
    page.window.width = 440
    page.window.height = 760
    page.window.resizable = True

    # Header with uploaded logo
    logo_widget = ft.Image(
        src=LOGO_PATH if os.path.exists(LOGO_PATH) else "",
        width=72,
        height=72,
        fit="contain",
    ) if os.path.exists(LOGO_PATH) else ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, size=48, color="#0f172a")

    header = ft.Column(
        [
            logo_widget,
            ft.Text("NDownloader", size=26, weight="bold", color="#0f172a"),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
    )

    # State variables
    current_video_info = [None]

    # Controls
    url_input = ft.TextField(
        hint_text="Paste Video Link here...",
        expand=True,
        border_radius=12,
        bgcolor="#f8fafc",
        border_color="#e2e8f0",
        focused_border_color="#0f172a",
        color="#0f172a",
        content_padding=14,
    )

    paste_btn = ft.IconButton(
        icon=ft.Icons.CONTENT_PASTE_ROUNDED,
        icon_color="#0f172a",
        tooltip="Paste Link",
        on_click=lambda e: paste_clipboard(),
    )

    fetch_btn = ft.Button(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.SEARCH_ROUNDED, color="#ffffff", size=18),
                ft.Text("Fetch Info & Data Sizes", color="#ffffff", size=14, weight="bold"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        ),
        style=ft.ButtonStyle(
            bgcolor="#0f172a",
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=14,
        ),
        on_click=lambda e: start_fetch_info(),
    )

    # Preview Card Controls
    thumbnail_img = ft.Image(
        src="",
        width=380,
        height=210,
        fit="cover",
        border_radius=12,
        visible=False,
    )

    title_text = ft.Text(
        "",
        size=15,
        weight="bold",
        color="#0f172a",
        max_lines=2,
        overflow=ft.TextOverflow.ELLIPSIS,
    )
    
    uploader_text = ft.Text("", size=12, color="#64748b")

    preview_card = ft.Container(
        content=ft.Column(
            [
                thumbnail_img,
                title_text,
                uploader_text,
            ],
            spacing=8,
        ),
        padding=12,
        bgcolor="#f8fafc",
        border=ft.Border.all(1, "#e2e8f0"),
        border_radius=16,
        visible=False,
    )

    # Dropdown format selector
    quality_dropdown = ft.Dropdown(
        label="Download Format & Data Size",
        options=[ft.dropdown.Option(text=opt[0], key=str(idx)) for idx, opt in enumerate(BASE_QUALITY_OPTIONS)],
        value="0",
        border_radius=12,
        bgcolor="#f8fafc",
        border_color="#e2e8f0",
        focused_border_color="#0f172a",
        color="#0f172a",
    )

    # Progress & Status Controls
    progress_bar = ft.ProgressBar(value=0, color="#2563eb", bgcolor="#e2e8f0", height=8, visible=False)
    status_text = ft.Text("Ready", size=13, color="#64748b", weight="w500")
    speed_text = ft.Text("", size=12, color="#2563eb")

    download_btn = ft.Button(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.FILE_DOWNLOAD_ROUNDED, color="#ffffff", size=22),
                ft.Text("Download Now", color="#ffffff", size=16, weight="bold"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        style=ft.ButtonStyle(
            bgcolor="#2563eb",
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=14,
        ),
        width=380,
        height=48,
        on_click=lambda e: start_download(),
    )

    def paste_clipboard():
        try:
            val = page.get_clipboard()
            if val:
                url_input.value = val
                page.update()
                start_fetch_info()
        except Exception:
            pass

    def start_fetch_info():
        url = url_input.value.strip()
        if not url:
            status_text.value = "⚠️ Please enter a valid video link"
            status_text.color = "#ef4444"
            page.update()
            return

        status_text.value = "⚡ Loading preview..."
        status_text.color = "#2563eb"
        page.update()

        def background_fetch():
            # Step 1: Instant oEmbed preview (<0.4s)
            quick_info = fetch_quick_info(url)
            if quick_info:
                thumbnail_img.src = quick_info["thumbnail"]
                thumbnail_img.visible = True
                title_text.value = quick_info["title"]
                uploader_text.value = f"👤 {quick_info['uploader']}"
                preview_card.visible = True
                status_text.value = "🔍 Calculating quality sizes..."
                page.update()

            # Step 2: Full format size calculation
            try:
                info = fetch_video_info(url)
                current_video_info[0] = info
                if not quick_info:
                    thumbnail_img.src = info["thumbnail"]
                    thumbnail_img.visible = True
                    title_text.value = info["title"]
                    uploader_text.value = f"👤 {info['uploader']}"
                    preview_card.visible = True

                # Dynamic format options with data sizes
                sizes = info.get("sizes", {})
                updated_options = []
                for idx, (label, height_or_tag, mode, tag) in enumerate(BASE_QUALITY_OPTIONS):
                    if mode == "video":
                        sz_str = sizes.get(height_or_tag, "N/A") if height_or_tag else ""
                    else:
                        sz_str = sizes.get("audio", "")
                    
                    if sz_str and sz_str != "Unknown size":
                        if sz_str == "N/A":
                            display_text = f"{label} (Not Available)"
                        else:
                            display_text = f"{label} (~{sz_str})"
                    else:
                        display_text = label
                        
                    updated_options.append(ft.dropdown.Option(text=display_text, key=str(idx)))
                
                quality_dropdown.options = updated_options
                quality_dropdown.value = "0"

                status_text.value = "✅ Ready! Select quality & tap Download."
                status_text.color = "#16a34a"
            except Exception as ex:
                if not quick_info:
                    status_text.value = f"❌ Failed to fetch info: {str(ex)[:60]}"
                    status_text.color = "#ef4444"
                else:
                    status_text.value = "✅ Preview loaded! Tap Download."
                    status_text.color = "#16a34a"
            page.update()

        threading.Thread(target=background_fetch, daemon=True).start()

    def start_download():
        url = url_input.value.strip()
        if not url:
            status_text.value = "⚠️ Please enter a video link first"
            status_text.color = "#ef4444"
            page.update()
            return

        selected_idx = int(quality_dropdown.value or 0)
        opt_label, height_or_tag, mode, tag = BASE_QUALITY_OPTIONS[selected_idx]

        download_btn.disabled = True
        progress_bar.visible = True
        progress_bar.value = 0
        status_text.value = f"⏳ Starting download ({opt_label})...."
        status_text.color = "#2563eb"
        speed_text.value = ""
        page.update()

        def update_progress(data):
            if data["status"] == "downloading":
                progress_bar.value = data["pct"]
                status_text.value = f"⬇️ Downloading... {data['pct_str']}"
                speed_text.value = f"Speed: {data['speed']} | ETA: {data['eta']}"
            elif data["status"] == "finished":
                progress_bar.value = 1.0
                status_text.value = "🔄 Merging & processing file..."
                speed_text.value = "Almost done!"
            page.update()

        def background_dl():
            try:
                download_media(
                    url=url,
                    mode=mode,
                    height=height_or_tag if mode == "video" else None,
                    progress_callback=update_progress,
                    tag=tag,
                )
                status_text.value = "🎉 Download Completed! Saved successfully."
                status_text.color = "#16a34a"
                speed_text.value = ""
                progress_bar.value = 1.0
            except Exception as ex:
                status_text.value = f"❌ Download error: {str(ex)[:70]}"
                status_text.color = "#ef4444"
                speed_text.value = ""
            finally:
                download_btn.disabled = False
                page.update()

        threading.Thread(target=background_dl, daemon=True).start()

    # Layout assembly
    page.add(
        ft.Column(
            [
                header,
                ft.Divider(color="#e2e8f0", height=15),
                ft.Row([url_input, paste_btn]),
                fetch_btn,
                preview_card,
                quality_dropdown,
                download_btn,
                progress_bar,
                status_text,
                speed_text,
            ],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

if __name__ == "__main__":
    ft.run(main)
