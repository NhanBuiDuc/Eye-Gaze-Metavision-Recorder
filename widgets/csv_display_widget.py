from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFileDialog, QFrame, QProgressBar)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
import pandas as pd
import cv2
import numpy as np
from styles import StyleSheetMain
from widgets.csv_convert import CSVConverterWidget

class CSVAnalysisWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CSV Analysis Tool")
        self.setMinimumSize(800, 600)
        self.events_df = None
        self.label_df = None
        
        # Set window background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(StyleSheetMain.BACKGROUND_COLOR))
        self.setPalette(palette)
        
        self.setup_ui()

    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Add converter button at the top
        converter_btn = QPushButton("Open RAW to CSV Converter")
        converter_btn.setStyleSheet(StyleSheetMain.BUTTON)
        converter_btn.clicked.connect(self.open_converter)
        main_layout.addWidget(converter_btn)

        # File Selection Section
        file_frame = QFrame()
        file_frame.setStyleSheet(f"background-color: {StyleSheetMain.CARD_COLOR}; border-radius: 12px;")
        file_layout = QVBoxLayout(file_frame)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_icon = QLabel("📊")
        title_icon.setFont(QFont("", 20))
        title_label = QLabel("CSV Analysis")
        title_label.setStyleSheet(StyleSheetMain.TITLE_LABEL)
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        file_layout.addLayout(title_layout)

        # Events CSV Section
        events_layout = QHBoxLayout()
        self.events_label = QLabel("Events CSV: Not selected")
        self.events_label.setStyleSheet(StyleSheetMain.LABEL)
        self.load_events_btn = QPushButton("Load Events CSV")
        self.load_events_btn.setStyleSheet(StyleSheetMain.BUTTON)
        self.load_events_btn.clicked.connect(self.load_events_csv)
        events_layout.addWidget(self.events_label)
        events_layout.addWidget(self.load_events_btn)
        file_layout.addLayout(events_layout)

        # Labels CSV Section
        labels_layout = QHBoxLayout()
        self.labels_label = QLabel("Labels CSV: Not selected")
        self.labels_label.setStyleSheet(StyleSheetMain.LABEL)
        self.load_labels_btn = QPushButton("Load Labels CSV")
        self.load_labels_btn.setStyleSheet(StyleSheetMain.BUTTON)
        self.load_labels_btn.clicked.connect(self.load_labels_csv)
        labels_layout.addWidget(self.labels_label)
        labels_layout.addWidget(self.load_labels_btn)
        file_layout.addLayout(labels_layout)

        main_layout.addWidget(file_frame)

        # Analysis Section
        analysis_frame = QFrame()
        analysis_frame.setStyleSheet(f"background-color: {StyleSheetMain.CARD_COLOR}; border-radius: 12px;")
        analysis_layout = QVBoxLayout(analysis_frame)

        # Analysis Controls
        controls_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("Start Analysis")
        self.analyze_btn.setStyleSheet(StyleSheetMain.BUTTON)
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet(StyleSheetMain.STOP_BUTTON)
        self.stop_btn.clicked.connect(self.stop_analysis)
        self.stop_btn.setEnabled(False)

        controls_layout.addWidget(self.analyze_btn)
        controls_layout.addWidget(self.stop_btn)
        analysis_layout.addLayout(controls_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(StyleSheetMain.PROGRESS_BAR)
        analysis_layout.addWidget(self.progress_bar)

        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(StyleSheetMain.LABEL)
        self.status_label.setAlignment(Qt.AlignCenter)
        analysis_layout.addWidget(self.status_label)

        main_layout.addWidget(analysis_frame)

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
        self.analyze_btn.setEnabled(self.events_df is not None and self.label_df is not None)

    def create_frame(self, events_df, gaze_x, gaze_y, h=720, w=1280):
        img = np.ones((h, w, 3), dtype=np.uint8) * 127

        # Plot events
        if len(events_df) > 0:
            events = events_df[['x', 'y', 'p']].values
            img[events[:, 1], events[:, 0], :] = 255 * events[:, 2][:, None]

        # Draw gaze point
        gaze_x = int(gaze_x * w / 1920)
        gaze_y = int(gaze_y * h / 1080)
        cv2.circle(img, (gaze_x, gaze_y), 5, (0, 0, 255), -1)

        return img

    def start_analysis(self):
        if self.events_df is None or self.label_df is None:
            return

        self.analyze_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Analysis in progress...")

        # Initialize progress bar
        self.progress_bar.setMaximum(len(self.label_df))
        self.progress_bar.setValue(0)

        # Create visualization window
        cv2.namedWindow('Synchronization Check', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Synchronization Check', 1280, 720)

        for idx, row in enumerate(self.label_df.iterrows()):
            if not self.stop_btn.isEnabled():  # Check if stopped
                break

            timestamp = row[1]['Timestamp_ms']
            events_window = self.events_df[
                (self.events_df['t'] >= timestamp - 33000) & 
                (self.events_df['t'] <= timestamp)
            ]

            frame = self.create_frame(events_window, row[1]['X'], row[1]['Y'])
            cv2.imshow('Synchronization Check', frame)

            # Update progress
            self.progress_bar.setValue(idx + 1)

            key = cv2.waitKey(100)
            if key & 0xFF == ord('q'):
                break
            elif key & 0xFF == ord(' '):
                cv2.waitKey(0)

        cv2.destroyAllWindows()
        self.stop_analysis()

    def stop_analysis(self):
        self.analyze_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Analysis completed")
        cv2.destroyAllWindows()
        
    def open_converter(self):
        """Open the RAW to CSV converter window"""
        self.converter_window = CSVConverterWidget()
        self.converter_window.show()