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
import numpy as np
import time
from screeninfo import get_monitors
import yaml
import csv
from datetime import datetime
from widgets.metavision_display_widget import MetavisionDisplayWidget

class MetavisionWidget(QWidget):
    def __init__(self, wrapper: LiveReplayEventsIteratorWrapper, parent=None):
        super().__init__(parent)
        self.wrapper = wrapper
        self.setup_ui()
        self.events = None
        self.event_list = []

    def setup_ui(self):
        layout = QHBoxLayout(self)

        # Left side - Record Button
        self.record_button = QPushButton("Record")
        self.record_button.setFixedSize(120, 50)
        left_layout = QVBoxLayout()
        left_layout.addStretch()
        left_layout.addWidget(self.record_button, alignment=Qt.AlignCenter)
        left_layout.addStretch()

        # Right side - Metavision Display
        self.displayer = MetavisionDisplayWidget()

        layout.addLayout(left_layout, 1)
        layout.addWidget(self.displayer, 4)
    
    def run_metavision(self):
        event_frame_gen = self.wrapper.get_event_frame_gen()

        def on_cd_frame_cb(ts, cd_frame):
            frame = np.copy(cd_frame)
            self.displayer.update_frame(frame)

        event_frame_gen.set_output_callback(on_cd_frame_cb)
        
        # Start processing in a new thread
        self.mv_thread = Thread(target=self.process_events, args=(event_frame_gen, ), daemon=True)
        self.mv_thread.start()

    def process_events(self, event_frame_gen):
        try:
            for evs in self.wrapper.mv_iterator:
                EventLoop.poll_and_dispatch()
                self.events = evs
                event_frame_gen.process_events(evs)
        except Exception as e:
            print(f"Error in Metavision pipeline: {str(e)}")

    def stop_recording(self):
        self.wrapper.stop_recording()