import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import yt_dlp
import sys, io
import os
import re
import threading
import urllib.request
from io import BytesIO
import time
from colorama import init as colorama_init
from urllib.parse import urlparse
from datetime import datetime

def set_console_title(title: str):
    if os.name == "nt":
        try:
            os.system(f"title {title}")
        except:
            pass

APP_NAME = "FluxMedia Downloader v2.1"
CREATOR_NAME = "Charun OT"

def app_dir():

    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = app_dir()
FFMPEG_DIR = os.path.join(BASE_DIR, "FG - [1]")
FFMPEG_EXE = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
FFPROBE_EXE = os.path.join(FFMPEG_DIR, "ffprobe.exe")
BASE_OUTPUT_FOLDER = os.path.join(BASE_DIR, "FluxMedia_Base - [2026]")
LOG_FILE = os.path.join(BASE_DIR, "FluxMedia_Log.txt")

YT_ROOT_FOLDER = os.path.join(BASE_OUTPUT_FOLDER, "YouTube - [1]")
FB_ROOT_FOLDER = os.path.join(BASE_OUTPUT_FOLDER, "Facebook - [2]")
IG_ROOT_FOLDER = os.path.join(BASE_OUTPUT_FOLDER, "Instagram - [3]")
TT_ROOT_FOLDER = os.path.join(BASE_OUTPUT_FOLDER, "TikTok - [4]")

YT_MP4_FOLDER = os.path.join(YT_ROOT_FOLDER, "YT - (MP4)")
YT_MP3_FOLDER = os.path.join(YT_ROOT_FOLDER, "YT - (MP3)")

FB_MP4_FOLDER = os.path.join(FB_ROOT_FOLDER, "FB - (MP4)")
FB_MP3_FOLDER = os.path.join(FB_ROOT_FOLDER, "FB - (MP3)")

IG_MP4_FOLDER = os.path.join(IG_ROOT_FOLDER, "IG - (MP4)")
IG_MP3_FOLDER = os.path.join(IG_ROOT_FOLDER, "IG - (MP3)")

TT_MP4_FOLDER = os.path.join(TT_ROOT_FOLDER, "TT - (MP4)")
TT_MP3_FOLDER = os.path.join(TT_ROOT_FOLDER, "TT - (MP3)")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

def _log_to_file(level: str, msg: str):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] [{level}] {msg}\n")
    except:
        pass

def ensure_base_folders():
    os.makedirs(BASE_OUTPUT_FOLDER, exist_ok=True)
    for p in [
        YT_ROOT_FOLDER, YT_MP4_FOLDER, YT_MP3_FOLDER,
        FB_ROOT_FOLDER, FB_MP4_FOLDER, FB_MP3_FOLDER,
        IG_ROOT_FOLDER, IG_MP4_FOLDER, IG_MP3_FOLDER,
        TT_ROOT_FOLDER, TT_MP4_FOLDER, TT_MP3_FOLDER,
    ]:
        os.makedirs(p, exist_ok=True)

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
    
def strip_ansi(text: str) -> str:
        if not text:
            return ""
        return ANSI_RE.sub("", str(text))

def console_hud(level: str, msg: str):
    colors = {
        "OK": "\x1b[32m", 
        "INFO": "\x1b[36m", 
        "WARN": "\x1b[33m",  
        "ERR": "\x1b[31m",  
    }
    prefixes = {
        "OK":   "[OK] ",
        "INFO": "[INFO] ",
        "WARN": "[WARN] ",
        "ERR":  "[ERR] ",
    }
    c = colors.get(level, "\x1b[36m")
    p = prefixes.get(level, "[•]      ")
    clean = strip_ansi(msg)
    print(f"{c}{p}{clean}\x1b[0m")

def fmt_size(bytes_):
    if not bytes_:
        return "—"
    b = float(bytes_)
    for u in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            if u in ("MB", "GB"):
                return f"{b:.1f} {u}"
            return f"{b:.0f} {u}"
        b /= 1024
    return "—"

def fmt_duration(sec):
    if not sec:
        return "—"
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"

def fmt_date(d):
    if not d or len(d) != 8:
        return "—"
    return f"{d[6:8]}/{d[4:6]}/{d[0:4]}"

def content_type(duration):
    if not duration:
        return "—"
    duration = int(duration)
    if duration <= 60:
        return "Short"
    if duration <= 300:
        return "Video corto"
    return "Video largo"

def safe_ui(app, func, *args, **kwargs):
    app.after(0, lambda: func(*args, **kwargs))

def canonical_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url

def normalize_host(url: str) -> str:
    try:
        u = canonical_url(url)
        host = urlparse(u).netloc.lower()
        host = host.split("@")[-1]
        host = host.split(":")[0]
        return host
    except:
        return ""

def load_image_from_url(url: str) -> Image.Image | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        img = Image.open(BytesIO(data))
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        return img
    except Exception as e:
        _log_to_file("WARN", f"No se pudo cargar miniatura: {e}")
        return None

def display_title_short(title: str) -> str:
    if not title:
        return ""
    title = str(title).strip()
    if len(title) <= 45:
        return title
    return f"{title[0]}…"

def fmt_clock(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    try:
        s = int(max(0, seconds))
    except:
        return "—"
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def next_available_index(folder_path: str, prefix: str) -> int:
    os.makedirs(folder_path, exist_ok=True)
    used = set()
    pattern = re.compile(rf"^{re.escape(prefix)}\s-\s\((\d+)\)\..+$", re.IGNORECASE)
    for fn in os.listdir(folder_path):
        m = pattern.match(fn)
        if m:
            try:
                used.add(int(m.group(1)))
            except:
                pass
    n = 1
    while n in used:
        n += 1
    return n

def base_http_headers():
    return {"User-Agent": "Mozilla/5.0", "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"}

def get_cookiefile_for_platform(platform: str) -> str | None:
    p = (platform or "").lower().strip()
    m = {"facebook": "facebook.txt", "instagram": "instagram.txt", "tiktok": "tiktok.txt"}
    if p in m:
        path = os.path.join(BASE_DIR, "cookies", m[p])
        return path if os.path.exists(path) else None
    return None

class CancelledByUser(Exception):
    pass

PLATFORM_DOMAINS = {
    "YouTube": {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"},
    "Facebook": {"facebook.com", "www.facebook.com", "m.facebook.com", "fb.watch"},
    "Instagram": {"instagram.com", "www.instagram.com"},
    "TikTok": {"tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"},
}

def url_matches_platform(url: str, platform: str) -> bool:
    host = normalize_host(url)
    if not host:
        return False
    allowed = PLATFORM_DOMAINS.get(platform, set())
    if host in allowed:
        return True
    for d in allowed:
        if host.endswith("." + d):
            return True
    return False

PLATFORM_CFG = {
    "YouTube": {
        "panel_title": "YOUTUBE CONTROL PANEL",
        "mp4_folder": YT_MP4_FOLDER,
        "mp3_folder": YT_MP3_FOLDER,
        "file_prefix": "YT",
        "supports_fps": True,
        "supports_weight": True,
        "placeholder": "🔗 Pega link de YouTube",
    },
    "Facebook": {
        "panel_title": "FACEBOOK CONTROL PANEL",
        "mp4_folder": FB_MP4_FOLDER,
        "mp3_folder": FB_MP3_FOLDER,
        "file_prefix": "FB",
        "supports_fps": False,
        "supports_weight": False,
        "placeholder": "🔗 Pega link de Facebook (reel/video)",
    },
    "Instagram": {
        "panel_title": "INSTAGRAM CONTROL PANEL",
        "mp4_folder": IG_MP4_FOLDER,
        "mp3_folder": IG_MP3_FOLDER,
        "file_prefix": "IG",
        "supports_fps": False,
        "supports_weight": False,
        "placeholder": "🔗 Pega link de Instagram (reel/post)",
    },
    "TikTok": {
        "panel_title": "TIKTOK CONTROL PANEL",
        "mp4_folder": TT_MP4_FOLDER,
        "mp3_folder": TT_MP3_FOLDER,
        "file_prefix": "TT",
        "supports_fps": False,
        "supports_weight": False,
        "placeholder": "🔗 Pega link de TikTok",
    },
}

def hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    r = int(lerp(r1, r2, t))
    g = int(lerp(g1, g2, t))
    b = int(lerp(b1, b2, t))
    return rgb_to_hex((r, g, b))

class HoverAnimator:
    def __init__(self, widget, base_fg, hover_fg, base_border, hover_border, steps=10, ms=16):
        self.w = widget
        self.base_fg = base_fg
        self.hover_fg = hover_fg
        self.base_border = base_border
        self.hover_border = hover_border
        self.steps = steps
        self.ms = ms
        self._job = None
        self._state = 0.0

    def force_reset(self):
        try:
            if self._job:
                self.w.after_cancel(self._job)
        except:
            pass
        self._job = None
        self._state = 0.0
        try:
            self.w.configure(fg_color=self.base_fg, border_color=self.base_border)
        except:
            pass

    def _animate_to(self, target):
        if self._job:
            try:
                self.w.after_cancel(self._job)
            except:
                pass
            self._job = None

        start = self._state
        end = target
        total = self.steps

        def step(i=0):
            if not self.w.winfo_exists():
                return
            t = i / total
            cur = lerp(start, end, t)
            self._state = cur
            fg = lerp_color(self.base_fg, self.hover_fg, cur)
            bd = lerp_color(self.base_border, self.hover_border, cur)
            try:
                self.w.configure(fg_color=fg, border_color=bd)
            except:
                return
            if i < total:
                self._job = self.w.after(self.ms, lambda: step(i + 1))
            else:
                self._job = None

        step(0)

    def on_enter(self, _=None):
        self._animate_to(1.0)

    def on_leave(self, _=None):
        self._animate_to(0.0)

def attach_hover(widget, base_fg, hover_fg, base_border, hover_border):
    anim = HoverAnimator(widget, base_fg, hover_fg, base_border, hover_border, steps=10, ms=16)
    widget.bind("<Enter>", lambda e: (widget.cget("state") == "normal") and anim.on_enter(e))
    widget.bind("<Leave>", lambda e: anim.on_leave(e))
    return anim

class YTDLPLogger:
    def __init__(self, app=None):
        self.app = app

    def debug(self, msg):

        return

    def warning(self, msg):

        _log_to_file("WARN", strip_ansi(msg)) 

    def error(self, msg):
        m = strip_ansi(msg)
        if self.app:
            safe_ui(self.app, self.app.sys_err, m)
        else:
            console_hud("ERR", m)

class FluxMediaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1360x860")
        self.resizable(True, True)
        self.minsize(1360, 860)

        self.platform = "YouTube"
        self.prepared_platform = None

        self.thumb_img = None
        self.info_cache = None
        self.analysis_cache = {}
        self.yt_quality_profiles = None

        self.loading = False
        self.loading_text = ""
        self.loading_dots = 0

        self.is_prepared = False
        self.analyze_token = 0
        self.download_token = 0

        self.cancel_requested = False
        self.download_started_at = None

        self.build_ui()

        ensure_base_folders()
        self.sys_ok(f"FFmpeg detectado: {FFMPEG_EXE}")
        self.sys_ok("Carpetas base listas.")
        self.sys_info("Programa en ejecución • SYSTEM ONLINE")

        self.reset_ui(full=True)
        self.select_platform("YouTube")

    def _limit_url_200(self, event=None):
     txt = self.url_entry.get()
     if len(txt) > 200:
         self.url_entry.delete(200, "end")
     self._update_url_placeholder()

    def _sys_append(self, level: str, text: str):

        _log_to_file(level, text)
        console_hud(level, text)

        if not hasattr(self, "sys_box"):
            return
        box = self.sys_box._textbox  

        prefix = {
            "OK":  "[✔ OK]  ",
            "INFO":"[◉ INFO]  ",
            "WARN":"[! WARN]  ",
            "ERR":"[✖ ERROR]  ",
        }.get(level, "[•]  ")

        color_tag = {
            "OK": "tag_ok",
            "INFO": "tag_info",
            "WARN": "tag_warn",
            "ERR": "tag_err",
        }.get(level, "tag_info")

        box.configure(state="normal")
        box.insert("end", prefix, color_tag)
        box.insert("end", text + "\n", "tag_text")
        box.see("end")
        box.configure(state="disabled")

    def sys_ok(self, text): self._sys_append("OK", text)
    def sys_info(self, text): self._sys_append("INFO", text)
    def sys_warn(self, text): self._sys_append("WARN", text)
    def sys_err(self, text): self._sys_append("ERR", text)

    def build_ui(self):
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True)

        sidebar = ctk.CTkFrame(main, width=240, fg_color="#120000", corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="FluxMedia", font=("Orbitron", 28, "bold"), text_color="#ff3b3b").pack(pady=(30, 0))
        ctk.CTkLabel(sidebar, text="Downloader - [2026]", text_color="gray").pack(pady=(0, 22))
        ctk.CTkFrame(sidebar, height=2, fg_color="#330000").pack(fill="x", padx=18, pady=(0, 16))

        self.platform_buttons = {}
        for name, icon in [("YouTube", "📺"), ("Facebook", "📘"), ("Instagram", "📸"), ("TikTok", "🎵")]:
            btn = ctk.CTkButton(
                sidebar,
                text=f"{icon}  {name}",
                width=200,
                height=50,
                fg_color="#160000",
                hover_color="#160000",
                corner_radius=18,
                border_width=2,
                border_color="#330000",
                anchor="w",
                command=lambda n=name: self.select_platform(n),
            )
            btn.pack(pady=9, padx=18)
            attach_hover(btn, "#160000", "#2a0000", "#330000", "#ff3b3b")
            self.platform_buttons[name] = btn

        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkLabel(sidebar, text=f"Created by {CREATOR_NAME}", text_color="#6b6b6b", font=("Segoe UI", 11)).pack(padx=18, pady=(0, 6), anchor="w")
        ctk.CTkFrame(sidebar, height=2, fg_color="#330000").pack(fill="x", padx=18, pady=(0, 14))

        self.exit_btn = ctk.CTkButton(
            sidebar,
            text="⏻ SALIR",
            width=200,
            height=46,
            fg_color="#2a0000",
            hover_color="#2a0000",
            corner_radius=18,
            border_width=2,
            border_color="#4d0000",
            command=self.on_exit
        )
        self.exit_btn.pack(padx=18, pady=(0, 22))
        attach_hover(self.exit_btn, "#2a0000", "#3a0000", "#4d0000", "#ff3b3b")

        content = ctk.CTkFrame(main)
        content.pack(side="left", fill="both", expand=True, padx=15, pady=15)

        body = ctk.CTkFrame(content)
        body.pack(fill="both", expand=True)

        self.center = ctk.CTkFrame(body, fg_color="#0b0000", corner_radius=18)
        self.center.pack(side="left", fill="both", expand=True, padx=(0, 15))

        header = ctk.CTkFrame(self.center, fg_color="transparent")
        header.pack(fill="x", pady=(18, 6), padx=18)

        self.panel_title_label = ctk.CTkLabel(header, text="YOUTUBE CONTROL PANEL", font=("Orbitron", 18, "bold"), text_color="#ff5c5c")
        self.panel_title_label.pack(side="left")

        right_hdr = ctk.CTkFrame(header, fg_color="transparent")
        right_hdr.pack(side="right")

        self.status_badge = ctk.CTkLabel(right_hdr, text="READY", text_color="#33ff33")
        self.status_badge.pack(side="right", padx=(8, 0))

        self.emergency_btn = ctk.CTkButton(
            right_hdr,
            text="🛑 EMERGENCIA",
            width=170,
            height=34,
            fg_color="#2a0000",
            hover_color="#2a0000",
            corner_radius=14,
            border_width=2,
            border_color="#4d0000",
            state="disabled",
            command=self.emergency_reset
        )
        self.emergency_btn.pack(side="right")
        self.emergency_anim = attach_hover(self.emergency_btn, "#2a0000", "#3a0000", "#4d0000", "#ff3b3b")

        url_block = ctk.CTkFrame(self.center, fg_color="#140000", corner_radius=16)
        url_block.pack(fill="x", padx=18, pady=12)

        self.url_wrap = ctk.CTkFrame(url_block, fg_color="transparent")
        self.url_wrap.pack(padx=14, pady=(14, 10), fill="x")

        self.url_entry = ctk.CTkEntry(
            self.url_wrap,
            width=680,
            height=44,
            text_color="white",
            fg_color="#0e0000",
            border_width=2,
            border_color="#330000",
        )
        self.url_entry.pack(fill="x")

        self.url_placeholder_label = ctk.CTkLabel(self.url_wrap, text="", text_color="#5b5b5b", fg_color="transparent", anchor="w")
        self.url_placeholder_label.place(x=14, y=11)
        self.url_placeholder_label.bind("<Button-1>", lambda e: self.url_entry.focus_set())
        self.url_entry.bind("<KeyRelease>", self._limit_url_200)
        self.url_entry.bind("<FocusIn>", lambda e: self._update_url_placeholder())
        self.url_entry.bind("<FocusOut>", lambda e: self._update_url_placeholder())

        self.fetch_btn = ctk.CTkButton(
            url_block,
            text="🔍 ANALIZAR",
            width=260,
            height=48,
            fg_color="#b30000",
            hover_color="#b30000",
            corner_radius=18,
            border_width=2,
            border_color="#330000",
            command=self.fetch_preview
        )
        self.fetch_btn.pack(pady=(0, 14))
        attach_hover(self.fetch_btn, "#b30000", "#d00000", "#330000", "#ff3b3b")

        settings_row = ctk.CTkFrame(self.center, fg_color="transparent")
        settings_row.pack(fill="x", padx=18, pady=8)

        mode_panel = ctk.CTkFrame(settings_row, fg_color="#140000", corner_radius=16)
        mode_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))

        ctk.CTkLabel(mode_panel, text="MODO", font=("Segoe UI", 13, "bold"), text_color="#ff5c5c").pack(anchor="w", padx=14, pady=(12, 2))

        self.mode_var = ctk.StringVar(value="mp4")
        self.rb_mp4 = ctk.CTkRadioButton(mode_panel, text="MP4 / VIDEO", variable=self.mode_var, value="mp4",
                                         command=self.on_mode_change, text_color="white", text_color_disabled="#ff5c5c")
        self.rb_mp4.pack(anchor="w", padx=16, pady=6)

        self.rb_mp3 = ctk.CTkRadioButton(mode_panel, text="MP3 / AUDIO", variable=self.mode_var, value="mp3",
                                         command=self.on_mode_change, text_color="white", text_color_disabled="#ff5c5c")
        self.rb_mp3.pack(anchor="w", padx=16, pady=(0, 12))

        audio_panel = ctk.CTkFrame(settings_row, fg_color="#140000", corner_radius=16)
        audio_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))

        ctk.CTkLabel(audio_panel, text="🎧 CALIDAD DE AUDIO (MP3)", font=("Segoe UI", 13, "bold"), text_color="#ff5c5c").pack(anchor="w", padx=14, pady=(12, 6))
        self.audio_bitrate_var = ctk.StringVar(value="192 kbps (default)")
        self.audio_menu = ctk.CTkOptionMenu(
            audio_panel,
            values=["128 kbps", "192 kbps (default)", "256 kbps", "320 kbps"],
            variable=self.audio_bitrate_var,
            width=260,
            fg_color="#4d0000",
            button_color="#b30000",
            button_hover_color="#ff1a1a",
            text_color="white",
            text_color_disabled="white"
        )
        self.audio_menu.pack(padx=14, pady=(0, 12), anchor="w")

        video_panel = ctk.CTkFrame(settings_row, fg_color="#140000", corner_radius=16)
        video_panel.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(video_panel, text="🎥 VIDEO SETTINGS (MP4)", font=("Segoe UI", 13, "bold"), text_color="#ff5c5c").pack(anchor="w", padx=14, pady=(12, 6))

        self.fps_row = ctk.CTkFrame(video_panel, fg_color="transparent")
        self.fps_row.pack(fill="x", padx=14, pady=(0, 6))
        ctk.CTkLabel(self.fps_row, text="🎞 FPS preferido", text_color="gray").pack(side="left")
        self.fps_var = ctk.StringVar(value="Automático")
        self.fps_menu = ctk.CTkOptionMenu(
            self.fps_row,
            values=["Automático", "30 FPS", "60 FPS"],
            variable=self.fps_var,
            width=170,
            fg_color="#4d0000",
            button_color="#b30000",
            button_hover_color="#ff1a1a",
            text_color="white",
            text_color_disabled="white"
        )
        self.fps_menu.pack(side="right")

        self.fmt_row = ctk.CTkFrame(video_panel, fg_color="transparent")
        self.fmt_row.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(self.fmt_row, text="📦 Formato de video", text_color="gray").pack(side="left", padx=(0, 20))
        self.container_var = ctk.StringVar(value="MP4 (H.264)")
        self.container_menu = ctk.CTkOptionMenu(
            self.fmt_row,
            values=["MP4 (H.264)", "MKV", "WEBM"],
            variable=self.container_var,
            width=170,
            fg_color="#4d0000",
            button_color="#b30000",
            button_hover_color="#ff1a1a",
            text_color="white",
            text_color_disabled="white"
        )
        self.container_menu.pack(side="right")
        self.container_var.trace_add("write", lambda *_: self.on_container_change())

        quality_panel = ctk.CTkFrame(self.center, fg_color="#140000", corner_radius=16)
        quality_panel.pack(fill="x", padx=18, pady=12)

        topq = ctk.CTkFrame(quality_panel, fg_color="transparent")
        topq.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(topq, text="CALIDAD", font=("Segoe UI", 13, "bold"), text_color="#ff5c5c").pack(side="left")
        ctk.CTkLabel(topq, text="(muestra peso estimado por calidad)", text_color="gray").pack(side="right")

        self.quality_var = ctk.StringVar(value="No hay calidades")
        self.quality_menu = ctk.CTkOptionMenu(
            quality_panel,
            values=["No hay calidades"],
            variable=self.quality_var,
            width=520,
            fg_color="#4d0000",
            button_color="#b30000",
            button_hover_color="#ff1a1a",
            text_color="white",
            text_color_disabled="white"
        )
        self.quality_menu.pack(padx=14, pady=(0, 8), anchor="w")
        self.quality_var.trace_add("write", self.update_quality_size)

        self.quality_size_label = ctk.CTkLabel(quality_panel, text="Peso estimado de la calidad: —", text_color="gray")
        self.quality_size_label.pack(padx=14, pady=(0, 12), anchor="w")

        dl_row = ctk.CTkFrame(self.center, fg_color="transparent")
        dl_row.pack(fill="x", padx=18, pady=(8, 12))

        self.download_btn = ctk.CTkButton(
            dl_row,
            text="⬇ DESCARGAR",
            width=320,
            height=56,
            fg_color="#b30000",
            hover_color="#b30000",
            corner_radius=18,
            border_width=2,
            border_color="#330000",
            state="disabled",
            command=self.start_download
        )
        self.download_btn.pack(side="left")
        attach_hover(self.download_btn, "#b30000", "#d00000", "#330000", "#ff3b3b")

        hud_outer = ctk.CTkFrame(dl_row, fg_color="#330000", corner_radius=18)
        hud_outer.pack(side="left", padx=12, fill="x", expand=True)

        hud_inner = ctk.CTkFrame(hud_outer, fg_color="#120000", corner_radius=16)
        hud_inner.pack(padx=2, pady=2, fill="both", expand=True)

        hud_head = ctk.CTkFrame(hud_inner, fg_color="transparent")
        hud_head.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(hud_head, text="LIVE TRANSFER", font=("Orbitron", 13, "bold"), text_color="#ff5c5c").pack(side="left")
        ctk.CTkLabel(hud_head, text="STREAM HUD", text_color="gray").pack(side="right")

        ctk.CTkFrame(hud_inner, height=2, fg_color="#330000").pack(fill="x", padx=14, pady=(0, 8))

        self.dl_pct_val = self._hud_value_row(hud_inner, "📊 Progreso", "—")
        self.dl_speed_val = self._hud_value_row(hud_inner, "⚡ Velocidad", "—")
        self.dl_time_val = self._hud_value_row(hud_inner, "⏱ Cronómetro", "—")

        sys_outer = ctk.CTkFrame(self.center, fg_color="#330000", corner_radius=18)
        sys_outer.pack(fill="both", expand=False, padx=18, pady=(0, 18))

        sys_inner = ctk.CTkFrame(sys_outer, fg_color="#080000", corner_radius=16)
        sys_inner.pack(padx=2, pady=2, fill="both", expand=True)

        sys_head = ctk.CTkFrame(sys_inner, fg_color="transparent")
        sys_head.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(sys_head, text="SYSTEM HUD", font=("Orbitron", 13, "bold"), text_color="#ff5c5c").pack(side="left")
        ctk.CTkLabel(sys_head, text="LOG STREAM", text_color="gray").pack(side="right")

        ctk.CTkFrame(sys_inner, height=2, fg_color="#330000").pack(fill="x", padx=14, pady=(0, 8))

        self.sys_box = ctk.CTkTextbox(sys_inner, height=110, fg_color="#050000", text_color="white", corner_radius=12)
        self.sys_box.pack(fill="x", padx=14, pady=(0, 12))
        self.sys_box.configure(state="disabled")

        tb = self.sys_box._textbox
        tb.tag_configure("tag_ok", foreground="#33ff33")
        tb.tag_configure("tag_info", foreground="#00d5ff")
        tb.tag_configure("tag_warn", foreground="#ffd34d")
        tb.tag_configure("tag_err", foreground="#ff3b3b")
        tb.tag_configure("tag_text", foreground="#e7e7e7")

        self.hud = ctk.CTkFrame(body, width=480, fg_color="#070000")
        self.hud.pack(side="right", fill="y")
        self.hud.pack_propagate(False)

        card_outer = ctk.CTkFrame(self.hud, fg_color="#330000", corner_radius=20)
        card_outer.pack(pady=(22, 10), padx=18)

        card_mid = ctk.CTkFrame(card_outer, fg_color="#120000", corner_radius=18)
        card_mid.pack(padx=2, pady=2)

        self.thumb_frame = ctk.CTkFrame(card_mid, width=430, height=242, fg_color="#0b0000", corner_radius=16)
        self.thumb_frame.pack(padx=2, pady=2)
        self.thumb_frame.pack_propagate(False)

        self.thumb_label = None
        self.set_thumbnail(None)

        self.title_label = ctk.CTkLabel(self.hud, text="", wraplength=440, justify="center",
                                        font=("Segoe UI", 15, "bold"), text_color="white")
        self.title_label.pack(pady=(8, 6), padx=18)

        ctk.CTkFrame(self.hud, height=2, fg_color="#330000").pack(fill="x", padx=28, pady=10)

        info = ctk.CTkFrame(self.hud, fg_color="#120000", corner_radius=18)
        info.pack(padx=18, pady=10, fill="x")
        ctk.CTkLabel(info, text="MEDIA HUD", font=("Orbitron", 14, "bold"), text_color="#ff5c5c").pack(anchor="w", padx=14, pady=(14, 6))

        self.rows = {}       
        self.row_frames = {}  
        
        for left in ["⏱ Duración", "🎬 Tipo", "🎞 FPS Máx", "🎥 Resolución Máx", "📦 Peso Estimado (máx)", "👤 Creador", "📅 Fecha"]:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=4)
            ctk.CTkLabel(row, text=left, text_color="gray", anchor="w").pack(side="left")
            v = ctk.CTkLabel(row, text="—", text_color="white", anchor="e")
            v.pack(side="right")
            self.rows[left] = v
            self.row_frames[left] = row

    def _hud_value_row(self, parent, left_text, right_text):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(row, text=left_text, text_color="gray", anchor="w").pack(side="left")
        v = ctk.CTkLabel(row, text=right_text, text_color="white", anchor="e")
        v.pack(side="right")
        return v

    def _set_placeholder_text(self, text: str):
        self.url_placeholder_label.configure(text=text)
        self._update_url_placeholder()

    def _update_url_placeholder(self):
        current = self.url_entry.get()
        if current.strip() == "":
            self.url_placeholder_label.place(x=14, y=11)
        else:
            self.url_placeholder_label.place_forget()

    def set_thumbnail(self, pil_img: Image.Image | None):
        try:
            if self.thumb_label is not None and self.thumb_label.winfo_exists():
                self.thumb_label.destroy()
        except:
            pass

        if pil_img is None:
            self.thumb_img = None
            self.thumb_label = ctk.CTkLabel(self.thumb_frame, text="NO SIGNAL", font=("Orbitron", 16, "bold"), text_color="#ff5c5c")
            self.thumb_label.pack(expand=True)
            return

        img = pil_img.resize((430, 242))
        self.thumb_img = ctk.CTkImage(light_image=img, dark_image=img, size=(430, 242))
        self.thumb_label = ctk.CTkLabel(self.thumb_frame, text="", image=self.thumb_img)
        self.thumb_label._img_ref = self.thumb_img
        self.thumb_label.pack(expand=True)

    def start_loading(self, text):
        self.loading = True
        self.loading_text = text
        self.loading_dots = 0
        self._animate_loading()

    def _animate_loading(self):
        if not self.loading:
            return
        dots = "." * (self.loading_dots % 4)
        self.loading_dots += 1
        self.set_status(f"{self.loading_text}{dots}", color="#ff5c5c")
        self.after(350, self._animate_loading)

    def stop_loading(self, final_text, color="#33ff33"):
        self.loading = False
        self.set_status(final_text, color=color)

    def set_status(self, text, color="gray"):
        self.status_badge.configure(text=text, text_color=color)

    def lock_settings(self, locked: bool):

        state = "disabled" if locked else "normal"
        self.rb_mp4.configure(state=state)
        self.rb_mp3.configure(state=state)
        self.audio_menu.configure(state=state)
        self.container_menu.configure(state=state)
        self.fps_menu.configure(state=state)

    def set_sidebar_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in self.platform_buttons.values():
            btn.configure(state=state)

    def set_emergency_enabled(self, enabled: bool):
        self.emergency_btn.configure(state=("normal" if enabled else "disabled"))
        self.emergency_anim.force_reset()

    def apply_platform_profile(self):
        cfg = PLATFORM_CFG.get(self.platform, PLATFORM_CFG["YouTube"])
        
        always = {"⏱ Duración", "🎬 Tipo", "🎥 Resolución Máx", "👤 Creador", "📅 Fecha"}
        
        if cfg.get("supports_fps", False):
            always.add("🎞 FPS Máx")
        
        if cfg.get("supports_weight", False):
            always.add("📦 Peso Estimado (máx)")
        
        for key, frame in self.row_frames.items():
            if key in always:
                if not frame.winfo_ismapped():
                    frame.pack(fill="x", padx=14, pady=4)
            else:
                if frame.winfo_ismapped():
                    frame.pack_forget()

        self._set_placeholder_text(cfg.get("placeholder", "🔗 Pega el link del video"))

        if cfg["supports_fps"]:
            if not self.fps_row.winfo_ismapped():
                self.fps_row.pack_forget()
                self.fps_row.pack(before=self.fmt_row, fill="x", padx=14, pady=(0, 6))
        else:
            if self.fps_row.winfo_ismapped():
                self.fps_row.pack_forget()

        if self.platform == "YouTube":
            self.quality_menu.configure(state=("normal" if self.is_prepared else "disabled"))
        else:
            self.quality_menu.configure(state="disabled")
            self.quality_var.set("No hay calidades")
            self.quality_menu.configure(values=["No hay calidades"])

    def highlight_platform(self, name):
        for p, btn in self.platform_buttons.items():
            btn.configure(fg_color="#160000", border_color="#330000")
        self.platform_buttons[name].configure(fg_color="#b30000", border_color="#ff3b3b")

    def select_platform(self, name):
        if self.platform_buttons.get(name) and str(self.platform_buttons[name].cget("state")) == "disabled":
            return
        self.platform = name
        self.highlight_platform(name)
        self.panel_title_label.configure(text=PLATFORM_CFG[name]["panel_title"])
        self.url_entry.delete(0, "end")
        self._update_url_placeholder()
        self.set_status("READY", color="#33ff33")
        self.reset_ui(full=False)
        self.apply_platform_profile()



    def reset_ui(self, full=False):
        self.info_cache = None
        self.is_prepared = False
        self.prepared_platform = None
        self.yt_quality_profiles = None
        self.cancel_requested = False
        self.download_started_at = None

        if full:
            self.url_entry.delete(0, "end")
            self._update_url_placeholder()

        self.set_thumbnail(None)
        self.title_label.configure(text="")

        for k in self.rows:
            self.rows[k].configure(text="—")

        self.quality_menu.configure(values=["No hay calidades"])
        self.quality_var.set("No hay calidades")
        self.quality_size_label.configure(text="Peso estimado de la calidad: —")

        self.dl_pct_val.configure(text="—")
        self.dl_speed_val.configure(text="—")
        self.dl_time_val.configure(text="—")

        self.download_btn.configure(state="disabled")
        self.fetch_btn.configure(state="normal")

        self.lock_settings(True)

        self.set_sidebar_enabled(True)
        self.set_emergency_enabled(False)

    def on_mode_change(self):
        mode = self.mode_var.get()
        cfg = PLATFORM_CFG.get(self.platform, PLATFORM_CFG["YouTube"])

        if mode == "mp3":
            self.quality_menu.configure(state="disabled")
            self.fps_menu.configure(state="disabled")
            self.container_menu.configure(state="disabled")
            self.audio_menu.configure(state="normal")
        else:
            self.container_menu.configure(state="normal")
            self.audio_menu.configure(state="disabled")
            self.fps_menu.configure(state=("normal" if cfg.get("supports_fps", False) else "disabled"))
            if self.platform == "YouTube" and self.is_prepared:
                self.quality_menu.configure(state="normal")
                self.refresh_youtube_quality_menu()

        if self.is_prepared:
            self.download_btn.configure(state="normal")

    def on_container_change(self):
        if self.platform == "YouTube" and self.is_prepared and self.mode_var.get() == "mp4":
            self.refresh_youtube_quality_menu()

    def update_quality_size(self, *args):
        val = self.quality_var.get()
        if "|" in val:
            right = val.split("|", 1)[1].strip()
            self.quality_size_label.configure(text=f"Peso estimado de la calidad: {right.replace('~', '').strip()}")
        else:
            self.quality_size_label.configure(text="Peso estimado de la calidad: —")

    def refresh_youtube_quality_menu(self):
        if not self.yt_quality_profiles:
            return
        if self.mode_var.get() != "mp4":
            return

        cont = self.container_var.get()
        if cont.startswith("MP4"):
            heights = self.yt_quality_profiles.get("mp4", [])
            sizes = self.yt_quality_profiles.get("sizes_mp4", {})
        elif cont == "WEBM":
            heights = self.yt_quality_profiles.get("webm", [])
            sizes = self.yt_quality_profiles.get("sizes_webm", {})
        else:
            heights = self.yt_quality_profiles.get("any", [])
            sizes = self.yt_quality_profiles.get("sizes_any", {})

        if not heights:
            self.quality_menu.configure(values=["No disponible"])
            self.quality_var.set("No disponible")
            self.download_btn.configure(state="disabled")
            return

        values = [f"{h}  |  ~{sizes.get(h, '—')}" for h in heights]
        self.quality_menu.configure(values=values)
        self.quality_var.set(values[0])
        self.download_btn.configure(state="normal")

    def fetch_preview(self):
        raw = self.url_entry.get().strip()
        url = canonical_url(raw)
        if not url:
            messagebox.showwarning("Aviso", "Ingresa un link válido")
            return

        if not url_matches_platform(url, self.platform):
            allowed = ", ".join(sorted(PLATFORM_DOMAINS[self.platform]))
            messagebox.showerror("Link incorrecto", f"Este link NO corresponde a: {self.platform}\n\nDominios: {allowed}")
            self.sys_warn(f"Link inválido para {self.platform}: {url}")
            return

        cache_key = f"{self.platform}|{url}"
        if cache_key in self.analysis_cache:
            self.set_sidebar_enabled(False)
            self.set_emergency_enabled(True)
            self.fetch_btn.configure(state="disabled")
            self.download_btn.configure(state="disabled")
            self.lock_settings(True)

            self.start_loading("CARGANDO CACHE")
            self.analyze_token += 1
            token = self.analyze_token

            def apply_cached():
                if token != self.analyze_token:
                    return
                self._apply_analyze_result(url, self.platform, self.analysis_cache[cache_key], from_cache=True)

            self.after(150, apply_cached)
            return

        self.set_sidebar_enabled(False)
        self.set_emergency_enabled(True)
        self.cancel_requested = False

        self.analyze_token += 1
        token = self.analyze_token

        self.fetch_btn.configure(state="disabled")
        self.download_btn.configure(state="disabled")
        self.lock_settings(True)

        self.start_loading("ANALIZANDO")
        self.sys_info(f"Analizando: {self.platform} | {url}")

        threading.Thread(target=self._analyze_thread, args=(url, token, self.platform), daemon=True).start()

    def _analyze_thread(self, url: str, token: int, platform_snapshot: str):
        try:
            cookiefile = get_cookiefile_for_platform(platform_snapshot)
            ydl_opts = {
                "quiet": True,
                "cookiefile": cookiefile,
                "http_headers": base_http_headers(),
                "retries": 3,
                "extractor_retries": 3,
                "socket_timeout": 15,
                "noplaylist": True,
                "cachedir": False,
                "no_warnings": True,
                "logger": YTDLPLogger(self),
                "noprogress": True,
                "progress_with_newline": False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            formats = info.get("formats", [])
            heights_all = [f.get("height") for f in formats if f.get("height")]
            max_height = max(heights_all) if heights_all else None

            fps_list = [f.get("fps") for f in formats if f.get("fps")]
            max_fps = max(fps_list) if fps_list else None

            sizes_all = [f.get("filesize_approx") for f in formats if f.get("filesize_approx")]
            max_size_any = max(sizes_all) if sizes_all else None

            thumb_url = info.get("thumbnail")
            thumb_img = load_image_from_url(thumb_url) if thumb_url else None

            yt_profiles = None
            if platform_snapshot == "YouTube":
                mp4_heights = set()
                webm_heights = set()
                any_heights = set()
                sizes_mp4, sizes_webm, sizes_any = {}, {}, {}

                for f in formats:
                    if f.get("vcodec") == "none":
                        continue
                    h = f.get("height")
                    if not h:
                        continue
                    tag = f"{h}p"
                    any_heights.add(tag)
                    if f.get("filesize_approx"):
                        sizes_any[tag] = fmt_size(f.get("filesize_approx"))

                    ext = (f.get("ext") or "").lower()
                    vcodec = (f.get("vcodec") or "").lower()

                    if ext == "mp4" and vcodec.startswith("avc1"):
                        mp4_heights.add(tag)
                        if f.get("filesize_approx"):
                            sizes_mp4[tag] = fmt_size(f.get("filesize_approx"))
                    if ext == "webm":
                        webm_heights.add(tag)
                        if f.get("filesize_approx"):
                            sizes_webm[tag] = fmt_size(f.get("filesize_approx"))

                yt_profiles = {
                    "mp4": sorted(mp4_heights, key=lambda x: int(x[:-1]), reverse=True),
                    "webm": sorted(webm_heights, key=lambda x: int(x[:-1]), reverse=True),
                    "any": sorted(any_heights, key=lambda x: int(x[:-1]), reverse=True),
                    "sizes_mp4": sizes_mp4,
                    "sizes_webm": sizes_webm,
                    "sizes_any": sizes_any,
                }

            data = {
                "info": info,
                "thumb_img": thumb_img,
                "max_height": max_height,
                "max_fps": max_fps,
                "max_size_any": max_size_any,
                "yt_profiles": yt_profiles,
            }

            self.analysis_cache[f"{platform_snapshot}|{url}"] = data
            safe_ui(self, self._apply_analyze_result, url, platform_snapshot, data, False)

        except Exception as e:
            err = strip_ansi(str(e))

            if platform_snapshot in {"Facebook", "Instagram", "TikTok"}:
                cookie_hint = os.path.join(BASE_DIR, "cookies", f"{platform_snapshot.lower()}.txt")
                err = (
                    f"{platform_snapshot} no pudo extraer datos.\n\n"
                    "✅ Solución:\n"
                    f"1) Usa cookies si es privado/restringido:\n{cookie_hint}\n\n"
                    "Error técnico:\n" + str(e)
                )

            def fail(err=err):
                self.stop_loading("ERROR", color="red")
                messagebox.showerror("Error", err)
                self.sys_err(f"ERROR al analizar ({platform_snapshot}).")
                self.reset_ui(full=False)
                self.apply_platform_profile()
                self.set_status("READY", color="#33ff33")

            safe_ui(self, fail)

    def _apply_analyze_result(self, url: str, platform_snapshot: str, data: dict, from_cache: bool = False):
        info = data.get("info") or {}
        cfg = PLATFORM_CFG.get(platform_snapshot, PLATFORM_CFG["YouTube"])

        self.prepared_platform = platform_snapshot
        self.info_cache = info
        self.yt_quality_profiles = data.get("yt_profiles")

        self.set_thumbnail(data.get("thumb_img"))
        self.title_label.configure(text=display_title_short(info.get("title", "—")))

        dur = info.get("duration")
        self.rows["⏱ Duración"].configure(text=fmt_duration(dur))
        self.rows["🎬 Tipo"].configure(text=content_type(dur))
        self.rows["👤 Creador"].configure(text=info.get("uploader", "—"))
        self.rows["📅 Fecha"].configure(text=fmt_date(info.get("upload_date")))
        self.rows["🎥 Resolución Máx"].configure(text=f"{data.get('max_height')}p" if data.get("max_height") else "—")

        if cfg.get("supports_fps", False):
            self.rows["🎞 FPS Máx"].configure(text=f"{data.get('max_fps')} FPS" if data.get("max_fps") else "—")
        else:
            self.rows["🎞 FPS Máx"].configure(text="—")

        if cfg.get("supports_weight", False):
            self.rows["📦 Peso Estimado (máx)"].configure(text=fmt_size(data.get("max_size_any")) if data.get("max_size_any") else "—")
        else:
            self.rows["📦 Peso Estimado (máx)"].configure(text="—")

        self.is_prepared = True
        self.stop_loading("LISTO ✔" + (" (cache)" if from_cache else ""), color="#33ff33")

        self.lock_settings(False)

        self.set_sidebar_enabled(False)
        self.set_emergency_enabled(True)

        self.apply_platform_profile()
        self.on_mode_change()

        if platform_snapshot == "YouTube":
            self.refresh_youtube_quality_menu()

        self.download_btn.configure(state="normal")
        self.fetch_btn.configure(state="disabled") 
        self.sys_ok(f"Listo: {platform_snapshot} • Video cargado")

    def start_download(self):
        raw = self.url_entry.get().strip()
        url = canonical_url(raw)
        if not url:
            messagebox.showwarning("Aviso", "Ingresa un link válido")
            return

        if not url_matches_platform(url, self.platform):
            allowed = ", ".join(sorted(PLATFORM_DOMAINS[self.platform]))
            messagebox.showerror("Link incorrecto", f"Este link NO corresponde a: {self.platform}\n\nDominios: {allowed}")
            return

        if not self.info_cache or not self.is_prepared or not self.prepared_platform:
            messagebox.showwarning("Aviso", "Primero presiona ANALIZAR.")
            return

        if self.platform != self.prepared_platform:
            messagebox.showwarning("Aviso", "Cambiaste de plataforma después de analizar.\n\nPresiona EMERGENCIA.")
            return

        self.cancel_requested = False
        self.download_started_at = time.time()
        self.download_token += 1
        token = self.download_token

        self.lock_settings(True)
        self.download_btn.configure(state="disabled")

        self.start_loading("DESCARGANDO")
        self.sys_info(f"Descarga iniciada: {self.prepared_platform}")

        threading.Thread(target=self._download_thread, args=(url, token, self.prepared_platform), daemon=True).start()

    def _progress_hook_factory(self, token: int):
        def hook(d):
            if self.cancel_requested or token != self.download_token:
                raise CancelledByUser("Cancelado por emergencia.")
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes")
                speed_bps = d.get("speed")

                pct = f"{(downloaded / total) * 100:.1f}%" if total and downloaded is not None else "—"
                speed = f"{(speed_bps / 1024 / 1024):.2f} MB/s" if speed_bps else "—"
                clk = fmt_clock(time.time() - self.download_started_at) if self.download_started_at else "—"

                safe_ui(self, lambda: self._update_dl_hud(pct, speed, clk))

            elif d.get("status") == "finished":
                clk = fmt_clock(time.time() - self.download_started_at) if self.download_started_at else "—"
                safe_ui(self, lambda: self._update_dl_hud("100%", "—", clk))
        return hook

    def _update_dl_hud(self, pct, speed, clk):
        self.dl_pct_val.configure(text=pct)
        self.dl_speed_val.configure(text=speed)
        self.dl_time_val.configure(text=clk)

    def _download_thread(self, url: str, token: int, platform_snapshot: str):
        try:
            hook = self._progress_hook_factory(token)

            cfg = PLATFORM_CFG.get(platform_snapshot)
            mp4_folder = cfg["mp4_folder"]
            mp3_folder = cfg["mp3_folder"]
            prefix = cfg["file_prefix"]
            cookiefile = get_cookiefile_for_platform(platform_snapshot)

            mode = self.mode_var.get()

            if mode == "mp3":
                br = self.audio_bitrate_var.get()
                br_num = "192"
                if "128" in br: br_num = "128"
                elif "256" in br: br_num = "256"
                elif "320" in br: br_num = "320"

                n = next_available_index(mp3_folder, prefix)
                outtmpl = os.path.join(mp3_folder, f"{prefix} - ({n}).%(ext)s")

                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": outtmpl,
                    "ffmpeg_location": FFMPEG_EXE,
                    "progress_hooks": [hook],
                    "cookiefile": cookiefile,
                    "http_headers": base_http_headers(),
                    "retries": 3,
                    "extractor_retries": 3,
                    "socket_timeout": 15,
                    "noplaylist": True,
                    "cachedir": False,
                    "quiet": True,
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": br_num,
                    }]
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

            else:
                container = self.container_var.get()

                height = None
                if platform_snapshot == "YouTube":
                    q = self.quality_var.get().split("|", 1)[0].strip()
                    if q.endswith("p"):
                        height = int(q[:-1])

                if platform_snapshot == "YouTube":
                    if container.startswith("MP4"):
                        fmt = f"bestvideo[height={height}][ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best" if height else \
                              "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                        merge_format = "mp4"
                    elif container == "WEBM":
                        fmt = f"bestvideo[height={height}][ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best" if height else \
                              "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best"
                        merge_format = "webm"
                    else:
                        fmt = f"bestvideo[height={height}]+bestaudio/best" if height else "bestvideo+bestaudio/best"
                        merge_format = "mkv"
                else:
                    if container.startswith("MP4"):
                        fmt = "best[ext=mp4]/best"
                        merge_format = "mp4"
                    elif container == "WEBM":
                        fmt = "best[ext=webm]/best"
                        merge_format = "webm"
                    else:
                        fmt = "best"
                        merge_format = "mkv"

                n = next_available_index(mp4_folder, prefix)
                outtmpl = os.path.join(mp4_folder, f"{prefix} - ({n}).%(ext)s")

                ydl_opts = {
                    "format": fmt,
                    "outtmpl": outtmpl,
                    "ffmpeg_location": FFMPEG_EXE,
                    "progress_hooks": [hook],
                    "cookiefile": cookiefile,
                    "http_headers": base_http_headers(),
                    "retries": 3,
                    "extractor_retries": 3,
                    "socket_timeout": 15,
                    "noplaylist": True,
                    "cachedir": False,
                    "quiet": True,
                    "merge_output_format": merge_format,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

            def done():
                if token != self.download_token:
                    return
                self.stop_loading("COMPLETADO ✔", color="#33ff33")
                messagebox.showinfo("Listo", "Descarga completada ✔\n\nListo para descargar otro.")
                self.sys_ok("Descarga completada.")
                self.reset_ui(full=True)
                self.apply_platform_profile()
                self.set_status("READY", color="#33ff33")

            safe_ui(self, done)

        except Exception as e:
            err = strip_ansi(str(e))
            if platform_snapshot in {"Facebook", "Instagram", "TikTok"}:
                cookie_hint = os.path.join(BASE_DIR, "cookies", f"{platform_snapshot.lower()}.txt")
                err = (
                    f"{platform_snapshot} no pudo descargar.\n\n"
                    "✅ Solución:\n"
                    f"1) Usa cookies si es privado/restringido:\n{cookie_hint}\n\n"
                    "Error técnico:\n" + str(e)
                )

            def fail(err=err):
                if token != self.download_token:
                    return
                self.stop_loading("ERROR", color="red")
                messagebox.showerror("Error", err)
                self.sys_err("ERROR en descarga.")
                self.reset_ui(full=False)
                self.apply_platform_profile()
                self.set_status("READY", color="#33ff33")

            safe_ui(self, fail)

    def emergency_reset(self):
        self.cancel_requested = True
        self.analyze_token += 1
        self.download_token += 1
        self.loading = False
        self.set_status("RESET...", color="orange")
        self.sys_warn("Reset por emergencia.")
        self.reset_ui(full=True)
        self.apply_platform_profile()
        self.set_status("READY", color="#33ff33")

    def on_exit(self):
        if self.emergency_btn.cget("state") == "normal":
            ok = messagebox.askyesno("Salir", "Hay un proceso en curso.\n\n¿Deseas salir igual?")
            if not ok:
                return
        self.sys_warn("Programa cerrado por el usuario.")
        self.destroy()

if __name__ == "__main__":

    try:
        import sys, io
        sys.stderr = io.StringIO()
    except:
        pass

    try:
        colorama_init(autoreset=True)
    except:
        pass

    def console_banner():
        try:
            if os.name == "nt":
                os.system("cls")
            else:
                os.system("clear")
        except:
            pass

        print("\x1b[31m" + "═" * 64 + "\x1b[0m")
        print("\x1b[31m" + "   FluxMedia v2.1  •  Console HUD  •  SYSTEM ONLINE" + "\x1b[0m")
        print("\x1b[31m" + "═" * 64 + "\x1b[0m")

    console_banner()

    set_console_title("FluxMedia v2.1")

    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FluxMedia.v2.1")
        except:
            pass

    if not os.path.exists(FFMPEG_EXE):
        messagebox.showerror(
            "FFmpeg no encontrado",
            f"No se encontró ffmpeg.exe en:\n{FFMPEG_EXE}\n\n"
            f"Colócalo en:\n{os.path.join(BASE_DIR, 'FG - [1]')}"
        )
        _log_to_file("ERR", f"FFmpeg NO encontrado: {FFMPEG_EXE}")
        raise SystemExit

    app = FluxMediaApp()
    app.title("FluxMedia v2.1")
    app.mainloop()