from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFileDialog, QFrame, QProgressBar)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
import pandas as pd
import cv2
import numpy as np
from styles import StyleSheetCSV
from widgets.csv_convert import CSVConverterWidget
from PyQt5.QtGui import QImage, QPixmap

class FrameDisplayWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: black;
                border-radius: 8px;
            }
        """)
        
    def update_frame(self, frame):
        if frame is None:
            return
            
        height, width = frame.shape[:2]
        bytes_per_line = 3 * width
        
        # Convert numpy array to QImage
        q_img = QImage(
            frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888
        )
        
        # Scale the image to fit the label while maintaining aspect ratio
        scaled_pixmap = QPixmap.fromImage(q_img).scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)

class CSVAnalysisWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CSV Analysis Tool")
        self.setMinimumSize(1200, 700)
        self.events_df = None
        self.label_df = None
        self.current_frame_index = 0
        self.is_playing = False
        
        # Set window background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(StyleSheetCSV.BACKGROUND_COLOR))
        self.setPalette(palette)
        
        self.setup_ui()
        
        # Setup timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.timer.setInterval(100)  # 100ms between frames

    def setup_ui(self):
        # Main layout with left and right panels
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Left Panel - Controls
        left_panel = QFrame()
        left_panel.setStyleSheet(f"background-color: {StyleSheetCSV.CARD_COLOR}; border-radius: 12px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(20)
        
        # Add converter button
        converter_btn = QPushButton("Open RAW to CSV Converter")
        converter_btn.setStyleSheet(StyleSheetCSV.BUTTON)
        converter_btn.clicked.connect(self.open_converter)
        left_layout.addWidget(converter_btn)

        # File Selection Section
        title_layout = QHBoxLayout()
        title_icon = QLabel("📊")
        title_icon.setFont(QFont("", 20))
        title_label = QLabel("CSV Analysis")
        title_label.setStyleSheet(StyleSheetCSV.TITLE_LABEL)
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        left_layout.addLayout(title_layout)

        # Events CSV Section
        events_layout = QVBoxLayout()  # Changed to vertical layout
        self.events_label = QLabel("Events CSV: Not selected")
        self.events_label.setStyleSheet(StyleSheetCSV.LABEL)
        self.events_label.setWordWrap(True)  # Enable word wrap
        self.events_label.setMaximumWidth(300)  # Limit width
        self.load_events_btn = QPushButton("Load Events CSV")
        self.load_events_btn.setStyleSheet(StyleSheetCSV.LOAD_BUTTON)
        self.load_events_btn.clicked.connect(self.load_events_csv)
        events_layout.addWidget(self.events_label)
        events_layout.addWidget(self.load_events_btn)
        left_layout.addLayout(events_layout)

        # Labels CSV Section
        labels_layout = QVBoxLayout()  # Changed to vertical layout
        self.labels_label = QLabel("Labels CSV: Not selected")
        self.labels_label.setStyleSheet(StyleSheetCSV.LABEL)
        self.labels_label.setWordWrap(True)  # Enable word wrap
        self.labels_label.setMaximumWidth(300)  # Limit width
        self.load_labels_btn = QPushButton("Load Labels CSV")
        self.load_labels_btn.setStyleSheet(StyleSheetCSV.LOAD_BUTTON)
        self.load_labels_btn.clicked.connect(self.load_labels_csv)
        labels_layout.addWidget(self.labels_label)
        labels_layout.addWidget(self.load_labels_btn)
        left_layout.addLayout(labels_layout)

        # Playback Controls
        controls_layout = QHBoxLayout()
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setStyleSheet(StyleSheetCSV.PLAY_BUTTON)
        self.play_btn.clicked.connect(self.toggle_playback)
        self.play_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("⬛ Stop")
        self.stop_btn.setStyleSheet(StyleSheetCSV.STOP_BUTTON)
        self.stop_btn.clicked.connect(self.stop_playback)
        self.stop_btn.setEnabled(False)

        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.stop_btn)
        left_layout.addLayout(controls_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(StyleSheetCSV.PROGRESS_BAR)
        left_layout.addWidget(self.progress_bar)

        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(StyleSheetCSV.LABEL)
        self.status_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.status_label)
        
        left_layout.addStretch()
        
        # Right Panel - Frame Display
        self.frame_display = FrameDisplayWidget()
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 2)
        main_layout.addWidget(self.frame_display, 5)

    def load_events_csv(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Events CSV", "", "CSV Files (*.csv)")
        if filename:
            try:
                self.events_df = pd.read_csv(filename)
                self.events_df.columns = ['x', 'y', 'p', 't']
                self.events_label.setText(f"Events CSV: {filename.split('/')[-1]}")
                self.check_files_loaded()
            except Exception as e:
                self.status_label.setText(f"Error loading events CSV: {str(e)}")

    def load_labels_csv(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Labels CSV", "", "CSV Files (*.csv)")
        if filename:
            try:
                self.label_df = pd.read_csv(filename)
                self.labels_label.setText(f"Labels CSV: {filename.split('/')[-1]}")
                self.check_files_loaded()
            except Exception as e:
                self.status_label.setText(f"Error loading labels CSV: {str(e)}")

    def check_files_loaded(self):
        files_loaded = self.events_df is not None and self.label_df is not None
        self.play_btn.setEnabled(files_loaded)
        if files_loaded:
            self.current_frame_index = 0
            self.progress_bar.setMaximum(len(self.label_df))
            self.progress_bar.setValue(0)

    def create_frame(self, events_df, gaze_x, gaze_y, h=720, w=1280):
        img = np.ones((h, w, 3), dtype=np.uint8) * 127

        # Plot events
        if len(events_df) > 0:
            events = events_df[['x', 'y', 'p']].values
            img[events[:, 1], events[:, 0], :] = 255 * events[:, 2][:, None]


        img = cv2.flip(img, 1)
        # Draw gaze point
        gaze_x = int(gaze_x * w / 1920)
        gaze_y = int(gaze_y * h / 1080)
        
        # Draw red circle for gaze point
        center = (gaze_x, gaze_y)
        color = (255, 0, 0)  # BGR format
        radius = 5
        thickness = -1  # Filled circle
        
        # Manual circle drawing
        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                if i*i + j*j <= radius*radius:
                    x, y = gaze_x + i, gaze_y + j
                    if 0 <= x < w and 0 <= y < h:
                        img[y, x] = color

        return img

    def toggle_playback(self):
        if not self.is_playing:
            self.start_playback()
        else:
            self.pause_playback()

    def start_playback(self):
        self.is_playing = True
        self.play_btn.setText("⏸ Pause")
        self.stop_btn.setEnabled(True)
        self.timer.start()

    def pause_playback(self):
        self.is_playing = False
        self.play_btn.setText("▶ Play")
        self.timer.stop()

    def stop_playback(self):
        self.is_playing = False
        self.play_btn.setText("▶ Play")
        self.timer.stop()
        self.current_frame_index = 0
        self.progress_bar.setValue(0)
        self.stop_btn.setEnabled(False)
        self.frame_display.clear()

    def next_frame(self):
        if self.current_frame_index >= len(self.label_df):
            self.stop_playback()
            return

        row = self.label_df.iloc[self.current_frame_index]
        timestamp = row['Timestamp_ms']
        
        events_window = self.events_df[
            (self.events_df['t'] >= timestamp - 33000) & 
            (self.events_df['t'] <= timestamp)
        ]

        frame = self.create_frame(events_window, row['X'], row['Y'])
        self.frame_display.update_frame(frame)
        
        self.progress_bar.setValue(self.current_frame_index + 1)
        self.current_frame_index += 1

    def open_converter(self):
        self.converter_window = CSVConverterWidget()
        self.converter_window.show()