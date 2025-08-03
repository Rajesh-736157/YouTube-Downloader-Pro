import sys
import os
import threading
import pyperclip
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QLineEdit, QFileDialog, QCheckBox, 
    QRadioButton, QButtonGroup, QScrollArea, QFrame, QMessageBox,
    QProgressDialog, QTabWidget, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QFont, QPalette, QColor, QIcon

from downloader_core import VideoDownloader
from ui_components import ProgressWindow, QualitySelector, VideoInfoPanel
from settings_manager import SettingsManager

class YouTubeDownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.settings = SettingsManager()
        
        # Initialize components
        self.downloader = VideoDownloader()
        self.current_video_info = None
        self.quality_selector = None
        
        # Load settings
        self.download_path = self.settings.get_download_path()
        self.theme_mode = self.settings.get_theme()
        
        # Setup UI
        self.setup_ui()
        self.apply_theme()
        
        # Set window properties
        self.setWindowTitle("YouTube Downloader Pro")
        self.setMinimumSize(800, 600)
        self.resize(900, 650)
        
    def setup_ui(self):
        """Create the main UI layout"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        self.create_header(main_layout)
        
        # URL Input Section
        self.create_url_section(main_layout)
        
        # Video Info Panel (initially hidden)
        self.video_info_panel = VideoInfoPanel()
        main_layout.addWidget(self.video_info_panel)
        self.video_info_panel.hide()
        
        # Quality Selection (initially hidden)
        self.quality_frame = QFrame()
        main_layout.addWidget(self.quality_frame)
        self.quality_frame.hide()
        
        # Download Settings
        self.create_download_section(main_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready to download")
        
    def create_header(self, parent_layout):
        """Create header with title and theme toggle"""
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("YouTube Downloader Pro")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Theme toggle button
        self.theme_btn = QPushButton("🌙" if self.theme_mode == "light" else "☀️")
        self.theme_btn.setFixedSize(50, 40)
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_btn)
        
        parent_layout.addLayout(header_layout)
    
    def create_url_section(self, parent_layout):
        """Create URL input section"""
        url_frame = QFrame()
        url_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        url_layout = QVBoxLayout(url_frame)
        
        # URL Label
        url_label = QLabel("Enter Video URL:")
        url_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        url_layout.addWidget(url_label)
        
        # URL Input Row
        url_input_layout = QHBoxLayout()
        
        # URL Entry
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("Paste YouTube URL here...")
        self.url_entry.setFixedHeight(45)
        self.url_entry.setFont(QFont("Arial", 12))
        url_input_layout.addWidget(self.url_entry)
        
        # Paste Button
        paste_btn = QPushButton("📋 Paste")
        paste_btn.setFixedSize(80, 45)
        paste_btn.clicked.connect(self.paste_url)
        url_input_layout.addWidget(paste_btn)
        
        # Fetch Button
        self.fetch_btn = QPushButton("🔍 Fetch Info")
        self.fetch_btn.setFixedSize(120, 45)
        self.fetch_btn.clicked.connect(self.fetch_video_info)
        url_input_layout.addWidget(self.fetch_btn)
        
        url_layout.addLayout(url_input_layout)
        parent_layout.addWidget(url_frame)
    
    def create_download_section(self, parent_layout):
        """Create download settings section"""
        download_frame = QFrame()
        download_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        download_layout = QVBoxLayout(download_frame)
        
        # Download Path
        path_label = QLabel("Download Location:")
        path_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        download_layout.addWidget(path_label)
        
        path_layout = QHBoxLayout()
        
        self.path_entry = QLineEdit(self.download_path)
        self.path_entry.setFixedHeight(35)
        path_layout.addWidget(self.path_entry)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.setFixedSize(100, 35)
        browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(browse_btn)
        
        download_layout.addLayout(path_layout)
        
        # Audio only checkbox
        self.audio_only_cb = QCheckBox("Audio only (MP3)")
        download_layout.addWidget(self.audio_only_cb)
        
        # Download Button
        self.download_btn = QPushButton("⬇️ Download Video")
        self.download_btn.setFixedHeight(50)
        self.download_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.download_btn.clicked.connect(self.start_download)
        download_layout.addWidget(self.download_btn)
        
        parent_layout.addWidget(download_frame)
    
    def paste_url(self):
        """Paste URL from clipboard"""
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content and ("youtube.com" in clipboard_content or "youtu.be" in clipboard_content):
                self.url_entry.setText(clipboard_content)
                self.statusBar().showMessage("URL pasted successfully")
            else:
                QMessageBox.warning(self, "Warning", "No valid YouTube URL found in clipboard")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to paste: {str(e)}")
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        new_theme = "dark" if self.theme_mode == "light" else "light"
        self.theme_mode = new_theme
        self.settings.set_theme(new_theme)
        self.apply_theme()
        
        # Update button icon
        self.theme_btn.setText("🌙" if new_theme == "light" else "☀️")
        self.statusBar().showMessage(f"Switched to {new_theme} mode")

    def apply_theme(self):
        """Apply dark or light theme with proper contrast"""
        if self.theme_mode == "dark":
            # Dark theme colors
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QFrame {
                    background-color: #3c3c3c;
                    border: 1px solid #555555;
                    border-radius: 8px;
                    padding: 10px;
                }
                QLineEdit {
                    background-color: #4a4a4a;
                    border: 2px solid #606060;
                    border-radius: 6px;
                    color: #ffffff;
                    padding: 8px;
                }
                QLineEdit:focus {
                    border-color: #3b82f6;
                }
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
                QPushButton:pressed {
                    background-color: #1d4ed8;
                }
                QLabel {
                    color: #ffffff;
                }
                QCheckBox {
                    color: #ffffff;
                }
                QRadioButton {
                    color: #ffffff;
                }
            """)
        else:
            # Light theme with proper contrast
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #ffffff;
                    color: #000000;
                }
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 10px;
                }
                QLineEdit {
                    background-color: #ffffff;
                    border: 2px solid #d1d5db;
                    border-radius: 6px;
                    color: #000000;
                    padding: 8px;
                }
                QLineEdit:focus {
                    border-color: #3b82f6;
                }
                QPushButton {
                    background-color: #3b82f6;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
                QPushButton:pressed {
                    background-color: #1d4ed8;
                }
                QLabel {
                    color: #000000;
                }
                QCheckBox {
                    color: #000000;
                }
                QRadioButton {
                    color: #000000;
                }
                QCheckBox::indicator {
                    border: 2px solid #6b7280;
                    border-radius: 3px;
                    background-color: #ffffff;
                }
                QCheckBox::indicator:checked {
                    background-color: #3b82f6;
                    border-color: #3b82f6;
                }
                QRadioButton::indicator {
                    border: 2px solid #6b7280;
                    border-radius: 8px;
                    background-color: #ffffff;
                }
                QRadioButton::indicator:checked {
                    background-color: #3b82f6;
                    border-color: #3b82f6;
                }
            """)

    def fetch_video_info(self):
        """Fetch video information"""
        url = self.url_entry.text().strip()
        if not url:
            QMessageBox.critical(self, "Error", "Please enter a YouTube URL")
            return
        
        self.statusBar().showMessage("Fetching video information...")
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("Loading...")
        
        # Start fetching in background thread
        self.fetch_thread = VideoInfoThread(url, self.downloader)
        self.fetch_thread.info_fetched.connect(self.on_video_info_fetched)
        self.fetch_thread.error_occurred.connect(self.on_fetch_error)
        self.fetch_thread.start()

    def on_video_info_fetched(self, info):
        """Handle successful video info fetch"""
        self.current_video_info = info
        
        # Update video info panel
        self.video_info_panel.update_info(info)
        self.video_info_panel.show()
        
        # Show quality selector
        self.show_quality_selector(info.get('formats', []))
        
        # Re-enable fetch button
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("🔍 Fetch Info")
        self.statusBar().showMessage("Video information loaded successfully")

    def on_fetch_error(self, error_msg):
        """Handle fetch error"""
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("🔍 Fetch Info")
        self.statusBar().showMessage("Failed to fetch video information")
        QMessageBox.critical(self, "Error", f"Failed to fetch video info: {error_msg}")

    def show_quality_selector(self, formats):
        """Show quality selection options"""
        if hasattr(self, 'quality_selector') and self.quality_selector:
            self.quality_selector.deleteLater()
        
        self.quality_selector = QualitySelector(formats)
        
        # Clear existing layout in quality frame
        if self.quality_frame.layout():
            while self.quality_frame.layout().count():
                child = self.quality_frame.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            layout = QVBoxLayout(self.quality_frame)
        
        self.quality_frame.layout().addWidget(self.quality_selector)
        self.quality_frame.show()

    def browse_folder(self):
        """Browse for download folder"""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", self.download_path
        )
        if folder:
            self.download_path = folder
            self.path_entry.setText(folder)
            self.settings.set_download_path(folder)
            self.statusBar().showMessage("Download location updated")

    def start_download(self):
        """Start the download process"""
        if not self.current_video_info:
            QMessageBox.warning(self, "Warning", "Please fetch video info first")
            return
        
        if not hasattr(self, 'quality_selector') or not self.quality_selector:
            QMessageBox.warning(self, "Warning", "Please select a quality option")
            return
        
        # Get settings
        url = self.url_entry.text().strip()
        quality = self.quality_selector.get_selected_quality()
        output_path = self.path_entry.text().strip()
        audio_only = self.audio_only_cb.isChecked()
        
        if not output_path:
            QMessageBox.warning(self, "Warning", "Please select a download location")
            return
        
        # Create progress window
        progress_window = ProgressWindow(self, self.current_video_info)
        progress_window.show()
        
        # Start download thread
        self.download_thread = DownloadThread(
            url, quality, output_path, audio_only, self.downloader
        )
        self.download_thread.progress_updated.connect(progress_window.update_progress)
        self.download_thread.download_completed.connect(progress_window.download_complete)
        self.download_thread.download_failed.connect(progress_window.download_failed)
        self.download_thread.start()
    
    def closeEvent(self, event):
        """Handle application closing"""
        self.settings.save_settings()
        event.accept()

class VideoInfoThread(QThread):
    info_fetched = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, url, downloader):
        super().__init__()
        self.url = url
        self.downloader = downloader
    
    def run(self):
        try:
            info = self.downloader.get_video_info(self.url)
            if info:
                self.info_fetched.emit(info)
            else:
                self.error_occurred.emit("Failed to fetch video information")
        except Exception as e:
            self.error_occurred.emit(str(e))

class DownloadThread(QThread):
    progress_updated = Signal(int, str)
    download_completed = Signal()
    download_failed = Signal()
    
    def __init__(self, url, quality, output_path, audio_only, downloader):
        super().__init__()
        self.url = url
        self.quality = quality
        self.output_path = output_path
        self.audio_only = audio_only
        self.downloader = downloader
    
    def run(self):
        def progress_callback(progress, status):
            self.progress_updated.emit(int(progress), status)
        
        try:
            success = self.downloader.download_video(
                self.url, self.quality, self.output_path, 
                self.audio_only, progress_callback
            )
            
            if success:
                self.download_completed.emit()
            else:
                self.download_failed.emit()
        except Exception as e:
            print(f"Download error: {e}")
            self.download_failed.emit()

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("YouTube Downloader Pro")
    app.setOrganizationName("Your Name")
    
    window = YouTubeDownloaderApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
