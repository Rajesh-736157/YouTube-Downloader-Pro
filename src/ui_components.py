from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
    QFrame, QButtonGroup, QRadioButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QDialog, QProgressBar
)

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class VideoInfoPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Thumbnail placeholder
        self.thumbnail_label = QLabel("📹")
        self.thumbnail_label.setFont(QFont("Arial", 48))
        self.thumbnail_label.setFixedSize(120, 90)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("border: 1px solid gray; border-radius: 8px;")
        layout.addWidget(self.thumbnail_label)
        
        # Video details
        details_layout = QVBoxLayout()
        
        self.title_label = QLabel("")
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)
        details_layout.addWidget(self.title_label)
        
        self.details_label = QLabel("")
        self.details_label.setFont(QFont("Arial", 12))
        details_layout.addWidget(self.details_label)
        
        layout.addLayout(details_layout)
        
    def update_info(self, video_info):
        title = video_info.get('title', 'Unknown Title')
        duration = video_info.get('duration', 0)
        uploader = video_info.get('uploader', 'Unknown')
        
        # Format duration
        if duration:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
        else:
            duration_str = "Unknown"
        
        self.title_label.setText(title[:80] + "..." if len(title) > 80 else title)
        self.details_label.setText(f"👤 {uploader} • ⏱️ {duration_str}")

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
    QFrame, QButtonGroup, QRadioButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)


class QualitySelector(QWidget):
    def __init__(self, formats):
        super().__init__()
        self.formats = formats
        self.selected_format_id = "auto"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Select Video Quality:")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Create scrollable area for quality table
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        
        # Quality table widget
        self.quality_table = QTableWidget()
        self.populate_quality_table()
        
        scroll_area.setWidget(self.quality_table)
        layout.addWidget(scroll_area)
        
    def populate_quality_table(self):
        """Populate table with detailed format information"""
        # Parse formats and create detailed entries
        quality_options = self.parse_detailed_formats()
        
        # Set up table
        self.quality_table.setRowCount(len(quality_options))
        self.quality_table.setColumnCount(7)
        
        # Headers
        headers = ["Select", "Resolution", "HDR/SDR", "Video Codec", "Audio Codec", "Video Bitrate", "Audio Bitrate"]
        self.quality_table.setHorizontalHeaderLabels(headers)
        
        # Configure table appearance
        self.quality_table.setAlternatingRowColors(True)
        self.quality_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.quality_table.verticalHeader().setVisible(False)
        
        # Populate rows
        for row, quality_info in enumerate(quality_options):
            # Radio button for selection
            radio_widget = QWidget()
            radio_layout = QHBoxLayout(radio_widget)
            radio_layout.setContentsMargins(5, 5, 5, 5)
            
            radio_button = QRadioButton()
            radio_button.setProperty("format_id", quality_info["format_id"])
            radio_button.toggled.connect(self.on_selection_changed)
            
            if row == 0:  # Select first option by default
                radio_button.setChecked(True)
                self.selected_format_id = quality_info["format_id"]
            
            radio_layout.addWidget(radio_button)
            radio_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.quality_table.setCellWidget(row, 0, radio_widget)
            
            # Other columns
            columns_data = [
                quality_info["resolution"],
                quality_info["hdr_status"],
                quality_info["video_codec"],
                quality_info["audio_codec"],
                quality_info["video_bitrate"],
                quality_info["audio_bitrate"]
            ]
            
            for col, data in enumerate(columns_data, 1):
                item = QTableWidgetItem(str(data))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
                
                # Color coding for HDR
                if col == 2 and "HDR" in str(data):
                    item.setBackground(Qt.GlobalColor.yellow)
                
                self.quality_table.setItem(row, col, item)
        
        # Adjust column widths
        header = self.quality_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Select column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Resolution
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # HDR/SDR
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Video Codec
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Audio Codec
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Video Bitrate
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Audio Bitrate
    
    def parse_detailed_formats(self):
        """Parse yt-dlp formats into detailed quality options"""
        quality_options = [{
            "format_id": "auto",
            "resolution": "Best Available",
            "hdr_status": "Auto",
            "video_codec": "Auto Select",
            "audio_codec": "Auto Select", 
            "video_bitrate": "Best",
            "audio_bitrate": "Best"
        }]
        
        if not self.formats:
            return quality_options
        
        # Group video and audio formats
        video_formats = []
        audio_formats = []
        combined_formats = []
        
        for fmt in self.formats:
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')
            
            if vcodec != 'none' and acodec != 'none':
                combined_formats.append(fmt)
            elif vcodec != 'none':
                video_formats.append(fmt)
            elif acodec != 'none':
                audio_formats.append(fmt)
        
        # Process combined formats first
        for fmt in combined_formats[:10]:  # Limit to prevent overwhelming UI
            quality_info = self.extract_format_details(fmt)
            if quality_info:
                quality_options.append(quality_info)
        
        # Process video-only formats (will be combined with best audio)
        for fmt in video_formats[:15]:  # Limit to prevent overwhelming UI
            quality_info = self.extract_format_details(fmt, video_only=True)
            if quality_info:
                quality_options.append(quality_info)
        
        return quality_options
    
    def extract_format_details(self, fmt, video_only=False):
        """Extract detailed information from a format"""
        # Basic info
        format_id = fmt.get('format_id', 'unknown')
        height = fmt.get('height', 0)
        fps = fmt.get('fps', 30)
        vcodec = fmt.get('vcodec', 'none')
        acodec = fmt.get('acodec', 'none')
        vbr = fmt.get('vbr', 0)  # Video bitrate
        abr = fmt.get('abr', 0)  # Audio bitrate
        format_note = fmt.get('format_note', '').lower()
        
        # Skip if no meaningful resolution
        if height < 144:
            return None
        
        # Resolution string
        resolution = f"{height}p"
        if fps and fps > 30:
            resolution += f"{int(fps)}"
        
        # HDR detection
        hdr_status = "HDR" if any(hdr_indicator in format_note for hdr_indicator in ['hdr', 'hdr10', 'dolby vision']) else "SDR"
        
        # Video codec parsing
        video_codec = "None"
        if vcodec and vcodec != 'none':
            if 'avc1' in vcodec or 'h264' in vcodec.lower():
                video_codec = f"H.264 ({vcodec[:8]})"
            elif 'vp9' in vcodec.lower():
                video_codec = f"VP9 ({vcodec[:8]})"
            elif 'av01' in vcodec.lower():
                video_codec = f"AV1 ({vcodec[:8]})"
            else:
                video_codec = vcodec[:15]
        
        # Audio codec parsing
        audio_codec = "Auto Select" if video_only else "None"
        if acodec and acodec != 'none':
            if 'mp4a' in acodec:
                audio_codec = f"AAC ({acodec[:8]})"
            elif 'opus' in acodec.lower():
                audio_codec = f"Opus ({acodec[:8]})"
            elif 'vorbis' in acodec.lower():
                audio_codec = f"Vorbis ({acodec[:8]})"
            else:
                audio_codec = acodec[:15]
        
        # Bitrate formatting
        video_bitrate = f"{vbr}kbps" if vbr else "Unknown"
        audio_bitrate = f"{abr}kbps" if abr and not video_only else ("Auto" if video_only else "None")
        
        return {
            "format_id": format_id,
            "resolution": resolution,
            "hdr_status": hdr_status,
            "video_codec": video_codec,
            "audio_codec": audio_codec,
            "video_bitrate": video_bitrate,
            "audio_bitrate": audio_bitrate
        }
    
    def on_selection_changed(self, checked):
        """Handle radio button selection change"""
        if checked:
            radio_button = self.sender()
            self.selected_format_id = radio_button.property("format_id")
    
    def get_selected_quality(self):
        """Get the selected format ID"""
        return self.selected_format_id


    def __init__(self, formats):
        super().__init__()
        self.formats = formats
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Select Quality:")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Radio button group
        self.button_group = QButtonGroup()
        
        # Quality options
        qualities = [
            ("🎬 Best Quality", "auto"),
            ("🔥 4K (2160p)", "2160"),
            ("📺 HD (1080p)", "1080"),
            ("📱 HD (720p)", "720"),
            ("💾 SD (480p)", "480"),
            ("📞 Low (360p)", "360")
        ]
        
        for i, (text, value) in enumerate(qualities):
            radio = QRadioButton(text)
            radio.setProperty("quality_value", value)
            self.button_group.addButton(radio, i)
            layout.addWidget(radio)
            
            if i == 0:  # Select first option by default
                radio.setChecked(True)
    
    def get_selected_quality(self):
        checked_button = self.button_group.checkedButton()
        if checked_button:
            return checked_button.property("quality_value")
        return "auto"

class ProgressWindow(QDialog):
    def __init__(self, parent, video_info):
        super().__init__(parent)
        self.video_info = video_info
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Download Progress")
        self.setFixedSize(400, 150)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Video title
        title = self.video_info.get('title', 'Unknown Video')
        title_label = QLabel(title[:50] + "..." if len(title) > 50 else title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Starting download...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
    
    def update_progress(self, progress, status):
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def download_complete(self):
        self.status_label.setText("✅ Download completed!")
        self.progress_bar.setValue(100)
        
        # Auto close after 2 seconds
        QTimer.singleShot(2000, self.accept)
    
    def download_failed(self):
        self.status_label.setText("❌ Download failed!")
