import os
import sys
import yaml
import csv
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QFileDialog, QTextEdit, QGroupBox,
                           QGridLayout, QFrame, QSplitter, QMessageBox, QSpinBox,
                           QTabWidget, QScrollArea, QDialog)
from PyQt5.QtGui import QFont, QColor, QPalette, QImage, QPixmap
from PyQt5.QtCore import Qt, QSize
from file_set import FileSet
from event_display_window import EventDisplayWindow

class FileReaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_sets = []
        self.setup_ui()
    
    def setup_ui(self):
        # Set window properties
        self.setWindowTitle("Multi-Set Event Camera File Reader")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2D2D30;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 12px;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0086F0;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            QTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #3E3E42;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
            QGroupBox {
                border: 1px solid #3E3E42;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
                color: #E0E0E0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
            QTabWidget::pane {
                border: 1px solid #3E3E42;
                background-color: #2D2D30;
            }
            QTabBar::tab {
                background-color: #252526;
                color: #E0E0E0;
                border: 1px solid #3E3E42;
                border-bottom-color: #3E3E42;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 8ex;
                padding: 6px 12px;
            }
            QTabBar::tab:selected {
                background-color: #007ACC;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3E3E42;
            }
            QSpinBox {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #3E3E42;
                padding: 4px;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Create sets number selection
        set_selection_layout = QHBoxLayout()
        set_selection_layout.addWidget(QLabel("Number of Sets:"))
        
        self.set_spinner = QSpinBox()
        self.set_spinner.setMinimum(1)
        self.set_spinner.setMaximum(10)
        self.set_spinner.setValue(1)
        self.set_spinner.setFixedWidth(80)
        self.set_spinner.valueChanged.connect(self.update_sets)
        
        set_selection_layout.addWidget(self.set_spinner)
        set_selection_layout.addStretch()
        
        main_layout.addLayout(set_selection_layout)
        
        # Create tabs for file selection
        self.file_tabs = QTabWidget()
        main_layout.addWidget(self.file_tabs)
        
        # Add analyze button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.analyze_btn = QPushButton("Analyze All Sets")
        self.analyze_btn.setFixedSize(200, 40)
        self.analyze_btn.clicked.connect(self.analyze_files)
        self.analyze_btn.setDisabled(True)
        
        button_layout.addWidget(self.analyze_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Create content area with tabs
        self.content_tabs = QTabWidget()
        main_layout.addWidget(self.content_tabs, 1)  # Give content area more stretch
        
        # Add "Show Parallel" button
        parallel_button_layout = QHBoxLayout()
        parallel_button_layout.addStretch()
        
        self.parallel_btn = QPushButton("Show Parallel")
        self.parallel_btn.setFixedSize(200, 40)
        self.parallel_btn.clicked.connect(self.show_parallel_windows)
        self.parallel_btn.setDisabled(True)
        
        parallel_button_layout.addWidget(self.parallel_btn)
        parallel_button_layout.addStretch()
        main_layout.addLayout(parallel_button_layout)
        
        self.setCentralWidget(central_widget)
        
        # Status bar
        self.statusBar().showMessage("Ready. Please configure sets and select files.")
        
        # Keep track of parallel windows
        self.parallel_windows = []
        
        # Initialize with one set
        self.update_sets(1)
    
    def update_sets(self, num_sets):
        # Clear existing tabs
        self.file_tabs.clear()
        
        # Adjust file sets list
        old_len = len(self.file_sets)
        
        # Keep existing sets if reducing number
        if num_sets < old_len:
            self.file_sets = self.file_sets[:num_sets]
        
        # Add new sets if increasing number
        for i in range(old_len, num_sets):
            self.file_sets.append(FileSet(i))
        
        # Create tabs for each set
        for i, file_set in enumerate(self.file_sets):
            self.create_file_selection_tab(file_set, i)
        
        # Reset analyze button state
        self.check_all_files_selected()
    
    def create_file_selection_tab(self, file_set, index):
        # Create tab for this set
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create file selection section
        file_group = QGroupBox(f"File Selection for Set {index+1}")
        file_layout = QGridLayout()
        
        # YAML file selection
        yaml_label = QLabel("YAML Config File:")
        file_set.yaml_path_label = QLabel("No file selected")
        file_set.yaml_path_label.setStyleSheet("color: #888888; font-style: italic;")
        yaml_btn = QPushButton("Select YAML File")
        yaml_btn.clicked.connect(lambda: self.select_yaml_file(file_set))
        
        file_layout.addWidget(yaml_label, 0, 0)
        file_layout.addWidget(file_set.yaml_path_label, 0, 1)
        file_layout.addWidget(yaml_btn, 0, 2)
        
        # CSV file selection
        csv_label = QLabel("CSV Label File:")
        file_set.csv_path_label = QLabel("No file selected")
        file_set.csv_path_label.setStyleSheet("color: #888888; font-style: italic;")
        csv_btn = QPushButton("Select CSV File")
        csv_btn.clicked.connect(lambda: self.select_csv_file(file_set))
        
        file_layout.addWidget(csv_label, 1, 0)
        file_layout.addWidget(file_set.csv_path_label, 1, 1)
        file_layout.addWidget(csv_btn, 1, 2)
        
        # RAW file selection
        raw_label = QLabel("RAW Event File:")
        file_set.raw_path_label = QLabel("No file selected")
        file_set.raw_path_label.setStyleSheet("color: #888888; font-style: italic;")
        raw_btn = QPushButton("Select RAW File")
        raw_btn.clicked.connect(lambda: self.select_raw_file(file_set))
        
        file_layout.addWidget(raw_label, 2, 0)
        file_layout.addWidget(file_set.raw_path_label, 2, 1)
        file_layout.addWidget(raw_btn, 2, 2)
        
        # Set column stretching
        file_layout.setColumnStretch(1, 1)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Add the tab
        self.file_tabs.addTab(tab, f"Set {index+1}")
    
    def select_yaml_file(self, file_set):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select YAML Config File for Set {file_set.index+1}", "", "YAML Files (*.yaml *.yml)"
        )
        
        if file_path:
            file_set.yaml_path = file_path
            file_set.yaml_path_label.setText(os.path.basename(file_path))
            file_set.yaml_path_label.setStyleSheet("color: #00AA00;")
            self.check_all_files_selected()
    
    def select_csv_file(self, file_set):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select CSV Label File for Set {file_set.index+1}", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            file_set.csv_path = file_path
            file_set.csv_path_label.setText(os.path.basename(file_path))
            file_set.csv_path_label.setStyleSheet("color: #00AA00;")
            self.check_all_files_selected()
    
    def select_raw_file(self, file_set):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select RAW Event File for Set {file_set.index+1}", "", "RAW Files (*.raw)"
        )
        
        if file_path:
            file_set.raw_path = file_path
            file_set.raw_path_label.setText(os.path.basename(file_path))
            file_set.raw_path_label.setStyleSheet("color: #00AA00;")
            self.check_all_files_selected()
    
    def check_all_files_selected(self):
        all_selected = True
        
        for file_set in self.file_sets:
            if not (file_set.yaml_path and file_set.csv_path and file_set.raw_path):
                all_selected = False
                break
        
        self.analyze_btn.setEnabled(all_selected)
        
        if all_selected:
            self.statusBar().showMessage("All files selected. Click 'Analyze All Sets' to proceed.")
        else:
            self.statusBar().showMessage("Please select all required files for each set.")
    
    def read_yaml_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                yaml_data = yaml.safe_load(file)
                
                # Format the output for display
                output = "YAML file loaded successfully\n\n"
                output += f"Label mode: {yaml_data.get('label_mode', 'N/A')}\n\n"
                
                if 'files' in yaml_data:
                    output += "Files referenced:\n"
                    for key, value in yaml_data['files'].items():
                        output += f"  • {key}: {value}\n"
                    output += "\n"
                
                if 'recording' in yaml_data:
                    output += "Recording settings:\n"
                    for key, value in yaml_data['recording'].items():
                        output += f"  • {key}: {value}\n"
                    output += "\n"
                    
                if 'display' in yaml_data and 'roi' in yaml_data['display']:
                    roi = yaml_data['display']['roi']
                    output += f"Region of Interest:\n"
                    output += f"  • X: {roi[0]}\n"
                    output += f"  • Y: {roi[1]}\n"
                    output += f"  • Width: {roi[2]}\n"
                    output += f"  • Height: {roi[3]}\n\n"
                
                if 'states' in yaml_data:
                    output += "States:\n"
                    for key, value in yaml_data['states'].items():
                        output += f"  • {key}: {value}\n"
                
                return output, yaml_data
        except Exception as e:
            return f"Error reading YAML file:\n{str(e)}", None
    
    def read_csv_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                csv_reader = csv.reader(file)
                headers = next(csv_reader)  # Get header row
                
                # Read all rows into a list
                rows = list(csv_reader)
                
                # Format the output for display
                output = f"CSV file loaded successfully\n\n"
                output += f"Headers:\n{', '.join(headers)}\n\n"
                output += f"Total rows: {len(rows)}\n\n"
                
                # Display first 10 rows as example
                if rows:
                    output += "Sample data (first 10 rows):\n"
                    for i, row in enumerate(rows[:10]):
                        output += f"Row {i+1}: {', '.join(row)}\n"
                
                return output, headers, rows
        except Exception as e:
            return f"Error reading CSV file:\n{str(e)}", None, None
    
    def read_raw_file(self, file_path):
        try:
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Read first 256 bytes as a sample for display
            with open(file_path, 'rb') as file:
                sample = file.read(256)
                
                # Read more data for later visualization (up to 1MB)
                file.seek(0)
                raw_data = file.read(min(1024*1024, file_size))  # Read up to 1MB for event data
            
            # Format the output for display
            output = f"RAW file loaded successfully\n\n"
            output += f"File path: {file_path}\n\n"
            output += f"File size: {file_size} bytes ({file_size/1024/1024:.2f} MB)\n\n"
            
            # Format hex dump
            output += "Hex dump (first 256 bytes):\n"
            
            hex_dump = ""
            ascii_dump = ""
            
            for i, byte in enumerate(sample):
                # Add address at the beginning of each line
                if i % 16 == 0:
                    if i > 0:
                        output += f"  {hex_dump}  |{ascii_dump}|\n"
                        hex_dump = ""
                        ascii_dump = ""
                    output += f"{i:04x}: "
                
                # Add hex representation
                hex_dump += f"{byte:02x} "
                
                # Add ASCII representation (if printable)
                if 32 <= byte <= 126:
                    ascii_dump += chr(byte)
                else:
                    ascii_dump += "."
            
            # Add the last line if it's not complete
            if hex_dump:
                # Pad hex_dump to align the ASCII part
                hex_dump = hex_dump.ljust(16*3)
                output += f"  {hex_dump}  |{ascii_dump}|\n"
            
            # Return the raw data for later use
            return output, file_size, raw_data
        except Exception as e:
            return f"Error reading RAW file:\n{str(e)}", None, None
    
    def create_raw_visualization(self, data, width=320, height=240):
        """Create a simple visualization of the RAW data as a binary image"""
        # This is a sample visualization only
        # In a real application, you would need to parse the actual event camera format
        # This creates a binary image where pixels are either on or off
        
        # Create a simple binary image from the data 
        # (threshold raw bytes to create binary values)
        np_data = np.frombuffer(data, dtype=np.uint8)
        
        # Resize to specified dimensions, or use defaults
        if len(np_data) < width * height:
            np_data = np.pad(np_data, (0, width * height - len(np_data)), 'constant')
        else:
            np_data = np_data[:width * height]
            
        # Reshape to 2D
        np_data = np_data.reshape(height, width)
        
        # Threshold to binary (0 or 255)
        binary_data = (np_data > 127).astype(np.uint8) * 255
        
        # Create QImage from the array
        image = QImage(binary_data.data, width, height, width, QImage.Format_Grayscale8)
        
        return QPixmap.fromImage(image)
    
    def analyze_files(self):
        self.statusBar().showMessage("Analyzing files...")
        
        # Clear previous content tabs
        self.content_tabs.clear()
        
        # Process each file set
        for file_set in self.file_sets:
            # Read files for this set
            yaml_text, file_set.yaml_data = self.read_yaml_file(file_set.yaml_path)
            csv_text, file_set.csv_headers, file_set.csv_rows = self.read_csv_file(file_set.csv_path)
            raw_text, file_set.raw_size, file_set.raw_data = self.read_raw_file(file_set.raw_path)
            
            # Create content tab for this set
            set_tab = QWidget()
            set_layout = QHBoxLayout(set_tab)
            
            # Create a splitter for the content panels
            content_splitter = QSplitter(Qt.Horizontal)
            
            # YAML content
            yaml_group = QGroupBox("YAML Configuration")
            yaml_layout = QVBoxLayout()
            yaml_text_edit = QTextEdit()
            yaml_text_edit.setReadOnly(True)
            yaml_text_edit.setText(yaml_text)
            yaml_layout.addWidget(yaml_text_edit)
            yaml_group.setLayout(yaml_layout)
            
            # CSV content
            csv_group = QGroupBox("CSV Labels")
            csv_layout = QVBoxLayout()
            csv_text_edit = QTextEdit()
            csv_text_edit.setReadOnly(True)
            csv_text_edit.setText(csv_text)
            csv_layout.addWidget(csv_text_edit)
            csv_group.setLayout(csv_layout)
            
            # RAW content (text only)
            raw_group = QGroupBox("RAW File Info")
            raw_layout = QVBoxLayout()
            
            # Add text info
            raw_text_edit = QTextEdit()
            raw_text_edit.setReadOnly(True)
            raw_text_edit.setText(raw_text)
            raw_layout.addWidget(raw_text_edit)
            
            raw_group.setLayout(raw_layout)
            
            # Add content groups to splitter
            content_splitter.addWidget(yaml_group)
            content_splitter.addWidget(csv_group)
            content_splitter.addWidget(raw_group)
            content_splitter.setSizes([300, 300, 400])  # Give RAW view a bit more space
            
            set_layout.addWidget(content_splitter)
            
            # Add the tab for this set
            self.content_tabs.addTab(set_tab, f"Set {file_set.index+1}")
        
        # Check if all files were read successfully
        success = all(fs.yaml_data and fs.csv_headers and fs.raw_size for fs in self.file_sets)
        
        if success:
            self.statusBar().showMessage("All files analyzed successfully.")
            
            # Enable the Show Parallel button
            self.parallel_btn.setEnabled(True)
            
            # Show success message
            QMessageBox.information(
                self, 
                "Analysis Complete", 
                "All files across all sets were loaded and analyzed successfully!"
            )
        else:
            self.statusBar().showMessage("Error analyzing some files. See details in the panels.")
            
            # Disable the Show Parallel button
            self.parallel_btn.setDisabled(True)
            
            # Show error message
            QMessageBox.warning(
                self, 
                "Analysis Issues", 
                "There were problems analyzing one or more files. Please check the details."
            )
    
    def show_parallel_windows(self):
        """Show parallel windows for each set with binary image and labels"""
        # Close any existing windows
        for window in self.parallel_windows:
            window.close()
        
        self.parallel_windows = []
        
        # Create new windows for each set
        for file_set in self.file_sets:
            # Only create windows for sets with valid data
            if file_set.raw_data and file_set.csv_headers and file_set.csv_rows:
                # Create window with binary image and CSV data
                from event_display_window import EventDisplayWindow
                window = EventDisplayWindow(
                    file_set.index,
                    file_set.raw_data,
                    (file_set.csv_headers, file_set.csv_rows),
                    self
                )
                
                # Position windows in cascade
                window_pos_x = 100 + (file_set.index * 50)
                window_pos_y = 100 + (file_set.index * 50)
                window.move(window_pos_x, window_pos_y)
                
                window.show()
                self.parallel_windows.append(window)
        
        if not self.parallel_windows:
            QMessageBox.warning(
                self,
                "No Data",
                "No valid data sets to display in parallel windows."
            )