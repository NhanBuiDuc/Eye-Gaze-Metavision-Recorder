import os
import sys
import yaml
import csv
import numpy as np
import cv2
import time
from threading import Thread
from PyQt5.QtGui import QFont, QColor, QPalette, QImage, QPixmap
from PyQt5.QtCore import Qt, QSize
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
from event_display_widget import EventDisplayWidget

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from metavision_sdk_core import PeriodicFrameGenerationAlgorithm, ColorPalette
from metavision_core.event_io import EventsIterator
from metavision_core.event_io.raw_reader import initiate_device
from metavision_sdk_ui import EventLoop
from metavision_sdk_core import PeriodicFrameGenerationAlgorithm, ColorPalette

class EventDisplayWindow(QDialog):
    """Window to display event data with labels side by side"""
    def __init__(self, set_index, raw_data, csv_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Event Display - Set {set_index+1}")
        self.setMinimumSize(1000, 600)
        
        # Store raw data and csv data
        self.raw_data = raw_data
        self.csv_data = csv_data
        
        # Frame navigation parameters
        self.current_frame_index = 0
        self.frame_step_ns = 10000  # 10,000 nanoseconds per step
        self.frame_width = 320  # Default frame width
        self.frame_height = 240  # Default frame height
        
        # Initialize with current point information
        self.current_point = None
        self.next_point = None
        
        # Label data for processing
        self.label_data = []
        self.current_frame_timestamp = 0
        self.event_window_before = 5000000  # 5ms window before timestamp
        
        # Extract label data from CSV
        self.extract_label_data_from_csv()
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Top part - Image and labels side by side
        top_layout = QHBoxLayout()
        
        # Left side - RAW binary image with EventDisplayWidget
        image_group = QGroupBox("Event Binary Image")
        image_layout = QVBoxLayout()
        
        # Create display widget for binary image
        self.display_widget = EventDisplayWidget()
        
        # Create initial binary image from raw data
        if raw_data:
            frame = self.create_binary_image(raw_data, self.frame_width, self.frame_height)
            self.display_widget.update_frame(frame)
            
            # Find and display closest label point to current frame
            timestamp = self.current_frame_index * self.frame_step_ns
            closest_point = self.find_closest_label_point(timestamp)
            if closest_point:
                self.draw_label_point(closest_point)
                
        image_layout.addWidget(self.display_widget)
        image_group.setLayout(image_layout)
        
        # Right side - CSV labels
        label_group = QGroupBox("Event Labels")
        label_layout = QVBoxLayout()
        
        # Display CSV labels
        self.labels_text = QTextEdit()
        self.labels_text.setReadOnly(True)
        
        self.update_label_display()
        
        label_layout.addWidget(self.labels_text)
        label_group.setLayout(label_layout)
        
        # Add both panels to top layout
        top_layout.addWidget(image_group, 3)  # More space for the image
        top_layout.addWidget(label_group, 2)
        
        # Navigation controls at the bottom
        nav_layout = QHBoxLayout()
        
        self.timestamp_label = QLabel("Frame Index: 0")
        self.timestamp_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.prev_button = QPushButton("◀ Previous Frame")
        self.prev_button.setStyleSheet("""
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
        """)
        self.prev_button.clicked.connect(self.show_previous_frame)
        
        self.next_button = QPushButton("Next Frame ▶")
        self.next_button.setStyleSheet("""
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
        """)
        self.next_button.clicked.connect(self.show_next_frame)
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.timestamp_label)
        nav_layout.addWidget(self.next_button)
        
        # Add layouts to main layout
        layout.addLayout(top_layout)
        layout.addLayout(nav_layout)
        
        # Initialize display
        self.update_display()
    
    def extract_label_data_from_csv(self):
        """Extract label data from CSV into format similar to RawViewerApp"""
        self.label_data = []
        
        if self.csv_data and len(self.csv_data) >= 2:
            headers, rows = self.csv_data
            
            if not rows:
                return
                
            # Find column indices
            x_idx = -1
            y_idx = -1
            next_x_idx = -1
            next_y_idx = -1
            timestamp_idx = -1
            point_index_idx = -1
            
            for i, header in enumerate(headers):
                header_upper = header.upper()
                if header_upper == 'X':
                    x_idx = i
                elif header_upper == 'Y':
                    y_idx = i
                elif header_upper == 'NEXT_X':
                    next_x_idx = i
                elif header_upper == 'NEXT_Y':
                    next_y_idx = i
                elif 'TIMESTAMP' in header_upper:
                    timestamp_idx = i
                elif 'POINT' in header_upper and 'INDEX' in header_upper:
                    point_index_idx = i
            
            # Process rows
            for row in rows:
                if len(row) > max(x_idx, y_idx) and x_idx >= 0 and y_idx >= 0:
                    point_data = {
                        'x': int(row[x_idx]) if row[x_idx] else 0,
                        'y': int(row[y_idx]) if row[y_idx] else 0,
                        'next_x': int(row[next_x_idx]) if next_x_idx >= 0 and next_x_idx < len(row) and row[next_x_idx] else None,
                        'next_y': int(row[next_y_idx]) if next_y_idx >= 0 and next_y_idx < len(row) and row[next_y_idx] else None,
                        'timestamp': int(row[timestamp_idx]) if timestamp_idx >= 0 and timestamp_idx < len(row) and row[timestamp_idx] else 0,
                        'point_index': int(row[point_index_idx]) if point_index_idx >= 0 and point_index_idx < len(row) and row[point_index_idx] else 0
                    }
                    self.label_data.append(point_data)
    
    def update_label_display(self):
        """Update the label text display"""
        if self.csv_data and len(self.csv_data) >= 2:
            headers, rows = self.csv_data
            
            text = "Event Labels:\n\n"
            text += f"Headers: {', '.join(headers)}\n\n"
            
            for i, row in enumerate(rows[:20]):  # Show first 20 rows
                prefix = "➤ " if i == self.current_frame_index % min(20, len(rows)) else "  "
                text += f"{prefix}Event {i+1}: {', '.join(row)}\n"
                
            if len(rows) > 20:
                text += f"\n... and {len(rows) - 20} more events"
                
            self.labels_text.setText(text)
        else:
            self.labels_text.setText("No CSV data available")
    
    def find_closest_label_point(self, timestamp):
        """Find the closest label point to the given timestamp"""
        if not self.label_data:
            return None
            
        closest_point = None
        min_diff = float('inf')
        
        for point in self.label_data:
            diff = abs(point['timestamp'] - timestamp)
            if diff < min_diff:
                min_diff = diff
                closest_point = point
                
        return closest_point
    
    def draw_label_point(self, point_data):
        """Draw the label point on a separate window and update display widget"""
        if not point_data:
            return
            
        # Create a white canvas (1920x1080)
        canvas = np.ones((1080, 1920, 3), dtype=np.uint8) * 255
        
        x, y = point_data['x'], point_data['y']
        
        # Draw the current point as a red circle
        cv2.circle(canvas, (x, y), 10, (0, 0, 255), -1)
        
        # Draw next point and connecting line if available
        if point_data['next_x'] is not None and point_data['next_y'] is not None:
            next_x, next_y = point_data['next_x'], point_data['next_y']
            cv2.circle(canvas, (next_x, next_y), 6, (0, 255, 0), -1)
            cv2.line(canvas, (x, y), (next_x, next_y), (255, 0, 0), 2)
            
        # Display point information
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(canvas, f"Point {point_data['point_index']} ({x}, {y})", 
                (50, 50), font, 1, (0, 0, 0), 2)
        cv2.putText(canvas, f"Timestamp: {point_data['timestamp']}", 
                (50, 80), font, 1, (0, 0, 0), 2)
        cv2.putText(canvas, f"Frame: {self.current_frame_index} (Time: {self.current_frame_index * self.frame_step_ns} ns)",
                (50, 110), font, 1, (0, 0, 0), 2)
        
        # Resize to 1280x720 for display
        resized = cv2.resize(canvas, (1280, 720))
        cv2.imshow(f"Label Points - Set {self.windowTitle().split(' ')[-1]}", resized)
        cv2.waitKey(1)
        
        # Update the point in the display widget
        self.display_widget.set_current_point(
            (x, y),
            (point_data['next_x'], point_data['next_y']) if point_data['next_x'] is not None else None
        )
    
    def create_binary_image(self, data, width, height):
        """Create a binary image from raw data with frame index offset"""
        # Get data slice based on frame index (each frame advances by frame_step_ns)
        offset = min(len(data) - 1, self.current_frame_index * self.frame_step_ns)
        data_slice = data[offset:offset + width * height]
        
        # Pad if necessary
        if len(data_slice) < width * height:
            data_padded = data_slice + bytes([0] * (width * height - len(data_slice)))
        else:
            data_padded = data_slice[:width * height]
            
        # Convert to numpy, reshape, and threshold
        np_data = np.frombuffer(data_padded, dtype=np.uint8).reshape(height, width)
        binary_data = (np_data > 127).astype(np.uint8) * 255
        
        return binary_data  # Return numpy array for EventDisplayWidget
    
    def show_previous_frame(self):
        """Show the previous frame by decreasing the frame index"""
        if self.current_frame_index > 0:
            self.current_frame_index -= 1
            self.update_display()
    
    def show_next_frame(self):
        """Show the next frame by increasing the frame index"""
        max_frames = max(1, len(self.raw_data) // self.frame_step_ns)
        if self.current_frame_index < max_frames - 1:
            self.current_frame_index += 1
            self.update_display()
    
    def update_display(self):
        """Update the display with the current frame"""
        # Update frame
        if self.raw_data:
            frame = self.create_binary_image(self.raw_data, self.frame_width, self.frame_height)
            self.display_widget.update_frame(frame)
        
        # Update timestamp label
        time_ns = self.current_frame_index * self.frame_step_ns
        self.timestamp_label.setText(f"Frame Index: {self.current_frame_index} (Time: {time_ns} ns)")
        
        # Find and display closest label point
        closest_point = self.find_closest_label_point(time_ns)
        if closest_point:
            self.draw_label_point(closest_point)
        
        # Update label display to highlight current frame
        self.update_label_display()
        
        # Enable/disable navigation buttons
        self.prev_button.setEnabled(self.current_frame_index > 0)
        max_frames = max(1, len(self.raw_data) // self.frame_step_ns) if self.raw_data else 1
        self.next_button.setEnabled(self.current_frame_index < max_frames - 1)
    
    def closeEvent(self, event):
        """Close OpenCV windows when the dialog is closed"""
        cv2.destroyAllWindows()
        super().closeEvent(event)


    def start_playback_at_timestamp(self, start_timestamp):
        if not self.current_file or not os.path.exists(self.current_file):
            return
        
        try:
            self.device = initiate_device(self.current_file)
            
            delta_t = 33333
            start_ts_rounded = (start_timestamp // delta_t) * delta_t
            
            self.mv_iterator = EventsIterator.from_device(self.device, delta_t=delta_t, start_ts=0)
            self.current_frame_timestamp = start_ts_rounded
            
            self.bias_supported = False
            if hasattr(self.device, 'get_i_ll_biases'):
                biases = self.device.get_i_ll_biases()
                if biases is not None:
                    self.bias_supported = True
                    for name, bias in self.bias_widget.bias_settings.biases.items():
                        try:
                            biases.set(name, bias.value)
                            print(f"Applied initial bias {name} = {bias.value}")
                        except Exception as e:
                            print(f"Warning: Could not set bias {name}: {e}")
            
            if self.bias_supported:
                self.bias_status_label.setText("Bias controls enabled for this file")
                self.bias_status_label.setStyleSheet("color: #388E3C; font-style: italic;")
                self.bias_update_timer.start(100)
            else:
                self.bias_status_label.setText("Bias controls not supported for this file")
                self.bias_status_label.setStyleSheet("color: #D32F2F; font-style: italic;")
            
            height, width = self.mv_iterator.get_size()
            print(f"Camera dimensions: {width}x{height}")
            
            self.event_frame_gen = PeriodicFrameGenerationAlgorithm(
                sensor_width=width,
                sensor_height=height,
                fps=30,
                palette=ColorPalette.Gray
            )
            
            def on_cd_frame_cb(ts, cd_frame):
                try:
                    frame = np.copy(cd_frame)
                    
                    self.display_widget.update_frame(frame)
                except Exception as e:
                    print(f"Error in frame callback: {e}")
            
            self.event_frame_gen.set_output_callback(on_cd_frame_cb)
            
            self.is_playing = True
            self.mv_thread = Thread(target=self.process_events, daemon=True)
            self.mv_thread.start()
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.load_button.setEnabled(False)
            self.load_label_button.setEnabled(False)
            
        except Exception as e:
            print(f"Error starting playback: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to start playback: {str(e)}")