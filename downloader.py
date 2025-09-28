# -*- coding: utf-8 -*-

import customtkinter as ctk
import yt_dlp
import threading
from pathlib import Path
import os
import sys
import platform

# --- Configuración Inicial ---
# Establece la apariencia de la aplicación (System, Dark, Light)
ctk.set_appearance_mode("Dark")
# Establece el tema de color por defecto para los widgets
ctk.set_default_color_theme("blue")

class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Configuración de la Ventana Principal ---
        self.title("Descargador de Videos Premium")
        self.geometry("700x450")
        self.minsize(600, 400)

        # --- Variables de Estado ---
        self.selected_platform = None # Plataforma seleccionada: 'youtube', 'tiktok', 'instagram'
        self.download_path = str(Path.home() / "Downloads") # Ruta de descargas del usuario

        # --- Creación de los Widgets (Componentes de la UI) ---
        self.create_widgets()

    def create_widgets(self):
        """Crea y organiza todos los elementos de la interfaz gráfica."""
        
        # --- Frame para los botones de selección de plataforma ---
        self.platform_frame = ctk.CTkFrame(self)
        self.platform_frame.pack(pady=20, padx=20, fill="x")

        self.label_platform = ctk.CTkLabel(self.platform_frame, text="1. Selecciona una plataforma:", font=ctk.CTkFont(size=16, weight="bold"))
        self.label_platform.pack(pady=10)

        self.youtube_button = ctk.CTkButton(self.platform_frame, text="YouTube", command=lambda: self.select_platform("youtube"))
        self.youtube_button.pack(side="left", expand=True, padx=10, pady=10)

        self.tiktok_button = ctk.CTkButton(self.platform_frame, text="TikTok", command=lambda: self.select_platform("tiktok"))
        self.tiktok_button.pack(side="left", expand=True, padx=10, pady=10)

        self.instagram_button = ctk.CTkButton(self.platform_frame, text="Instagram", command=lambda: self.select_platform("instagram"))
        self.instagram_button.pack(side="left", expand=True, padx=10, pady=10)

        # --- Frame para la entrada de URL y el botón de descarga ---
        # Este frame estará oculto al principio
        self.download_frame = ctk.CTkFrame(self)
        
        self.label_url = ctk.CTkLabel(self.download_frame, text="2. Pega la URL del video aquí:", font=ctk.CTkFont(size=16, weight="bold"))
        self.label_url.pack(pady=10)
        
        self.url_entry = ctk.CTkEntry(self.download_frame, placeholder_text="https://...", width=400, height=35)
        self.url_entry.pack(pady=10, padx=20, fill="x")

        self.download_button = ctk.CTkButton(self.download_frame, text="Descargar Video", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.start_download_thread)
        self.download_button.pack(pady=20, padx=20)
        
        # --- Etiqueta de Estado ---
        self.status_label = ctk.CTkLabel(self, text="Bienvenido. Selecciona una plataforma para comenzar.", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=10, side="bottom", fill="x")
        
        # --- Barra de Progreso ---
        self.progress_bar = ctk.CTkProgressBar(self, mode='determinate')
        self.progress_bar.set(0)
        # Se mostrará cuando la descarga comience
        

    def select_platform(self, platform):
        """
        Se activa al seleccionar una plataforma. Muestra el frame de descarga.
        """
        self.selected_platform = platform
        self.status_label.configure(text=f"Plataforma seleccionada: {platform.capitalize()}. Listo para descargar.")
        self.label_url.configure(text=f"2. Pega la URL de {platform.capitalize()} aquí:")
        
        # Muestra el frame de descarga si no está visible
        self.download_frame.pack(pady=20, padx=20, fill="x", after=self.platform_frame)
        self.progress_bar.pack(pady=(0, 10), padx=20, side="bottom", fill="x", before=self.status_label)


    def start_download_thread(self):
        """
        Inicia la descarga en un hilo separado para no congelar la UI.
        """
        url = self.url_entry.get()
        if not url:
            self.status_label.configure(text="Error: Por favor, introduce una URL.", text_color="red")
            return
        
        # Deshabilitar botón para evitar múltiples descargas
        self.download_button.configure(state="disabled", text="Descargando...")
        self.progress_bar.set(0)

        # Crear y empezar el hilo de descarga
        download_thread = threading.Thread(target=self.download_video, args=(url,))
        download_thread.start()

    def _get_ffmpeg_path(self):
        """Determina la ruta del ejecutable FFmpeg empaquetado."""
        
        # Define el nombre del ejecutable según el sistema operativo
        ffmpeg_exe = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"

        if getattr(sys, 'frozen', False):
            # Estamos ejecutando como un archivo empaquetado (.exe)
            base_path = sys._MEIPASS
        else:
            # Estamos ejecutando como un script de Python normal
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Devuelve la ruta completa al ejecutable de FFmpeg
        return os.path.join(base_path, ffmpeg_exe)

    def download_video(self, url):
        """
        Función que se ejecuta en el hilo y realiza la descarga con yt-dlp.
        """
        try:
            # --- OPCIONES DE DESCARGA MEJORADAS ---
            # Se prioriza el códec de video 'avc1' (H.264) por ser el más compatible,
            # lo que evita el problema de la pantalla negra en algunos videos.
            ydl_opts = {
                'format': 'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'noplaylist': True, # Descargar solo el video, no la lista de reproducción
                'ffmpeg_location': self._get_ffmpeg_path()
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.after(0, self.update_status, "Iniciando descarga...", "white")
                ydl.download([url])

        except Exception as e:
            # En caso de error, mostrarlo en la etiqueta de estado
            self.after(0, self.update_status, f"Error: {str(e)}", "red")
        finally:
            # Reactivar el botón de descarga cuando todo termine (éxito o error)
            self.after(0, self.reset_ui)

    def progress_hook(self, d):
        """
        Hook que se llama durante la descarga para actualizar la UI.
        """
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes')
            if total_bytes and downloaded_bytes:
                progress = downloaded_bytes / total_bytes
                percentage = progress * 100
                self.after(0, self.update_progress, progress, f"Descargando... {percentage:.1f}%")

        elif d['status'] == 'finished':
            self.after(0, self.update_status, "¡Descarga completada con éxito!", "green")
            # El reseteo final se hace en el 'finally' del bloque try/except

    def update_status(self, text, color):
        """Función segura para actualizar la etiqueta de estado desde cualquier hilo."""
        self.status_label.configure(text=text, text_color=color)

    def update_progress(self, value, text):
        """Función segura para actualizar la barra y etiqueta de progreso."""
        self.progress_bar.set(value)
        self.status_label.configure(text=text, text_color="white")
        
    def reset_ui(self):
        """Restaura la interfaz a su estado inicial después de una descarga."""
        self.download_button.configure(state="normal", text="Descargar Video")
        self.url_entry.delete(0, 'end') # Limpia el campo de URL

if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
