import sys
import os
import traceback
import time
import csv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QGroupBox, QPushButton, QLabel, QFileDialog, QSlider, QGridLayout,
                           QFrame, QSplitter, QMessageBox, QListWidget)
from PyQt5.QtGui import QImage, QPainter, QPen, QColor

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

from metavision_core.event_io import EventsIterator
from metavision_core.event_io.raw_reader import initiate_device
from metavision_sdk_ui import EventLoop
from metavision_sdk_core import PeriodicFrameGenerationAlgorithm, ColorPalette

import numpy as np
import cv2
from threading import Thread
from datetime import datetime

from styles import RawViewerStyles as Styles

class EventDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.setMinimumSize(640, 480)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        
        self.img_x_offset = 0
        self.img_y_offset = 0
        self.img_width = 0
        self.img_height = 0
        
        self.frame_count = 0
        self.last_update_time = time.time()
        self.current_point = None
        self.next_point = None

    def update_frame(self, frame):
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        
        if time_diff < 0.1:
            return
            
        self.last_update_time = current_time
        self.frame_count += 1
        
        if frame is not None:
            try:
                if len(frame.shape) == 2:
                    height, width = frame.shape
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                    
                    frame_rgb = cv2.flip(frame_rgb, 1)

                    # Vẽ điểm hiện tại lên frame nếu có
                    if self.current_point:
                        # Scale điểm từ 1920x1080 sang kích thước frame
                        x_scale = width / 1920
                        y_scale = height / 1080
                        
                        x = int(self.current_point[0] * x_scale)
                        y = int(self.current_point[1] * y_scale)
                        
                        # Vẽ điểm hiện tại
                        cv2.circle(frame_rgb, (x, y), max(3, int(10 * x_scale)), (0, 0, 255), -1)
                        
                        # # Vẽ điểm tiếp theo và đường nối nếu có
                        # if self.next_point:
                        #     next_x = int(self.next_point[0] * x_scale)
                        #     next_y = int(self.next_point[1] * y_scale)
                            
                        #     cv2.circle(frame_rgb, (next_x, next_y), max(2, int(6 * x_scale)), (0, 255, 0), -1)
                        #     cv2.line(frame_rgb, (x, y), (next_x, next_y), (255, 0, 0), max(1, int(2 * x_scale)))
                    
                    bytes_per_line = frame_rgb.strides[0]
                    self.image = QImage(
                        frame_rgb.data, width, height, 
                        bytes_per_line, QImage.Format_RGB888
                    )
                else:
                    height, width = frame.shape[:2]
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Vẽ điểm hiện tại lên frame nếu có
                    if self.current_point:
                        # Scale điểm từ 1920x1080 sang kích thước frame
                        x_scale = width / 1920
                        y_scale = height / 1080
                        
                        x = int(self.current_point[0] * x_scale)
                        y = int(self.current_point[1] * y_scale)
                        
                        # Vẽ điểm hiện tại
                        cv2.circle(frame_rgb, (x, y), max(3, int(10 * x_scale)), (0, 0, 255), -1)
                        
                        # # Vẽ điểm tiếp theo và đường nối nếu có
                        # if self.next_point:
                        #     next_x = int(self.next_point[0] * x_scale)
                        #     next_y = int(self.next_point[1] * y_scale)
                            
                        #     cv2.circle(frame_rgb, (next_x, next_y), max(2, int(6 * x_scale)), (0, 255, 0), -1)
                        #     cv2.line(frame_rgb, (x, y), (next_x, next_y), (255, 0, 0), max(1, int(2 * x_scale)))
                    
                    bytes_per_line = frame_rgb.strides[0]
                    self.image = QImage(
                        frame_rgb.data, width, height, 
                        bytes_per_line, QImage.Format_RGB888
                    )
                
                self.update_image_boundaries()
                self.update()
            except Exception as e:
                print(f"Error in update_frame: {e}")
    
    def set_current_point(self, point, next_point=None):
        self.current_point = point
        self.next_point = next_point
    
    def update_image_boundaries(self):
        if self.image is None or self.image.isNull():
            return
            
        scaled_img = self.image.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        self.img_x_offset = (self.width() - scaled_img.width()) // 2
        self.img_y_offset = (self.height() - scaled_img.height()) // 2
        self.img_width = scaled_img.width()
        self.img_height = scaled_img.height()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        if self.image is not None and not self.image.isNull():
            scaled_img = self.image.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            x = (self.width() - scaled_img.width()) // 2
            y = (self.height() - scaled_img.height()) // 2
            
            painter.drawImage(x, y, scaled_img)
            
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(
                self.width() - 100, 
                self.height() - 20, 
                f"Frame: {self.frame_count}"
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image_boundaries()
        
# Define a simple class for bias settings
class BiasValue:
    def __init__(self, name, value, limits):
        self.name = name
        self.value = value
        self.limits = limits


class BiasSettings:
    def __init__(self):
        self.biases = {
            "bias_diff": BiasValue("bias_diff", 25, (-25, 23)),
            "bias_diff_off": BiasValue("bias_diff_off", 190, (-35, 190)),
            "bias_diff_on": BiasValue("bias_diff_on", 140, (-85, 140)),
            "bias_fo": BiasValue("bias_fo", 35, (-35, 55)),
            "bias_hpf": BiasValue("bias_hpf", 110, (0, 120)),
        }
    
    @classmethod
    def create_default(cls):
        return cls()


class BiasControlWidget(QWidget):
    bias_changed = pyqtSignal(str, int)  # Bias name, new value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bias_settings = BiasSettings.create_default()
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Create contrast section
        contrast_group = QGroupBox("Contrast")
        contrast_group.setStyleSheet(Styles.GROUP_BOX)
        contrast_layout = QGridLayout(contrast_group)
        contrast_layout.setColumnStretch(1, 1)  # Make slider column expandable
        
        # Add contrast bias sliders
        row = 0
        for bias_name, display_name in [
            ("bias_diff", "Bias Diff"), 
            ("bias_diff_off", "Bias Diff Off"), 
            ("bias_diff_on", "Bias Diff On")
        ]:
            self.add_bias_slider(contrast_layout, bias_name, display_name, row)
            row += 1
        
        main_layout.addWidget(contrast_group)
        
        # Create bandwidth section
        bandwidth_group = QGroupBox("Bandwidth")
        bandwidth_group.setStyleSheet(Styles.GROUP_BOX)
        bandwidth_layout = QGridLayout(bandwidth_group)
        bandwidth_layout.setColumnStretch(1, 1)  # Make slider column expandable
        
        # Add bandwidth bias sliders
        row = 0
        for bias_name, display_name in [
            ("bias_fo", "Bias FO"), 
            ("bias_hpf", "Bias HPF")
        ]:
            self.add_bias_slider(bandwidth_layout, bias_name, display_name, row)
            row += 1
        
        main_layout.addWidget(bandwidth_group)
        main_layout.addStretch()
        
    def add_bias_slider(self, parent_layout, bias_name, display_name, row):
        bias = self.bias_settings.biases[bias_name]
        min_val, max_val = bias.limits
        
        # Label for bias name
        name_label = QLabel(display_name)
        name_label.setFixedWidth(80)  # Fixed width for all labels
        name_label.setStyleSheet(Styles.LABEL)
        parent_layout.addWidget(name_label, row, 0)
        
        # Create slider
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(bias.value)
        slider.setObjectName(bias_name)
        slider.setStyleSheet(Styles.SLIDER)
        slider.valueChanged.connect(lambda val, name=bias_name: self.on_slider_changed(name, val))
        parent_layout.addWidget(slider, row, 1)
        
        # Value label
        value_label = QLabel(str(bias.value))
        value_label.setObjectName(f"{bias_name}_value")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(Styles.LABEL)
        value_label.setFixedWidth(50)  # Fixed width for value label
        parent_layout.addWidget(value_label, row, 2)
        
        # Add "-" and "+" buttons
        minus_btn = QPushButton("-")
        minus_btn.setFixedSize(30, 30)
        minus_btn.setStyleSheet(Styles.BUTTON)
        minus_btn.clicked.connect(lambda _, name=bias_name: self.decrease_bias(name))
        
        plus_btn = QPushButton("+")
        plus_btn.setFixedSize(30, 30)
        plus_btn.setStyleSheet(Styles.BUTTON)
        plus_btn.clicked.connect(lambda _, name=bias_name: self.increase_bias(name))
        
        parent_layout.addWidget(minus_btn, row, 3)
        parent_layout.addWidget(plus_btn, row, 4)
        
    def on_slider_changed(self, bias_name, value):
        # Update the bias value
        self.bias_settings.biases[bias_name].value = value
        
        # Update the value label
        value_label = self.findChild(QLabel, f"{bias_name}_value")
        if value_label:
            value_label.setText(str(value))
        
        # Emit signal for bias change
        self.bias_changed.emit(bias_name, value)
        
    def decrease_bias(self, bias_name):
        slider = self.findChild(QSlider, bias_name)
        if slider:
            current_value = slider.value()
            slider.setValue(current_value - 5)  # Decrease by 5
            
    def increase_bias(self, bias_name):
        slider = self.findChild(QSlider, bias_name)
        if slider:
            current_value = slider.value()
            slider.setValue(current_value + 5)  # Increase by 5


class RawViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RAW File Viewer with Bias Controls")
        self.setGeometry(100, 100, 1280, 800)
        
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(Styles.BACKGROUND_COLOR))
        self.setPalette(palette)
        
        self.device = None
        self.mv_iterator = None
        self.event_frame_gen = None
        self.mv_thread = None
        self.is_playing = False
        self.current_file = ""
        self.bias_supported = False
        self.label_file = ""
        self.label_data = []
        self.current_frame_timestamp = 0
        self.label_window = None
        
        self.event_window_before = 5000000
        
        self.bias_update_timer = QTimer(self)
        self.bias_update_timer.timeout.connect(self.apply_pending_biases)
        self.pending_bias_updates = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        left_panel = QFrame()
        left_panel.setStyleSheet(Styles.CARD_FRAME)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(20)
        
        file_group = QGroupBox("File Controls")
        file_group.setStyleSheet(Styles.GROUP_BOX)
        file_layout = QVBoxLayout(file_group)
        file_layout.setContentsMargins(15, 25, 15, 15)
        
        self.load_button = QPushButton("Load RAW File")
        self.load_button.setStyleSheet(Styles.BUTTON)
        self.load_button.clicked.connect(self.load_raw_file)
        file_layout.addWidget(self.load_button)
        
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet(Styles.LABEL)
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)
        
        self.load_label_button = QPushButton("Load Label File")
        self.load_label_button.setStyleSheet(Styles.BUTTON)
        self.load_label_button.clicked.connect(self.load_label_file)
        file_layout.addWidget(self.load_label_button)
        
        self.label_file_label = QLabel("No label file selected")
        self.label_file_label.setStyleSheet(Styles.LABEL)
        self.label_file_label.setWordWrap(True)
        file_layout.addWidget(self.label_file_label)
        
        self.label_list = QListWidget()
        self.label_list.setStyleSheet(Styles.LIST_WIDGET)
        self.label_list.itemClicked.connect(self.on_label_selected)
        file_layout.addWidget(QLabel("Label Frames:"))
        file_layout.addWidget(self.label_list)
        
        controls_layout = QHBoxLayout()
        
        self.start_button = QPushButton("▶ Start")
        self.start_button.setStyleSheet(Styles.START_BUTTON)
        self.start_button.clicked.connect(self.start_playback)
        self.start_button.setEnabled(False)
        
        self.stop_button = QPushButton("⬛ Stop")
        self.stop_button.setStyleSheet(Styles.STOP_BUTTON)
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setEnabled(False)
        
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        
        file_layout.addLayout(controls_layout)
        left_layout.addWidget(file_group)
        
        self.bias_widget = BiasControlWidget()
        self.bias_widget.bias_changed.connect(self.queue_bias_update)
        left_layout.addWidget(self.bias_widget)
        
        self.bias_status_label = QLabel("")
        self.bias_status_label.setStyleSheet("color: #D32F2F; font-style: italic;")
        self.bias_status_label.setWordWrap(True)
        left_layout.addWidget(self.bias_status_label)
        
        right_panel = QFrame()
        right_panel.setStyleSheet(Styles.CARD_FRAME)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        display_header = QHBoxLayout()
        display_icon = QLabel("🎥")
        display_icon.setFont(QFont("", 20))
        display_label = QLabel("Event Camera View")
        display_label.setStyleSheet(Styles.DISPLAY_TITLE)
        display_header.addWidget(display_icon)
        display_header.addWidget(display_label)
        display_header.addStretch()
        right_layout.addLayout(display_header)
        
        self.display_widget = EventDisplayWidget()
        self.display_widget.setStyleSheet(Styles.DISPLAY_WIDGET)
        right_layout.addWidget(self.display_widget)
        
        self.timestamp_label = QLabel("Timestamp: -")
        self.timestamp_label.setStyleSheet(Styles.LABEL)
        right_layout.addWidget(self.timestamp_label)
        
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 3)
        
        self.setCentralWidget(central_widget)
    
    def load_raw_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select RAW File", "", "RAW Files (*.raw)"
        )
        
        if file_path:
            self.current_file = file_path
            self.file_label.setText(f"Selected: {os.path.basename(file_path)}")
            self.update_start_button_state()
            
            self.stop_playback()
    
    def load_label_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Label File", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            self.label_file = file_path
            self.label_file_label.setText(f"Label: {os.path.basename(file_path)}")
            
            self.load_label_data(file_path)
            self.update_start_button_state()
            
    
    def load_label_data(self, file_path):
        try:
            self.label_data = []
            self.label_list.clear()
            
            with open(file_path, 'r') as f:
                csv_reader = csv.DictReader(f)
                for i, row in enumerate(csv_reader):
                    timestamp = int(row['Timestamp_ms'])
                    point_index = int(row['Point_Index'])
                    
                    self.label_data.append({
                        'timestamp': timestamp,
                        'point_index': point_index,
                        'x': int(row['X']),
                        'y': int(row['Y']),
                        'next_x': int(row['Next_X']) if row['Next_X'] else None,
                        'next_y': int(row['Next_Y']) if row['Next_Y'] else None,
                    })
                    
                    self.label_list.addItem(f"Point {point_index}: Timestamp {timestamp}")
                    
            print(f"Loaded {len(self.label_data)} label points")
            
        except Exception as e:
            print(f"Error loading label file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load label file: {str(e)}")
    
    def update_start_button_state(self):
        # self.start_button.setEnabled(self.current_file and self.label_file)
        pass
    

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
    
    def start_playback(self):
        if self.label_data:
            first_timestamp = self.label_data[0]['timestamp']
            start_timestamp = first_timestamp - self.event_window_before
            self.start_playback_at_timestamp(start_timestamp)
        else:
            self.start_playback_at_timestamp(0)
            
            
    def on_label_selected(self, item):
        if not self.label_data:
            return
            
        index = self.label_list.currentRow()
        if 0 <= index < len(self.label_data):
            selected_label = self.label_data[index]
            timestamp = selected_label['timestamp']
            
            start_timestamp = timestamp - self.event_window_before
            
            if self.is_playing:
                self.stop_playback()
            
            self.start_playback_at_timestamp(start_timestamp)
            
            self.timestamp_label.setText(f"Timestamp: {timestamp}, Start at: {start_timestamp}")
            self.draw_label_point(selected_label)
    
    def stop_playback(self):
        self.is_playing = False
        
        self.bias_update_timer.stop()
        
        if self.mv_thread and self.mv_thread.is_alive():
            self.mv_thread.join(1.0)
        
        self.mv_thread = None
        self.event_frame_gen = None
        self.mv_iterator = None
        
        if self.device:
            del self.device
            self.device = None
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.load_button.setEnabled(True)
        self.load_label_button.setEnabled(True)
        self.bias_status_label.setText("")
        
    def draw_label_point(self, point_data):
        if not point_data:
            return
            
        # Tạo canvas trắng 1920x1080
        canvas = np.ones((1080, 1920, 3), dtype=np.uint8) * 255
        
        x, y = point_data['x'], point_data['y']
        
        cv2.circle(canvas, (x, y), 10, (0, 0, 255), -1)
        
        # # Vẽ điểm tiếp theo và đường nối nếu có
        # if point_data['next_x'] is not None and point_data['next_y'] is not None:
        #     next_x, next_y = point_data['next_x'], point_data['next_y']
        #     cv2.circle(canvas, (next_x, next_y), 6, (0, 255, 0), -1)
        #     cv2.line(canvas, (x, y), (next_x, next_y), (255, 0, 0), 2)
            
        # Hiển thị thông tin về điểm
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(canvas, f"Point {point_data['point_index']} ({x}, {y})", 
                (50, 50), font, 1, (0, 0, 0), 2)
        cv2.putText(canvas, f"Timestamp: {point_data['timestamp']}", 
                (50, 80), font, 1, (0, 0, 0), 2)
        
        # Resize về 1280x720 để hiển thị
        resized = cv2.resize(canvas, (1280, 720))
        cv2.imshow("Label Points", resized)
        cv2.waitKey(1)
        
        # Cập nhật điểm hiện tại cho display widget
        self.display_widget.set_current_point((x, y), 
                                            (point_data['next_x'], point_data['next_y']) 
                                            if point_data['next_x'] is not None else None)
    
    def find_closest_label_point(self, timestamp):
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
    
    def process_events(self):
        try:
            for evs in self.mv_iterator:
                if not self.is_playing:
                    break
                
                if len(evs) > 0:
                    last_event_ts = evs[-1][3] - 5000000 - 33333 + self.label_data[0]['timestamp']
                    self.current_frame_timestamp = last_event_ts
                    
                    closest_point = self.find_closest_label_point(last_event_ts)
                    if closest_point:
                        self.draw_label_point(closest_point)
                    
                    QApplication.processEvents()
                    self.timestamp_label.setText(f"Current timestamp: {last_event_ts}")
                
                EventLoop.poll_and_dispatch()
                self.event_frame_gen.process_events(evs)
                
                time.sleep(0.03)
        except Exception as e:
            print(f"Error in event processing: {str(e)}")
            self.is_playing = False
            
            QTimer.singleShot(0, lambda: self.stop_button.setEnabled(False))
            QTimer.singleShot(0, lambda: self.start_button.setEnabled(True))
            QTimer.singleShot(0, lambda: self.load_button.setEnabled(True))
            QTimer.singleShot(0, lambda: self.load_label_button.setEnabled(True))
            
    def queue_bias_update(self, bias_name, value):
        self.pending_bias_updates[bias_name] = value
    
    def apply_pending_biases(self):
        if not self.bias_supported or not self.pending_bias_updates:
            return
            
        if self.device and hasattr(self.device, 'get_i_ll_biases'):
            try:
                biases = self.device.get_i_ll_biases()
                if biases is not None:
                    for name, value in self.pending_bias_updates.items():
                        biases.set(name, value)
                        print(f"Applied bias update {name} = {value}")
                    
                    self.pending_bias_updates.clear()
            except Exception as e:
                print(f"Error applying biases: {str(e)}")
    
    def closeEvent(self, event):
        self.stop_playback()
        cv2.destroyAllWindows()
        super().closeEvent(event)
        
def main():
    # Thêm style cho QListWidget
    if not hasattr(Styles, 'LIST_WIDGET'):
        Styles.LIST_WIDGET = """
            QListWidget {
                background-color: #2D2D30;
                color: #CCCCCC;
                border: 1px solid #3F3F46;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3F3F46;
            }
            QListWidget::item:selected {
                background-color: #007ACC;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #3E3E42;
            }
        """
    
    app = QApplication(sys.argv)
    window = RawViewerApp()
    window.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()