import json
import os
from pathlib import Path

class SettingsManager:
    def __init__(self):
        self.config_dir = Path("config")
        self.config_file = self.config_dir / "settings.json"
        self.default_settings = {
            "theme": "dark",
            "download_path": str(Path.home() / "Downloads"),
            "last_quality": "auto",
            "audio_only": False,
            "window_geometry": "900x650"
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file or create default"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                # Merge with defaults for new settings
                for key, value in self.default_settings.items():
                    if key not in settings:
                        settings[key] = value
                return settings
            else:
                return self.default_settings.copy()
        except Exception:
            return self.default_settings.copy()
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")
    
    def get_theme(self):
        return self.settings.get("theme", "dark")
    
    def set_theme(self, theme):
        self.settings["theme"] = theme
        self.save_settings()
    
    def get_download_path(self):
        return self.settings.get("download_path", str(Path.home() / "Downloads"))
    
    def set_download_path(self, path):
        self.settings["download_path"] = path
        self.save_settings()
    
    def get_last_quality(self):
        return self.settings.get("last_quality", "auto")
    
    def set_last_quality(self, quality):
        self.settings["last_quality"] = quality
        self.save_settings()
