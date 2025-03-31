import sys
import csv
import yaml
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                            QVBoxLayout, QWidget, QFileDialog, QLabel,
                            QTextEdit, QHBoxLayout, QGroupBox, QMessageBox,
                            QSplitter, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette
from metavision_core.event_io import EventsIterator
from metavision_core.event_io.raw_reader import initiate_device
from metavision_sdk_ui import EventLoop
from metavision_sdk_core import PeriodicFrameGenerationAlgorithm, ColorPalette
import pandas as pd
import numpy as np
class FileReaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Reader")
        self.setGeometry(100, 100, 900, 700)
        
        # File paths
        self.yaml_path = ""
        self.csv_path = ""
        self.raw_path = ""
        self.delta_t = 33333
        self.device = None
        # File data
        self.yaml_data = None
        self.csv_data = None
        
        self.initUI()
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
            QPushButton:pressed {
                background-color: #2a66c8;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QLabel {
                padding: 4px;
            }
        """)
        
    def initUI(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # File selection section
        file_group = QGroupBox("File Selection")
        file_layout = QHBoxLayout()
        
        # YAML file selection
        yaml_layout = QVBoxLayout()
        self.yaml_btn = QPushButton("Select YAML File")
        self.yaml_btn.setMinimumHeight(40)
        self.yaml_btn.clicked.connect(self.select_yaml_file)
        self.yaml_label = QLabel("No file selected")
        self.yaml_label.setStyleSheet("background-color: #f0f0f0; border-radius: 3px;")
        self.yaml_label.setAlignment(Qt.AlignCenter)
        yaml_layout.addWidget(self.yaml_btn)
        yaml_layout.addWidget(self.yaml_label)
        
        # CSV file selection
        csv_layout = QVBoxLayout()
        self.csv_btn = QPushButton("Select CSV File")
        self.csv_btn.setMinimumHeight(40)
        self.csv_btn.clicked.connect(self.select_csv_file)
        self.csv_label = QLabel("No file selected")
        self.csv_label.setStyleSheet("background-color: #f0f0f0; border-radius: 3px;")
        self.csv_label.setAlignment(Qt.AlignCenter)
        csv_layout.addWidget(self.csv_btn)
        csv_layout.addWidget(self.csv_label)
        
        # RAW file selection
        raw_layout = QVBoxLayout()
        self.raw_btn = QPushButton("Select RAW File")
        self.raw_btn.setMinimumHeight(40)
        self.raw_btn.clicked.connect(self.select_raw_file)
        self.raw_label = QLabel("No file selected")
        self.raw_label.setStyleSheet("background-color: #f0f0f0; border-radius: 3px;")
        self.raw_label.setAlignment(Qt.AlignCenter)
        raw_layout.addWidget(self.raw_btn)
        raw_layout.addWidget(self.raw_label)
        
        # Add file selection layouts to file group
        file_layout.addLayout(yaml_layout)
        file_layout.addLayout(csv_layout)
        file_layout.addLayout(raw_layout)
        file_group.setLayout(file_layout)
        
        # Display area for file contents
        content_group = QGroupBox("File Contents")
        content_layout = QVBoxLayout()
        
        self.display_area = QTextEdit()
        self.display_area.setReadOnly(True)
        self.display_area.setLineWrapMode(QTextEdit.NoWrap)
        
        # Use a better font for the display area
        font = QFont("Consolas", 10)
        self.display_area.setFont(font)
        
        content_layout.addWidget(self.display_area)
        content_group.setLayout(content_layout)
        
        # Load file button
        self.load_btn = QPushButton("Load Selected Files")
        self.load_btn.setMinimumHeight(50)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.load_btn.clicked.connect(self.load_files)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Add widgets to main layout
        main_layout.addWidget(file_group)
        main_layout.addWidget(self.load_btn)
        main_layout.addWidget(content_group, 1)  # Give this more space

        # Add this to the initUI method after creating the load_btn
        self.sync_btn = QPushButton("Synchronize")
        self.sync_btn.setMinimumHeight(50)
        self.sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
        """)
        self.sync_btn.clicked.connect(self.synchronize_files)

        # Add this to main_layout after adding the load_btn
        main_layout.addWidget(self.sync_btn)

        # Set main layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    # Add this method to the class
    def synchronize_files(self):
        """
        Function to synchronize the loaded files
        This is currently empty and can be implemented as needed
        """
        # This is an empty function that will be called when the Synchronize button is pressed
        self.statusBar().showMessage("Synchronization initiated...", 3000)
        starting_ts = self.yaml_data['recording']['starting_timestamp']
        # Initialize index
        label_index = 0
        current_label_row = self.csv_data.iloc[label_index]  # Get the current row
        
        # Extract values from the current row
        current_label_timestamp_ms = current_label_row["Timestamp_ms"]
        current_label_point_index = current_label_row["Point_Index"]
        print("current_label_point_index", current_label_point_index)
        current_label_x = current_label_row["X"]
        current_label_y = current_label_row["Y"]
        next_x = current_label_row["Next_X"]
        next_y = current_label_row["Next_Y"]

        screen_width = current_label_row["Screen_Width"]
        screen_height = current_label_row["Screen_Height"]

        current_timestamp_starting_range = current_label_timestamp_ms - self.delta_t
        current_timestamp_ending_range = current_label_timestamp_ms + self.delta_t

        # Your synchronization logic will go here
        for evs in self.mv_iterator:
            timestamps = evs["t"] + starting_ts
            # Create a boolean mask for events within the time range
            in_range_mask = (timestamps >= current_timestamp_starting_range) & (timestamps <= current_timestamp_ending_range)
            # Filter the batch using the mask
            in_range_batch = evs[in_range_mask]
            if len(in_range_batch) > 0:
                # Write the filtered events to CSV with the current screen coordinates
                self.write_events_to_csv(
                    in_range_batch,
                    screen_x=current_label_x,
                    screen_y=current_label_y,
                    screen_ts=current_label_timestamp_ms,
                    starting_ts = starting_ts,
                    filename="synchronized_data.csv"
                )
            next_ts_inspect_mask = timestamps >= current_timestamp_ending_range
            if np.any(next_ts_inspect_mask):
                label_index += 1
                current_label_row = self.csv_data.iloc[label_index]  # Get the current row
                current_label_timestamp_ms = current_label_row["Timestamp_ms"]
                current_timestamp_starting_range = current_label_timestamp_ms - self.delta_t
                current_timestamp_ending_range = current_label_timestamp_ms + self.delta_t
                current_label_point_index = current_label_row["Point_Index"]
                print("current_label_point_index", current_label_point_index)

    def write_events_to_csv(self, in_range_batch, screen_x, screen_y, screen_ts, starting_ts, filename="synchronized_events.csv"):
        # Check if file exists
        file_exists = os.path.isfile(filename)
        
        # Create a DataFrame from the numpy structured array
        df = pd.DataFrame(in_range_batch)
        
        # Add screen information columns (same value for all rows)
        df['screen_x'] = screen_x
        df['screen_y'] = screen_y
        df['screen_ts'] = screen_ts
        
        # Rename columns if needed to match your desired output format
        # If your NumPy array already has 'x', 'y', 'p', 't' columns
        column_mapping = {
            'x': 'event_x',
            'y': 'event_y',
            'p': 'event_p',
            't': 'event_ts'
        }
        df = df.rename(columns=column_mapping)
        
        # Ensure timestamps include starting_ts if needed
        if 'event_ts' in df.columns:
            df['event_ts'] = df['event_ts'] + starting_ts
        
        # Write to CSV
        mode = 'a' if file_exists else 'w'
        header = not file_exists
        df.to_csv(filename, mode=mode, header=header, index=False)

    def select_yaml_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select YAML File", "", "YAML Files (*.yaml *.yml)")
        if file_path:
            self.yaml_path = file_path
            self.yaml_label.setText(os.path.basename(file_path))
            self.yaml_label.setStyleSheet("background-color: #e6f7ff; border-radius: 3px; border: 1px solid #91d5ff;")
            self.statusBar().showMessage(f"YAML file selected: {file_path}", 3000)
    
    def select_csv_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if file_path:
            self.csv_path = file_path
            self.csv_label.setText(os.path.basename(file_path))
            self.csv_label.setStyleSheet("background-color: #e6f7ff; border-radius: 3px; border: 1px solid #91d5ff;")
            self.statusBar().showMessage(f"CSV file selected: {file_path}", 3000)
    
    def select_raw_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select RAW File", "", "RAW Files (*.raw)")
        if file_path:
            self.raw_path = file_path
            self.raw_label.setText(os.path.basename(file_path))
            self.raw_label.setStyleSheet("background-color: #e6f7ff; border-radius: 3px; border: 1px solid #91d5ff;")
            self.statusBar().showMessage(f"RAW file selected: {file_path}", 3000)
            self.device = initiate_device(self.raw_path)
            self.mv_iterator = EventsIterator.from_device(self.device, delta_t=self.delta_t, start_ts=0)

    def load_files(self):
        self.display_area.clear()
        loaded_files = []
        
        # Load YAML file
        if self.yaml_path:
            try:
                with open(self.yaml_path, 'r') as file:
                    self.yaml_data = yaml.safe_load(file)
                self.display_area.append("=== YAML FILE CONTENTS ===")
                self.display_area.append(str(self.yaml_data))
                self.display_area.append("\n")
                loaded_files.append("YAML")
            except Exception as e:
                self.display_area.append(f"Error loading YAML file: {str(e)}\n")
        
        # Load CSV file
        if self.csv_path:
            try:
                # Read CSV using pandas
                self.csv_data = pd.read_csv(self.csv_path)

                self.display_area.append("=== CSV FILE CONTENTS ===")
                self.display_area.append(self.csv_data.to_string(index=False))  # Convert DataFrame to string
                self.display_area.append("\n")
                loaded_files.append("CSV")
            except Exception as e:
                self.display_area.append(f"Error loading CSV file: {str(e)}\n")
        
        # Handle RAW file - just store the path, don't display content
        if self.raw_path:
            try:
                # Just verify the file exists and is readable
                with open(self.raw_path, 'rb') as file:
                    pass
                
                self.display_area.append("=== RAW FILE INFO ===")
                self.display_area.append(f"File: {os.path.basename(self.raw_path)}")
                self.display_area.append(f"Path: {self.raw_path}")
                self.display_area.append(f"Size: {os.path.getsize(self.raw_path)} bytes")
                self.display_area.append("Raw file content not displayed, but path is saved for processing.")
                self.display_area.append("\n")
                loaded_files.append("RAW")
            except Exception as e:
                self.display_area.append(f"Error checking RAW file: {str(e)}\n")
        
        # Update status
        if loaded_files:
            self.statusBar().showMessage(f"Loaded files: {', '.join(loaded_files)}", 5000)
            # Show a confirmation message box
            QMessageBox.information(self, "Files Loaded", 
                                    f"Successfully loaded: {', '.join(loaded_files)} files.")
        else:
            self.statusBar().showMessage("No files were loaded", 5000)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FileReaderApp()
    window.show()
    sys.exit(app.exec_())