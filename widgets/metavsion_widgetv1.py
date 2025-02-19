# import sys
# import numpy as np
# from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
#                             QWidget, QPushButton, QLabel)
# from PyQt5.QtGui import QImage, QPainter, QFont, QPen, QColor
# from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
# from threading import Thread
# import yaml
# import csv
# from datetime import datetime
# from metavision_API.live_replay_events_iterator import *
# import random
# import cv2
# import numpy as np
# import time
# from screeninfo import get_monitors
# import yaml
# import csv
# from datetime import datetime
# from widgets.metavision_display_widget import MetavisionDisplayWidget

# class MetavisionWidget(QWidget):
#     def __init__(self, wrapper, parent=None):
#         super().__init__(parent)
#         self.wrapper = wrapper
#         self.setup_ui()
#         self.events = None
#         self.event_list = []

#     def setup_ui(self):
#         layout = QHBoxLayout(self)

#         # Left side - Record Button
#         self.record_button = QPushButton("Record")
#         self.record_button.setFixedSize(120, 50)
#         left_layout = QVBoxLayout()
#         left_layout.addStretch()
#         left_layout.addWidget(self.record_button, alignment=Qt.AlignCenter)
#         left_layout.addStretch()

#         # Right side - Metavision Display
#         self.displayer = MetavisionDisplayWidget()

#         layout.addLayout(left_layout, 1)
#         layout.addWidget(self.displayer, 4)
    
#     def run_metavision(self):
#         event_frame_gen = self.wrapper.get_event_frame_gen()

#         def on_cd_frame_cb(ts, cd_frame):
#             frame = np.copy(cd_frame)
#             self.displayer.update_frame(frame)

#         event_frame_gen.set_output_callback(on_cd_frame_cb)
        
#         # Start processing in a new thread
#         self.mv_thread = Thread(target=self.process_events, args=(event_frame_gen, ), daemon=True)
#         self.mv_thread.start()

#     def process_events(self, event_frame_gen):
#         try:
#             for evs in self.wrapper.mv_iterator:
#                 EventLoop.poll_and_dispatch()
#                 self.events = evs
#                 self.event_list.append(evs)
#                 event_frame_gen.process_events(evs)
#         except Exception as e:
#             print(f"Error in Metavision pipeline: {str(e)}")

# import os
# import sys
# import numpy as np
# from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
#                             QWidget, QPushButton, QLabel)
# from PyQt5.QtGui import QImage, QPainter, QFont, QPen, QColor
# from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
# from threading import Thread
# import yaml
# import csv
# from datetime import datetime
# from metavision_API.live_replay_events_iterator import *
# import random
# import cv2
# import numpy as np
# import time
# from screeninfo import get_monitors
# import yaml
# import csv
# from datetime import datetime
# from widgets.metavision_display_widget import MetavisionDisplayWidget
# import numpy as np
# import cv2
# from datetime import datetime
# import struct

# class MetavisionWidget(QWidget):
#     def __init__(self, wrapper, parent=None):
#         super().__init__(parent)
#         self.wrapper = wrapper
        
#         # Add recording status label
#         self.status_label = QLabel("Not Recording")
#         self.status_label.setStyleSheet("color: gray;")
#         self.setup_ui()
#         self.events = None
#         self.event_list = []
#         self.recording = False
#         self.video_writer = None
#         self.aedat_file = None
        
#         # Create recordings directory if it doesn't exist
#         self.recordings_dir = "recordings"
#         os.makedirs(self.recordings_dir, exist_ok=True)
        
#     def setup_ui(self):
#         layout = QHBoxLayout(self)

#         # Left side - Record Controls
#         left_layout = QVBoxLayout()
        
#         # Modified record button to toggle recording
#         self.record_button = QPushButton("Start Recording")
#         self.record_button.setFixedSize(120, 50)
#         self.record_button.clicked.connect(self.toggle_recording)
        
#         left_layout.addStretch()
#         left_layout.addWidget(self.record_button, alignment=Qt.AlignCenter)
#         left_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
#         left_layout.addStretch()

#         # Right side - Metavision Display
#         self.displayer = MetavisionDisplayWidget()

#         layout.addLayout(left_layout, 1)
#         layout.addWidget(self.displayer, 4)
    
#     def toggle_recording(self):
#         if not self.recording:
#             self.start_recording()
#         else:
#             self.stop_recording()
    
#     def start_recording(self):
#         """Start recording both video and events"""
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
#         try:
#             # Initialize video writer
#             fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#             video_path = os.path.join(self.recordings_dir, f"video_{timestamp}.mp4")
#             frame_size = (self.displayer.width(), self.displayer.height())
#             self.video_writer = cv2.VideoWriter(video_path, fourcc, 30.0, frame_size)
            
#             # Initialize AEDAT file
#             aedat_path = os.path.join(self.recordings_dir, f"events_{timestamp}.aedat")
#             self.aedat_file = open(aedat_path, 'wb')
            
#             # Write AEDAT header
#             self.write_aedat_header()
            
#             self.recording = True
#             self.record_button.setText("Stop Recording")
#             self.status_label.setText("Recording...")
#             self.status_label.setStyleSheet("color: red;")
            
#         except Exception as e:
#             self.status_label.setText(f"Error: {str(e)}")
#             self.status_label.setStyleSheet("color: red;")
#             print(f"Error starting recording: {str(e)}")
#             self.stop_recording()  # Clean up any partially opened files
    
#     def stop_recording(self):
#         """Stop recording and close files"""
#         if self.video_writer:
#             self.video_writer.release()
#             self.video_writer = None
            
#         if self.aedat_file:
#             self.aedat_file.close()
#             self.aedat_file = None
        
#         self.recording = False
#         self.record_button.setText("Start Recording")
#         self.status_label.setText("Recording Saved")
#         self.status_label.setStyleSheet("color: green;")
    
#     def write_aedat_header(self):
#         """Write the AEDAT file header"""
#         header = b"#!AER-DAT3.1\r\n"
#         header += b"# This is a raw AER data file created by Metavision\r\n"
#         header += f"# Date: {datetime.now()}\r\n".encode()
#         header += b"# Start of data\r\n"
#         self.aedat_file.write(header)
    
#     def write_event_to_aedat(self, event):
#         """Write a single event to the AEDAT file"""
#         if self.aedat_file:
#             # AEDAT3 format: timestamp (8 bytes) + x (2 bytes) + y (2 bytes) + polarity (1 byte)
#             timestamp = int(event[3] * 1e6)  # Convert to microseconds
#             x = int(event[0])
#             y = int(event[1])
#             polarity = int(event[2])
            
#             event_data = struct.pack('>QHHB', timestamp, x, y, polarity)
#             self.aedat_file.write(event_data)
    
#     def run_metavision(self):
#         event_frame_gen = self.wrapper.get_event_frame_gen()

#         def on_cd_frame_cb(ts, cd_frame):
#             frame = np.copy(cd_frame)
#             self.displayer.update_frame(frame)
            
#             # Save frame to video if recording
#             if self.recording and self.video_writer:
#                 # Convert to RGB if necessary
#                 if len(frame.shape) == 2:
#                     frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
#                 self.video_writer.write(frame)

#         event_frame_gen.set_output_callback(on_cd_frame_cb)
        
#         # Start processing in a new thread
#         self.mv_thread = Thread(target=self.process_events, args=(event_frame_gen,), daemon=True)
#         self.mv_thread.start()

#     def process_events(self, event_frame_gen):
#         try:
#             for evs in self.wrapper.mv_iterator:
#                 EventLoop.poll_and_dispatch()
#                 self.events = evs
#                 self.event_list.append(evs)
                
#                 # Save events to AEDAT file if recording
#                 if self.recording and self.aedat_file:
#                     for event in evs:
#                         self.write_event_to_aedat(event)
                
#                 event_frame_gen.process_events(evs)
#         except Exception as e:
#             print(f"Error in Metavision pipeline: {str(e)}")
#             self.stop_recording()  # Ensure files are closed if error occurs


# import os
# import sys
# import numpy as np
# from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
#                             QWidget, QPushButton, QLabel)
# from PyQt5.QtGui import QImage, QPainter, QFont, QPen, QColor
# from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
# from threading import Thread
# import yaml
# import csv
# from datetime import datetime
# from metavision_API.live_replay_events_iterator import *
# import random
# import cv2
# import time
# from screeninfo import get_monitors
# from widgets.metavision_display_widget import MetavisionDisplayWidget
# import h5py

# class MetavisionWidget(QWidget):
#     def __init__(self, wrapper, parent=None):
#         super().__init__(parent)
#         self.wrapper = wrapper
        
#         # Add recording status label
#         self.status_label = QLabel("Not Recording")
#         self.status_label.setStyleSheet("color: gray;")
#         self.setup_ui()
#         self.events = None
#         self.event_list = []
#         self.recording = False
#         self.video_writer = None
#         self.h5_file = None
#         self.event_buffer = {
#             'x': [],
#             'y': [],
#             'polarity': [],
#             'timestamp': []
#         }
#         self.buffer_size = 10000  # Number of events to buffer before writing to file
        
#         # Create recordings directory if it doesn't exist
#         self.recordings_dir = "recordings"
#         os.makedirs(self.recordings_dir, exist_ok=True)
        
#     def setup_ui(self):
#         layout = QHBoxLayout(self)

#         # Left side - Record Controls
#         left_layout = QVBoxLayout()
        
#         # Modified record button to toggle recording
#         self.record_button = QPushButton("Start Recording")
#         self.record_button.setFixedSize(120, 50)
#         self.record_button.clicked.connect(self.toggle_recording)
        
#         left_layout.addStretch()
#         left_layout.addWidget(self.record_button, alignment=Qt.AlignCenter)
#         left_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
#         left_layout.addStretch()

#         # Right side - Metavision Display
#         self.displayer = MetavisionDisplayWidget()

#         layout.addLayout(left_layout, 1)
#         layout.addWidget(self.displayer, 4)
    
#     def toggle_recording(self):
#         if not self.recording:
#             self.start_recording()
#         else:
#             self.stop_recording()
    
#     def start_recording(self):
#         """Start recording both video and events"""
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
#         try:
#             # Initialize video writer
#             fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#             video_path = os.path.join(self.recordings_dir, f"video_{timestamp}.mp4")
#             frame_size = (self.displayer.width(), self.displayer.height())
#             self.video_writer = cv2.VideoWriter(video_path, fourcc, 30.0, frame_size)
            
#             # Initialize HDF5 file
#             h5_path = os.path.join(self.recordings_dir, f"events_{timestamp}.h5")
#             self.h5_file = h5py.File(h5_path, 'w')
            
#             # Create event datasets with chunking for efficient appending
#             self.create_h5_datasets()
            
#             # Add metadata
#             self.h5_file.attrs['date'] = str(datetime.now())
#             self.h5_file.attrs['frame_width'] = frame_size[0]
#             self.h5_file.attrs['frame_height'] = frame_size[1]
            
#             self.recording = True
#             self.record_button.setText("Stop Recording")
#             self.status_label.setText("Recording...")
#             self.status_label.setStyleSheet("color: red;")
            
#         except Exception as e:
#             self.status_label.setText(f"Error: {str(e)}")
#             self.status_label.setStyleSheet("color: red;")
#             print(f"Error starting recording: {str(e)}")
#             self.stop_recording()  # Clean up any partially opened files
    
#     def create_h5_datasets(self):
#         """Create initial empty datasets in the HDF5 file"""
#         events_group = self.h5_file.create_group('events')
        
#         # Create extendable datasets for each event attribute
#         max_shape = (None,)  # Allows dataset to be resized
#         chunk_size = (self.buffer_size,)  # Optimize for appending in buffer_size chunks
        
#         events_group.create_dataset('x', (0,), maxshape=max_shape, 
#                                   dtype='uint16', chunks=chunk_size)
#         events_group.create_dataset('y', (0,), maxshape=max_shape, 
#                                   dtype='uint16', chunks=chunk_size)
#         events_group.create_dataset('polarity', (0,), maxshape=max_shape, 
#                                   dtype='uint8', chunks=chunk_size)
#         events_group.create_dataset('timestamp', (0,), maxshape=max_shape, 
#                                   dtype='uint64', chunks=chunk_size)
    
#     def write_event_buffer_to_h5(self):
#         """Write buffered events to HDF5 file"""
#         if not self.h5_file or not any(self.event_buffer['x']):
#             return
            
#         events_group = self.h5_file['events']
        
#         # Get current sizes
#         current_size = len(events_group['x'])
#         append_size = len(self.event_buffer['x'])
#         new_size = current_size + append_size
        
#         # Resize datasets
#         for key in self.event_buffer.keys():
#             events_group[key].resize((new_size,))
#             events_group[key][current_size:new_size] = self.event_buffer[key]
        
#         # Clear buffer
#         self.event_buffer = {key: [] for key in self.event_buffer.keys()}
    
#     def stop_recording(self):
#         """Stop recording and close files"""
#         if self.video_writer:
#             self.video_writer.release()
#             self.video_writer = None
        
#         if self.h5_file:
#             # Write any remaining buffered events
#             self.write_event_buffer_to_h5()
#             self.h5_file.close()
#             self.h5_file = None
        
#         self.recording = False
#         self.record_button.setText("Start Recording")
#         self.status_label.setText("Recording Saved")
#         self.status_label.setStyleSheet("color: green;")
    
#     def add_event_to_buffer(self, event):
#         """Add a single event to the buffer and write if buffer is full"""
#         if self.h5_file:
#             # Add event to buffer
#             self.event_buffer['x'].append(int(event[0]))
#             self.event_buffer['y'].append(int(event[1]))
#             self.event_buffer['polarity'].append(int(event[2]))
#             self.event_buffer['timestamp'].append(int(event[3] * 1e6))  # Convert to microseconds
            
#             # Write to file if buffer is full
#             if len(self.event_buffer['x']) >= self.buffer_size:
#                 self.write_event_buffer_to_h5()
    
#     def run_metavision(self):
#         event_frame_gen = self.wrapper.get_event_frame_gen()

#         def on_cd_frame_cb(ts, cd_frame):
#             frame = np.copy(cd_frame)
#             self.displayer.update_frame(frame)
            
#             # Save frame to video if recording
#             if self.recording and self.video_writer:
#                 # Convert to RGB if necessary
#                 if len(frame.shape) == 2:
#                     frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
#                 self.video_writer.write(frame)

#         event_frame_gen.set_output_callback(on_cd_frame_cb)
        
#         # Start processing in a new thread
#         self.mv_thread = Thread(target=self.process_events, args=(event_frame_gen,), daemon=True)
#         self.mv_thread.start()

#     def process_events(self, event_frame_gen):
#         try:
#             for evs in self.wrapper.mv_iterator:
#                 EventLoop.poll_and_dispatch()
#                 self.events = evs
#                 self.event_list.append(evs)
                
#                 # Save events to HDF5 file if recording
#                 if self.recording and self.h5_file:
#                     for event in evs:
#                         self.add_event_to_buffer(event)
                
#                 event_frame_gen.process_events(evs)
#         except Exception as e:
#             print(f"Error in Metavision pipeline: {str(e)}")
#             self.stop_recording()  # Ensure files are closed if error occurs


import os
import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                            QWidget, QPushButton, QLabel)
from PyQt5.QtGui import QImage, QPainter, QFont, QPen, QColor
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from threading import Thread
import yaml
import csv
from datetime import datetime
from metavision_API.live_replay_events_iterator import *
import random
import cv2
import time
from screeninfo import get_monitors
from widgets.metavision_display_widget import MetavisionDisplayWidget
import h5py

class MetavisionWidget(QWidget):
    def __init__(self, wrapper, parent=None):
        super().__init__(parent)
        self.wrapper = wrapper
        
        # Add recording status label
        self.status_label = QLabel("Not Recording")
        self.status_label.setStyleSheet("color: gray;")
        self.setup_ui()
        self.events = None
        self.event_list = []
        self.recording = False
        self.video_writer = None
        self.h5_file = None
        
        # Improved event buffer with numpy arrays
        self.event_buffer = {
            'x': np.array([], dtype=np.uint16),
            'y': np.array([], dtype=np.uint16),
            'polarity': np.array([], dtype=np.uint8),
            'timestamp': np.array([], dtype=np.uint64)
        }
        self.buffer_size = 10000
        
        # Create recordings directory if it doesn't exist
        self.recordings_dir = "recordings"
        os.makedirs(self.recordings_dir, exist_ok=True)
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.setFixedSize(120, 50)
        self.record_button.clicked.connect(self.toggle_recording)
        
        left_layout.addStretch()
        left_layout.addWidget(self.record_button, alignment=Qt.AlignCenter)
        left_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        left_layout.addStretch()

        self.displayer = MetavisionDisplayWidget()
        layout.addLayout(left_layout, 1)
        layout.addWidget(self.displayer, 4)
    
    def start_recording(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Initialize video writer with more robust settings
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            video_path = os.path.join(self.recordings_dir, f"video_{timestamp}.avi")
            frame_size = (self.displayer.width(), self.displayer.height())
            
            if frame_size[0] <= 0 or frame_size[1] <= 0:
                raise ValueError(f"Invalid frame size: {frame_size}")
            
            self.video_writer = cv2.VideoWriter(video_path, fourcc, 30.0, frame_size)
            if not self.video_writer.isOpened():
                raise ValueError("Failed to open video writer")
            
            # Initialize HDF5 file with Meta Vision compatible structure
            h5_path = os.path.join(self.recordings_dir, f"events_{timestamp}.hdf5")
            self.h5_file = h5py.File(h5_path, 'w')
            self.create_h5_datasets()
            
            self.recording = True
            self.record_button.setText("Stop Recording")
            self.status_label.setText("Recording...")
            self.status_label.setStyleSheet("color: red;")
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            print(f"Error starting recording: {str(e)}")
            self.stop_recording()
    
    def create_h5_datasets(self):
        """Create HDF5 datasets in Meta Vision compatible format"""
        # Create main event compound dataset
        dt = np.dtype([
            ('timestamp', np.uint64),
            ('x', np.uint16),
            ('y', np.uint16),
            ('polarity', np.uint8)
        ])
        
        # Create datasets with chunking and compression
        self.h5_file.create_dataset(
            'events',
            shape=(0,),
            maxshape=(None,),
            dtype=dt,
            chunks=(self.buffer_size,),
            compression='gzip',
            compression_opts=4
        )
        
        # Add metadata
        self.h5_file.attrs['width'] = self.displayer.width()
        self.h5_file.attrs['height'] = self.displayer.height()
        self.h5_file.attrs['date_recorded'] = str(datetime.now())
        self.h5_file.attrs['format_version'] = '2.0'
    
    def add_events_to_buffer(self, events):
        """Add multiple events to buffer efficiently"""
        if not self.h5_file:
            return
            
        # Convert events to structured array
        event_data = np.zeros(len(events), dtype=[
            ('timestamp', np.uint64),
            ('x', np.uint16),
            ('y', np.uint16),
            ('polarity', np.uint8)
        ])
        
        for i, event in enumerate(events):
            event_data[i] = (
                int(event[3] * 1e6),  # timestamp in microseconds
                int(event[0]),        # x
                int(event[1]),        # y
                int(event[2])         # polarity
            )
        
        # Append to dataset
        current_size = len(self.h5_file['events'])
        new_size = current_size + len(event_data)
        
        try:
            self.h5_file['events'].resize((new_size,))
            self.h5_file['events'][current_size:new_size] = event_data
        except Exception as e:
            print(f"Error writing events to HDF5: {str(e)}")
    
    def stop_recording(self):
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        if self.h5_file:
            try:
                # Ensure all pending writes are completed
                self.h5_file.flush()
                self.h5_file.close()
            except Exception as e:
                print(f"Error closing HDF5 file: {str(e)}")
            self.h5_file = None
        
        self.recording = False
        self.record_button.setText("Start Recording")
        self.status_label.setText("Recording Saved")
        self.status_label.setStyleSheet("color: green;")
    
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def run_metavision(self):
        event_frame_gen = self.wrapper.get_event_frame_gen()

        def on_cd_frame_cb(ts, cd_frame):
            frame = np.copy(cd_frame)
            self.displayer.update_frame(frame)
            
            if self.recording and self.video_writer and self.video_writer.isOpened():
                try:
                    # Ensure frame is in correct format
                    if len(frame.shape) == 2:
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    elif len(frame.shape) == 3 and frame.shape[2] == 4:
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                    
                    # Normalize and convert to uint8
                    if frame.dtype != np.uint8:
                        frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                    
                    success = self.video_writer.write(frame)
                    if not success:
                        print(f"Warning: Failed to write video frame at timestamp {ts}")
                except Exception as e:
                    print(f"Error processing video frame: {str(e)}")

        event_frame_gen.set_output_callback(on_cd_frame_cb)
        
        self.mv_thread = Thread(target=self.process_events, args=(event_frame_gen,), daemon=True)
        self.mv_thread.start()

    def process_events(self, event_frame_gen):
        try:
            for evs in self.wrapper.mv_iterator:
                EventLoop.poll_and_dispatch()
                self.events = evs
                
                # Save events if recording
                if self.recording and self.h5_file:
                    self.add_events_to_buffer(evs)
                
                event_frame_gen.process_events(evs)
        except Exception as e:
            print(f"Error in Metavision pipeline: {str(e)}")
            self.stop_recording()

