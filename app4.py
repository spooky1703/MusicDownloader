"""
soundcloud_downloader_improved.py
Descargador GUI mejorado con yt-dlp - Versión optimizada final - CORREGIDO
"""

import os
import sys
import threading
import queue
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp

# ---------------------------
# Configuration & Constants
# ---------------------------
class Config:
    DEFAULT_BITRATE = "192"
    SUPPORTED_FORMATS = ["mp3", "m4a", "flac", "wav"]
    BITRATE_OPTIONS = ["320", "256", "192", "128", "96"]
    DEFAULT_OUT_TEMPLATE = "%(artist)s - %(title).200s.%(ext)s"
    FALLBACK_TEMPLATE = "%(uploader)s - %(title).200s.%(ext)s"
    CONFIG_FILE = "downloader_config.json"
    LOG_FILE = "downloader.log"
    MAX_LOG_SIZE = 1024 * 1024  # 1MB

# ---------------------------
# Logging Setup
# ---------------------------
def setup_logging():
    """Configure logging with rotation"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# ---------------------------
# Configuration Manager
# ---------------------------
class ConfigManager:
    def __init__(self):
        self.config_path = Path(Config.CONFIG_FILE)
        self.default_config = {
            "output_dir": str(Path.home() / "Downloads"),
            "bitrate": Config.DEFAULT_BITRATE,
            "format": "mp3",
            "template": Config.DEFAULT_OUT_TEMPLATE,
            "create_artist_folders": False,
            "skip_existing": True,
            "max_concurrent": 3,
            "save_cover_art": True,
            "cover_format": "jpg",
            "cover_size": "original"
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults for missing keys
                    return {**self.default_config, **config}
        except Exception as e:
            logging.warning(f"Failed to load config: {e}")
        return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

# ---------------------------
# Enhanced Downloader Thread
# ---------------------------
class DownloaderThread(threading.Thread):
    def __init__(self, url: str, config: Dict[str, Any], progress_queue: queue.Queue, 
                 stop_event: threading.Event, logger: logging.Logger):
        super().__init__(daemon=True)
        self.url = url
        self.config = config
        self.progress_queue = progress_queue
        self.stop_event = stop_event
        self.logger = logger
        self.download_info = {}
        
    def run(self):
        try:
            self._download()
        except Exception as e:
            if self.stop_event.is_set():
                self.progress_queue.put(("canceled", "Descarga cancelada por usuario"))
            else:
                self.logger.error(f"Download error: {e}")
                self.progress_queue.put(("error", f"Error: {str(e)}"))

    def _download(self):
        """Main download logic with enhanced options"""
        output_dir = Path(self.config['output_dir'])
        
        # Create artist subfolder if enabled
        if self.config.get('create_artist_folders', False):
            try:
                # First, extract info to get artist name
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                    info = ydl.extract_info(self.url, download=False)
                    artist = info.get('artist') or info.get('uploader') or 'Unknown'
                    output_dir = output_dir / self._sanitize_filename(artist)
            except Exception:
                pass  # Continue with original output_dir
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build output template
        template = self.config.get('template', Config.DEFAULT_OUT_TEMPLATE)
        outtmpl = str(output_dir / template)
        
        # Enhanced yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self._progress_hook],
            'extract_flat': False,
            'writethumbnail': True,  # Download thumbnail
            'writeinfojson': False,  # Skip JSON metadata
            'embedthumbnail': True,  # Embed thumbnail in audio
            'restrictfilenames': False,
            'nocheckcertificate': True,
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'skip_download': False,
        }
        
        # Skip if file exists
        if self.config.get('skip_existing', True):
            ydl_opts['overwrites'] = False
        
        # Audio postprocessing
        audio_format = self.config.get('format', 'mp3')
        bitrate = self.config.get('bitrate', Config.DEFAULT_BITRATE)
        
        postprocessors = []
        
        if audio_format in ['mp3', 'm4a']:
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': bitrate,
            })
        
        # Add metadata
        postprocessors.append({
            'key': 'FFmpegMetadata',
            'add_metadata': True,
        })
        
        # Embed thumbnail in audio file
        if audio_format == 'mp3':
            postprocessors.append({
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False,
            })
        
        ydl_opts['postprocessors'] = postprocessors
        
        self.progress_queue.put(("status", "Extrayendo información..."))
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(self.url, download=False)
            self.download_info = {
                'ALONSO AGRADECE CADA DESCARGA'
                'title': info.get('title', 'Unknown'),
                'artist': info.get('artist') or info.get('uploader', 'Unknown'),
                'duration': info.get('duration'),
                'description': info.get('description', ''),
                'webpage_url': info.get('webpage_url', self.url)
            }
            
            self.progress_queue.put(("info", self.download_info))
            self.progress_queue.put(("status", "Iniciando descarga..."))
            
            # Download
            ydl.download([self.url])
            
            if not self.stop_event.is_set():
                self.progress_queue.put(("complete", "Descarga completada exitosamente"))

    def _progress_hook(self, d):
        """Enhanced progress hook with better error handling"""
        if self.stop_event.is_set():
            raise yt_dlp.DownloadError("User cancelled")
        
        status = d.get('status')
        
        if status == 'downloading':
            self._handle_download_progress(d)
        elif status == 'finished':
            filename = Path(d.get('filename', '')).name
            self.progress_queue.put(("status", f"Descarga finalizada: {filename}"))
            self.progress_queue.put(("status", "Procesando audio..."))
        elif status == 'error':
            error_msg = d.get('error', 'Unknown error')
            self.progress_queue.put(("error", f"Error en descarga: {error_msg}"))

    def _handle_download_progress(self, d):
        """Handle download progress with detailed information"""
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        speed = d.get('speed', 0)
        eta = d.get('eta', 0)
        filename = Path(d.get('filename', '')).name
        
        percent = None
        if total > 0:
            percent = min(100.0, (downloaded / total) * 100.0)
        
        progress_info = {
            'percent': percent,
            'downloaded': downloaded,
            'total': total,
            'speed': speed,
            'eta': eta,
            'filename': filename
        }
        
        self.progress_queue.put(("progress", progress_info))

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        return filename.strip()

# ---------------------------
# Enhanced GUI Application
# ---------------------------
class EnhancedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced SoundCloud Downloader (yt-dlp)")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Initialize components
        self.logger = setup_logging()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # Variables
        self.url_var = tk.StringVar()
        self.outdir_var = tk.StringVar(value=self.config['output_dir'])
        self.bitrate_var = tk.StringVar(value=self.config['bitrate'])
        self.format_var = tk.StringVar(value=self.config['format'])
        self.artist_folder_var = tk.BooleanVar(value=self.config['create_artist_folders'])
        self.skip_existing_var = tk.BooleanVar(value=self.config['skip_existing'])
        self.save_cover_var = tk.BooleanVar(value=self.config['save_cover_art'])
        self.cover_format_var = tk.StringVar(value=self.config['cover_format'])
        
        # Queues and threading
        self.progress_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker = None
        self.download_info = {}
        
        self._build_enhanced_ui()
        self._periodic_check()
        
        # Bind cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_enhanced_ui(self):
        """Build enhanced UI with more options"""
        # Configure style for better appearance (using only available styles)
        style = ttk.Style()
        
        # Main container with notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Download tab
        self.download_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.download_frame, text="Descarga")
        
        # Settings tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Configuracion")
        
        # Info tab
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="Acerca de")
        
        self._build_download_tab()
        self._build_settings_tab()
        self._build_info_tab()
        
    def _build_download_tab(self):
        """Build the main download interface"""
        frame = self.download_frame
        
        # URL section with improved styling
        url_frame = ttk.LabelFrame(frame, text="URL de Audio", padding=15)
        url_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # URL input with paste button in same row
        url_input_frame = ttk.Frame(url_frame)
        url_input_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.url_entry = ttk.Entry(url_input_frame, textvariable=self.url_var, font=('Consolas', 10))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.url_entry.focus()
        
        ttk.Button(url_input_frame, text="Pegar", 
                  command=self._paste_from_clipboard, width=8).pack(side=tk.RIGHT)
        
        # Quick format selection
        format_quick_frame = ttk.Frame(url_frame)
        format_quick_frame.pack(fill=tk.X)
        
        ttk.Label(format_quick_frame, text="Formato:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Combobox(format_quick_frame, textvariable=self.format_var, values=Config.SUPPORTED_FORMATS, 
                    width=8, state="readonly").pack(side=tk.LEFT, padx=(8, 20))
        
        ttk.Label(format_quick_frame, text="Calidad:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Combobox(format_quick_frame, textvariable=self.bitrate_var, values=Config.BITRATE_OPTIONS, 
                    width=8, state="readonly").pack(side=tk.LEFT, padx=(8, 0))
        
        # Output section with better organization
        output_frame = ttk.LabelFrame(frame, text="Configuracion de Descarga", padding=15)
        output_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Directory selection
        dir_frame = ttk.Frame(output_frame)
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dir_frame, text="Carpeta de salida:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        dir_input_frame = ttk.Frame(dir_frame)
        dir_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Entry(dir_input_frame, textvariable=self.outdir_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(dir_input_frame, text="Explorar", command=self._choose_outdir, width=12).pack(side=tk.RIGHT)
        
        # Download options with checkboxes
        options_frame = ttk.Frame(output_frame)
        options_frame.pack(fill=tk.X)
        
        left_options = ttk.Frame(options_frame)
        left_options.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Checkbutton(left_options, text="Crear carpetas por artista", 
                       variable=self.artist_folder_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(left_options, text="Omitir archivos existentes", 
                       variable=self.skip_existing_var).pack(anchor=tk.W, pady=2)
        
        right_options = ttk.Frame(options_frame)
        right_options.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        ttk.Checkbutton(right_options, text="Guardar caratula separada", 
                       variable=self.save_cover_var).pack(anchor=tk.W, pady=2)
        
        cover_format_frame = ttk.Frame(right_options)
        cover_format_frame.pack(anchor=tk.W, pady=2)
        ttk.Label(cover_format_frame, text="Formato caratula:").pack(side=tk.LEFT)
        ttk.Combobox(cover_format_frame, textvariable=self.cover_format_var, 
                    values=["jpg", "png"], width=6, state="readonly").pack(side=tk.LEFT, padx=(5, 0))
        
        # Control buttons with icons
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=10, pady=15)
        
        self.btn_download = ttk.Button(control_frame, text="Descargar", command=self._on_download)
        self.btn_download.pack(side=tk.LEFT, padx=(0, 15))
        
        self.btn_cancel = ttk.Button(control_frame, text="Cancelar", command=self._on_cancel, state=tk.DISABLED)
        self.btn_cancel.pack(side=tk.LEFT)
        
        # Quick actions
        ttk.Button(control_frame, text="Abrir carpeta", 
                  command=self._open_output_folder).pack(side=tk.RIGHT, padx=(15, 0))
        ttk.Button(control_frame, text="Limpiar log", 
                  command=self._clear_log).pack(side=tk.RIGHT)
        
        # Info section with better styling
        info_frame = ttk.LabelFrame(frame, text="Informacion del Track", padding=15)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.info_text = tk.Text(info_frame, height=3, wrap='word', state=tk.DISABLED, 
                               font=('Arial', 9), relief=tk.FLAT, borderwidth=0)
        self.info_text.pack(fill=tk.X)
        
        # Progress section enhanced
        progress_frame = ttk.LabelFrame(frame, text="Progreso de Descarga", padding=15)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Progress bar with percentage label
        progress_container = ttk.Frame(progress_frame)
        progress_container.pack(fill=tk.X, pady=(0, 8))
        
        self.progress = ttk.Progressbar(progress_container, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.progress_label = ttk.Label(progress_container, text="0%", width=6)
        self.progress_label.pack(side=tk.RIGHT)
        
        self.lbl_status = ttk.Label(progress_frame, text="Listo para descargar", font=('Arial', 9))
        self.lbl_status.pack(anchor=tk.W, pady=(0, 8))
        
        # Enhanced log with scrollbar
        log_container = ttk.Frame(progress_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.txt_log = tk.Text(log_container, wrap='word', state=tk.DISABLED, font=('Consolas', 8),
                              bg='#f8f9fa', fg='#495057')
        scrollbar = ttk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=scrollbar.set)
        
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_settings_tab(self):
        """Build enhanced settings tab"""
        frame = self.settings_frame
        
        # Audio settings
        audio_frame = ttk.LabelFrame(frame, text="Configuracion de Audio", padding=15)
        audio_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Default format and quality
        defaults_frame = ttk.Frame(audio_frame)
        defaults_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(defaults_frame, text="Formato por defecto:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Combobox(defaults_frame, textvariable=self.format_var, values=Config.SUPPORTED_FORMATS, 
                    width=10, state="readonly").pack(side=tk.LEFT, padx=(10, 30))
        
        ttk.Label(defaults_frame, text="Calidad por defecto:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Combobox(defaults_frame, textvariable=self.bitrate_var, values=Config.BITRATE_OPTIONS, 
                    width=10, state="readonly").pack(side=tk.LEFT, padx=(10, 0))
        
        # File organization
        org_frame = ttk.LabelFrame(frame, text="Organizacion de Archivos", padding=15)
        org_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(org_frame, text="Crear carpetas por artista automaticamente", 
                       variable=self.artist_folder_var).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(org_frame, text="Omitir archivos que ya existen", 
                       variable=self.skip_existing_var).pack(anchor=tk.W, pady=3)
        
        # Cover art settings
        cover_frame = ttk.LabelFrame(frame, text="Configuracion de Caratulas", padding=15)
        cover_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(cover_frame, text="Guardar caratula como archivo separado", 
                       variable=self.save_cover_var).pack(anchor=tk.W, pady=3)
        
        cover_options_frame = ttk.Frame(cover_frame)
        cover_options_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(cover_options_frame, text="Formato de caratula:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Combobox(cover_options_frame, textvariable=self.cover_format_var, 
                    values=["jpg", "png", "webp"], width=8, state="readonly").pack(side=tk.LEFT, padx=(10, 0))
        
        # Action buttons
        action_frame = ttk.Frame(frame)
        action_frame.pack(fill=tk.X, padx=10, pady=20)
        
        ttk.Button(action_frame, text="Guardar configuracion", 
                  command=self._save_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="Restaurar valores por defecto", 
                  command=self._reset_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="Abrir carpeta de configuracion", 
                  command=self._open_config_folder).pack(side=tk.LEFT)

    def _build_info_tab(self):
        """Build info/about tab"""
        frame = self.info_frame
        
        # Title
        title_frame = ttk.Frame(frame)
        title_frame.pack(pady=20)
        
        title_label = ttk.Label(title_frame, text="Enhanced SoundCloud Downloader", 
                               font=('Arial', 16, 'bold'))
        title_label.pack()
        
        version_label = ttk.Label(title_frame, text="Version 2.0 - Mejorado con yt-dlp", 
                                 font=('Arial', 10))
        version_label.pack(pady=5)
        
        # Features
        features_frame = ttk.LabelFrame(frame, text="Caracteristicas", padding=15)
        features_frame.pack(fill=tk.X, padx=20, pady=10)
        
        features_text = """• Descarga de audio de alta calidad desde múltiples plataformas
• Soporte para MP3, M4A, FLAC y WAV
• Descarga automática de carátulas y metadatos
• Organización inteligente por artistas
• Interfaz moderna e intuitiva
• Configuración persistente
• Progreso detallado en tiempo real"""
        
        features_label = tk.Text(features_frame, wrap='word', height=8, state=tk.DISABLED,
                               font=('Arial', 10), bg='#f0f0f0', relief=tk.FLAT)
        features_label.insert('1.0', features_text)
        features_label.pack(fill=tk.X)
        
        # Requirements
        req_frame = ttk.LabelFrame(frame, text="Requisitos", padding=15)
        req_frame.pack(fill=tk.X, padx=20, pady=10)
        
        req_text = """• Python 3.7+
• yt-dlp (pip install yt-dlp)
• FFmpeg (para conversión de audio)
• tkinter (incluido con Python)"""
        
        req_label = tk.Text(req_frame, wrap='word', height=5, state=tk.DISABLED,
                          font=('Arial', 10), bg='#f0f0f0', relief=tk.FLAT)
        req_label.insert('1.0', req_text)
        req_label.pack(fill=tk.X)

    def _paste_from_clipboard(self):
        """Paste URL from clipboard"""
        try:
            clipboard_content = self.root.clipboard_get()
            if clipboard_content and ('http' in clipboard_content.lower()):
                self.url_var.set(clipboard_content.strip())
        except Exception:
            pass

    def _choose_outdir(self):
        """Choose output directory"""
        directory = filedialog.askdirectory(title="Seleccionar carpeta de salida", 
                                          initialdir=self.outdir_var.get())
        if directory:
            self.outdir_var.set(directory)

    def _save_settings(self):
        """Save current settings to config"""
        self.config.update({
            'output_dir': self.outdir_var.get(),
            'bitrate': self.bitrate_var.get(),
            'format': self.format_var.get(),
            'create_artist_folders': self.artist_folder_var.get(),
            'skip_existing': self.skip_existing_var.get(),
            'save_cover_art': self.save_cover_var.get(),
            'cover_format': self.cover_format_var.get()
        })
        self.config_manager.save_config(self.config)
        messagebox.showinfo("Configuracion", "Configuracion guardada correctamente")

    def _reset_settings(self):
        """Reset settings to default values"""
        if messagebox.askyesno("Restaurar configuracion", "¿Restaurar todos los valores por defecto?"):
            defaults = self.config_manager.default_config
            self.outdir_var.set(defaults['output_dir'])
            self.bitrate_var.set(defaults['bitrate'])
            self.format_var.set(defaults['format'])
            self.artist_folder_var.set(defaults['create_artist_folders'])
            self.skip_existing_var.set(defaults['skip_existing'])
            self.save_cover_var.set(defaults['save_cover_art'])
            self.cover_format_var.set(defaults['cover_format'])
            messagebox.showinfo("Configuracion", "Configuracion restaurada")

    def _open_output_folder(self):
        """Open output folder in file explorer"""
        output_dir = self.outdir_var.get()
        if os.path.exists(output_dir):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(output_dir)
                elif os.name == 'posix':  # macOS and Linux
                    os.system(f'open "{output_dir}"' if sys.platform == 'darwin' else f'xdg-open "{output_dir}"')
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")
        else:
            messagebox.showwarning("Carpeta no encontrada", "La carpeta de salida no existe")

    def _open_config_folder(self):
        """Open configuration folder"""
        config_dir = Path(Config.CONFIG_FILE).parent.absolute()
        try:
            if os.name == 'nt':  # Windows
                os.startfile(str(config_dir))
            elif os.name == 'posix':  # macOS and Linux
                os.system(f'open "{config_dir}"' if sys.platform == 'darwin' else f'xdg-open "{config_dir}"')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta de configuracion: {e}")

    def _on_download(self):
        """Start download process"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL vacia", "Ingresa una URL valida")
            return
        
        output_dir = self.outdir_var.get()
        if not os.path.isdir(output_dir):
            messagebox.showwarning("Directorio invalido", "Selecciona un directorio valido")
            return
        
        # Update config with current values
        self.config.update({
            'output_dir': output_dir,
            'bitrate': self.bitrate_var.get(),
            'format': self.format_var.get(),
            'create_artist_folders': self.artist_folder_var.get(),
            'skip_existing': self.skip_existing_var.get(),
            'save_cover_art': self.save_cover_var.get(),
            'cover_format': self.cover_format_var.get()
        })
        
        # Reset UI state
        self.stop_event.clear()
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.progress.config(mode='determinate')
        self._clear_log()
        self._update_info("")
        self.lbl_status.config(text="Preparando descarga...")
        
        # Update buttons
        self.btn_download.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL)
        
        # Start worker
        self.worker = DownloaderThread(
            url=url,
            config=self.config,
            progress_queue=self.progress_queue,
            stop_event=self.stop_event,
            logger=self.logger
        )
        self.worker.start()

    def _on_cancel(self):
        """Cancel download"""
        if messagebox.askyesno("Cancelar", "¿Cancelar la descarga actual?"):
            self.stop_event.set()
            self.lbl_status.config(text="Cancelando...")

    def _periodic_check(self):
        """Periodic check for progress updates"""
        try:
            while True:
                msg_type, payload = self.progress_queue.get_nowait()
                self._handle_progress_message(msg_type, payload)
        except queue.Empty:
            pass
        
        # Check if worker finished
        if self.worker and not self.worker.is_alive():
            if self.btn_cancel['state'] == tk.NORMAL:
                self._finish_download()
        
        self.root.after(200, self._periodic_check)

    def _handle_progress_message(self, msg_type: str, payload: Any):
        """Handle different types of progress messages"""
        if msg_type == "progress":
            self._update_progress(payload)
        elif msg_type == "status":
            self._append_log(payload)
            self.lbl_status.config(text=payload)
        elif msg_type == "info":
            self._update_info_display(payload)
        elif msg_type == "complete":
            self._append_log(f"✅ {payload}")
            self.lbl_status.config(text=f"✅ {payload}")
            self.progress['value'] = 100
            self.progress_label.config(text="100%")
            self._finish_download(success=True)
        elif msg_type == "error":
            self._append_log(f"❌ {payload}")
            self.lbl_status.config(text=f"❌ {payload}")
            self._finish_download(success=False)
        elif msg_type == "canceled":
            self._append_log(f"⚠️ {payload}")
            self.lbl_status.config(text=f"⚠️ {payload}")
            self._finish_download(success=False)

    def _update_progress(self, info: Dict[str, Any]):
        """Update progress bar and status"""
        percent = info.get('percent')
        if percent is not None:
            progress_val = max(0, min(100, percent))
            self.progress['value'] = progress_val
            self.progress_label.config(text=f"{progress_val:.0f}%")
            
            downloaded = self._format_bytes(info.get('downloaded', 0))
            total = self._format_bytes(info.get('total', 0))
            speed = self._format_speed(info.get('speed', 0))
            eta = info.get('eta', 0)
            
            status = f"{progress_val:.1f}% - {downloaded}"
            if info.get('total'):
                status += f" / {total}"
            if speed:
                status += f" - {speed}"
            if eta and eta > 0:
                status += f" - ETA: {eta}s"
                
            self.lbl_status.config(text=status)
        else:
            # Indeterminate progress
            if self.progress['mode'] != 'indeterminate':
                self.progress.config(mode='indeterminate')
                self.progress.start(10)
            self.progress_label.config(text="...")
            
            downloaded = self._format_bytes(info.get('downloaded', 0))
            self.lbl_status.config(text=f"Descargando... {downloaded}")

    def _update_info_display(self, info: Dict[str, Any]):
        """Update info display with track information"""
        self.download_info = info
        info_text = f"Titulo: {info.get('title', 'N/A')}\n"
        info_text += f"Artista: {info.get('artist', 'N/A')}\n"
        if info.get('duration'):
            duration = time.strftime('%M:%S', time.gmtime(info['duration']))
            info_text += f"Duracion: {duration}"
        
        self._update_info(info_text)

    def _update_info(self, text: str):
        """Update info text widget"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", text)
        self.info_text.config(state=tk.DISABLED)

    def _append_log(self, text: str):
        """Append text to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.insert(tk.END, f"[{timestamp}] {text}\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def _clear_log(self):
        """Clear log text"""
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def _finish_download(self, success: bool = False):
        """Finish download and reset UI"""
        # Stop indeterminate progress
        if self.progress['mode'] == 'indeterminate':
            self.progress.stop()
            self.progress.config(mode='determinate')
        
        if not success:
            self.progress['value'] = 0
            self.progress_label.config(text="0%")
        
        # Reset buttons
        self.btn_download.config(state=tk.NORMAL)
        self.btn_cancel.config(state=tk.DISABLED)
        
        if success:
            # Show success notification
            if self.download_info:
                title = self.download_info.get('title', 'Audio')
                artist = self.download_info.get('artist', 'Artista desconocido')
                messagebox.showinfo("Descarga Completada", 
                                  f"'{title}' de {artist}\n\nAudio descargado, Agradece a Alonso cada descarga\nCaratula procesada\nMetadatos embebidos")
            
            # Update status
            self.lbl_status.config(text="Descarga completada - Listo para nueva descarga")

    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human readable string"""
        if not bytes_val:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} TB"

    def _format_speed(self, speed: float) -> str:
        """Format download speed"""
        if not speed:
            return ""
        return f"{self._format_bytes(speed)}/s"

    def _on_closing(self):
        """Handle application closing"""
        if self.worker and self.worker.is_alive():
            if messagebox.askyesno("Salir", "¿Cancelar descarga y salir?"):
                self.stop_event.set()
                self.root.after(100, self._force_close)
            return
        self.root.destroy()

    def _force_close(self):
        """Force close after worker cleanup"""
        try:
            if self.worker and self.worker.is_alive():
                self.worker.join(timeout=1.0)
        except:
            pass
        self.root.destroy()

# ---------------------------
# Main Entry Point
# ---------------------------
def main():
    """Main application entry point"""
    try:
        # Check for required dependencies
        import yt_dlp
    except ImportError:
        print("Error: yt-dlp no esta instalado. Instala con: pip install yt-dlp")
        sys.exit(1)
    
    root = tk.Tk()
    app = EnhancedApp(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        messagebox.showerror("Error", f"Error inesperado: {e}")

if __name__ == "__main__":
    main()