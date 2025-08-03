import yt_dlp
import os
import sys
from pathlib import Path

class VideoDownloader:
    def __init__(self):
        self.current_download = None
        self.setup_ffmpeg_path()
    
    def setup_ffmpeg_path(self):
        """Setup FFmpeg path for both development and packaged app"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = Path(sys.executable).parent
        else:
            # Running as Python script
            base_path = Path(__file__).parent.parent
        
        # Look for ffmpeg in multiple locations
        ffmpeg_locations = [
            base_path / 'ffmpeg.exe',           # Same directory as exe
            base_path / 'tools' / 'ffmpeg.exe', # tools subfolder
            'ffmpeg.exe'                        # System PATH
        ]
        
        self.ffmpeg_path = None
        for location in ffmpeg_locations:
            if Path(location).exists():
                self.ffmpeg_path = str(location)
                break
    
    def get_video_info(self, url):
        """Get video information without downloading"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def download_video(self, url, quality, output_path, audio_only=False, progress_callback=None):
        """Download video with advanced quality selection support"""
        
        # Store progress callback for use in _progress_hook
        self.progress_callback = progress_callback
        
        if audio_only:
            format_selector = 'bestaudio/best'
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            # Handle advanced format combinations
            if '+' in quality:
                # Advanced mode: specific video+audio combination
                format_selector = quality
            elif quality == "auto":
                # Auto mode: best available
                format_selector = 'bestvideo+bestaudio/best'
            elif quality in ['best', 'worst']:
                # Simple quality selection
                format_selector = quality
            else:
                # Specific resolution
                format_selector = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best'
            
            postprocessors = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }]
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': format_selector,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'extract_flat': False,
            'postprocessors': postprocessors,
            'merge_output_format': 'mp4',
        }
        
        # Add FFmpeg path if available
        if self.ffmpeg_path:
            ydl_opts['ffmpeg_location'] = self.ffmpeg_path
            print(f"Using FFmpeg from: {self.ffmpeg_path}")
        else:
            print("FFmpeg not found - using fallback format selection")
            # Use single format selection to avoid merging
            ydl_opts['format'] = 'best[ext=mp4]/best'
        
        # Add progress hook if callback provided
        if progress_callback:
            ydl_opts['progress_hooks'] = [self._progress_hook]
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            print(f"Download error: {e}")
            return False
    
    def _progress_hook(self, d):
        """Handle download progress updates from yt-dlp"""
        if not hasattr(self, 'progress_callback') or not self.progress_callback:
            return
        
        try:
            status = d.get('status', 'unknown')
            
            if status == 'downloading':
                if 'downloaded_bytes' in d and 'total_bytes' in d:
                    progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    speed = d.get('speed', 0)
                    
                    # Format speed
                    if speed:
                        speed_mb = speed / (1024 * 1024)
                        if speed_mb >= 1:
                            speed_str = f"{speed_mb:.2f} MB/s"
                        else:
                            speed_kb = speed / 1024
                            speed_str = f"{speed_kb:.1f} KB/s"
                    else:
                        speed_str = "Unknown speed"
                    
                    # Call the progress callback
                    self.progress_callback(progress, f"📥 Downloading... {speed_str}")
                else:
                    # No byte information available
                    self.progress_callback(0, "📥 Downloading...")
                    
            elif status == 'finished':
                self.progress_callback(95, "🔄 Processing and merging...")
                
        except Exception as e:
            print(f"Progress hook error: {e}")
            # Fallback - just call with basic info
            if hasattr(self, 'progress_callback') and self.progress_callback:
                self.progress_callback(50, "Downloading...")
