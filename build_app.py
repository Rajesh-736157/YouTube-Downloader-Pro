import os
import subprocess
import sys
import shutil
import urllib.request
import zipfile
import time
from pathlib import Path

def safe_rmtree(path, max_retries=3):
    """Safely remove directory tree with retries"""
    path = Path(path)
    if not path.exists():
        return True
    
    for attempt in range(max_retries):
        try:
            # Try to make all files writable
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        file_path.chmod(0o777)  # Make writable
                    except Exception:
                        pass
            
            # Remove the directory
            shutil.rmtree(path)
            return True
            
        except PermissionError as e:
            print(f"⚠️  Attempt {attempt + 1}: Permission denied - {e}")
            if attempt < max_retries - 1:
                print("🔄 Waiting 3 seconds and retrying...")
                time.sleep(3)
            else:
                print("❌ Could not remove directory after multiple attempts")
                return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    return False

def download_ffmpeg():
    """Download FFmpeg if not present"""
    tools_dir = Path("tools")
    tools_dir.mkdir(exist_ok=True)
    
    ffmpeg_path = tools_dir / "ffmpeg.exe"
    
    if ffmpeg_path.exists():
        print("✅ FFmpeg already present")
        return
    
    print("📥 Downloading FFmpeg...")
    
    # Download FFmpeg
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    temp_zip = "ffmpeg_temp.zip"
    
    try:
        urllib.request.urlretrieve(ffmpeg_url, temp_zip)
        
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            # Find ffmpeg.exe in the zip
            for file_info in zip_ref.filelist:
                if file_info.filename.endswith('ffmpeg.exe'):
                    # Extract only ffmpeg.exe
                    with zip_ref.open(file_info) as source:
                        with open(ffmpeg_path, 'wb') as target:
                            target.write(source.read())
                    break
        
        os.remove(temp_zip)
        print("✅ FFmpeg downloaded successfully")
        
    except Exception as e:
        print(f"❌ Failed to download FFmpeg: {e}")
        print("Please download FFmpeg manually from https://ffmpeg.org/")

def build_executable():
    """Build standalone executable with all dependencies"""
    
    print("🔨 Building YouTube Downloader executable...")
    
    # Download FFmpeg if needed
    download_ffmpeg()
    
    # Clean previous builds with safe removal
    print("🧹 Cleaning previous builds...")
    if os.path.exists("dist"):
        if not safe_rmtree("dist"):
            print("⚠️  Could not remove dist folder, continuing anyway...")
    
    if os.path.exists("build"):
        if not safe_rmtree("build"):
            print("⚠️  Could not remove build folder, continuing anyway...")
    
    # PyInstaller command with FFmpeg bundling
    cmd = [
    "pyinstaller",
    "--onefile",
    "--windowed", 
    "--name", "YouTubeDownloader",
    "--add-data", "tools;tools",
    "--add-data", "assets;assets",
    "--hidden-import", "PySide6.QtCore",
    "--hidden-import", "PySide6.QtWidgets", 
    "--hidden-import", "PySide6.QtGui",
    "--collect-all", "PySide6",
    "--collect-all", "yt_dlp",
    "src/main.py"
    ]
    
    # Add icon if available
    icon_path = Path("assets/app_icon.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Build completed successfully!")
        
        # Copy FFmpeg to dist folder as backup
        dist_ffmpeg = Path("dist/ffmpeg.exe")
        tools_ffmpeg = Path("tools/ffmpeg.exe")
        if tools_ffmpeg.exists():
            shutil.copy2(tools_ffmpeg, dist_ffmpeg)
            print("✅ FFmpeg copied to dist folder")
        
        print(f"📦 Executable location: {Path('dist/YouTubeDownloader.exe').absolute()}")
        
        # Create portable package
        create_portable_package()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)

def create_portable_package():
    """Create a portable package with better error handling"""
    print("📦 Creating portable package...")
    
    package_dir = Path("YouTubeDownloader_Portable")
    
    # Safe removal of existing package directory
    if package_dir.exists():
        print("🧹 Removing existing portable package...")
        if not safe_rmtree(package_dir):
            print("⚠️  Warning: Could not remove existing package directory")
            print("💡 Trying to create package anyway...")
    
    # Create directory
    try:
        package_dir.mkdir(exist_ok=True)
    except Exception as e:
        print(f"❌ Could not create package directory: {e}")
        return
    
    # Copy files with individual error handling
    files_to_copy = [
        ("dist/YouTubeDownloader.exe", "YouTubeDownloader.exe"),
        ("dist/ffmpeg.exe", "ffmpeg.exe")
    ]
    
    copied_files = []
    for src, dst in files_to_copy:
        src_path = Path(src)
        dst_path = package_dir / dst
        
        if src_path.exists():
            try:
                # Remove destination file if it exists
                if dst_path.exists():
                    dst_path.chmod(0o777)
                    dst_path.unlink()
                
                shutil.copy2(src_path, dst_path)
                copied_files.append(dst)
                print(f"✅ Copied {dst}")
                
            except Exception as e:
                print(f"⚠️  Warning: Could not copy {src}: {e}")
        else:
            print(f"⚠️  Warning: {src} not found, skipping...")
    
    # Create README
    try:
        readme_content = """YouTube Downloader Pro - Portable Edition

✅ FEATURES:
- Modern GUI with day/night mode
- Multiple quality options (4K, 1080p, 720p, etc.)
- Audio-only downloads (MP3)
- Paste button for easy URL input
- Progress tracking
- Remembers your settings

🚀 HOW TO USE:
1. Double-click YouTubeDownloader.exe
2. Paste or enter a YouTube URL
3. Click "Fetch Info" to see video details
4. Select your preferred quality
5. Choose download location (optional)
6. Click "Download Video"

📁 FILES INCLUDED:
- YouTubeDownloader.exe (main application)
- ffmpeg.exe (video processing - required)

⚠️ IMPORTANT:
Keep both files in the same folder!

🔧 TROUBLESHOOTING:
- If downloads fail, ensure both exe files are together
- Check your internet connection
- Some videos may be region-locked
- Antivirus might flag the app initially (it's safe)

For support, contact: [your-email]
"""
        
        readme_path = package_dir / "README.txt"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        copied_files.append("README.txt")
        print("✅ Created README.txt")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not create README: {e}")
    
    # Final summary
    if copied_files:
        print(f"✅ Portable package created: {package_dir}/")
        print("🎉 Your app is ready to share!")
        print("📋 Package contents:")
        for item in package_dir.iterdir():
            try:
                size = item.stat().st_size / (1024 * 1024)  # Size in MB
                print(f"   - {item.name} ({size:.1f} MB)")
            except Exception:
                print(f"   - {item.name}")
        
        print(f"\n💡 To share with friends:")
        print(f"   1. Right-click on '{package_dir}' folder")
        print(f"   2. Choose 'Send to > Compressed (zipped) folder'")
        print(f"   3. Share the ZIP file!")
    else:
        print("❌ No files were copied to the portable package")

if __name__ == "__main__":
    build_executable()
