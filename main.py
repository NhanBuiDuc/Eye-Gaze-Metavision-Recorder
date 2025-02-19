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
from widgets.metavsion_widget import MetavisionWidget
from widgets.smooth_pursuit_widget import SmoothPursuitWidget  # Import the widget

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Metavision UI")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create wrapper instance
        self.wrapper = LiveReplayEventsIteratorWrapper(
            output_file="public/recordings",
            event_count=100000,
            roi_coordinates=[400, 200, 800, 470],
            bias_file="public/biases.bias" 
        )
        
        self.metavision_widget = MetavisionWidget(self.wrapper, self)
        self.setCentralWidget(self.metavision_widget)
        
        self.smooth_pursuit = None
        
        self.metavision_widget.run_metavision()
        
        self.metavision_widget.record_button.clicked.connect(self.start_smooth_pursuit)
        
    def start_smooth_pursuit(self):
        """Start the smooth pursuit pattern"""
        self.smooth_pursuit = SmoothPursuitWidget(self.metavision_widget, "config/config_smooth.yaml", self.wrapper)
        self.smooth_pursuit.showFullScreen()
        
    def on_smooth_pursuit_finished(self):
        """Handle completion of smooth pursuit pattern"""
        self.smooth_pursuit = None  # Clean up reference
        self.show()  
        self.metavision_widget.update()  # Refresh main widget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainApp()
    mainWin.showMaximized()
    sys.exit(app.exec_())