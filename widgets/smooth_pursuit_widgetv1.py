import sys
import random
import numpy as np
import yaml
import csv
import time
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtWidgets import QDesktopWidget

class SmoothPursuitWidget(QWidget):
    finished = pyqtSignal()  # Signal to emit when widget is done

    def __init__(self, config_path="config.yaml", wrapper=None):
        super().__init__()
        self.wrapper = wrapper  # Store the wrapper for recording
        self.load_config(config_path)
        self.init_ui()
        self.init_variables()
        self.init_logging()
        self.start_time = None
        self.hide()  # Start hidden

    def load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Error reading config file: {e}")
            raise

        # Initialize parameters from config
        pattern_config = self.config['pattern']
        self.num_rows = pattern_config['num_rows']
        self.points_per_row = pattern_config['points_per_row']
        self.margin = pattern_config['margin']
        self.tail_points = pattern_config['tail_points']

        # Timing configuration
        timing_config = self.config['timing']
        self.point_delay = int(timing_config['point_delay'] * 1000)  # Convert to milliseconds
        self.countdown_seconds = timing_config['countdown_seconds']
        self.thank_you_duration = int(timing_config['thank_you_duration'] * 1000)

        # Colors
        self.colors = self.config['colors']
        self.bg_color = QColor(*self.colors['background'])
        self.point_color = QColor(*self.colors['point'])
        self.text_color = QColor(*self.colors['text'])
        self.heart_color = QColor(*self.colors['heart'])

    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle(self.config['window']['name'])
        if self.config['window']['fullscreen']:
            self.showFullScreen()
        self.setStyleSheet(f"background-color: rgb({self.bg_color.red()}, {self.bg_color.green()}, {self.bg_color.blue()})")

    def init_variables(self):
        """Initialize variables for animation"""
        self.tail_history = []
        self.current_row = 0
        self.current_point = 0
        self.state = 'countdown'
        self.countdown_value = self.countdown_seconds
        self.points = []
        self.calculate_all_points()
        
        # Setup timers
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        
        # Start countdown
        self.countdown_timer.start(1000)

    def init_logging(self):
        """Initialize logging"""
        self.log_file = f"smooth_log.csv"
        with open(self.log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp_ms', 'Row', 'Point_Index', 'X', 'Y', 'Screen_Width', 'Screen_Height'])
            
    def start_countdown(self):
        """Public method to start the countdown and show widget"""
        self.showFullScreen()
        self.countdown_timer.start(1000)

    def update_countdown(self):
        """Update countdown timer"""
        self.countdown_value -= 1
        if self.countdown_value < 0:
            self.countdown_timer.stop()
            self.state = 'animation'
            self.start_time = time.time()
            self.animation_timer.start(self.point_delay)
        self.update()
    def update_animation(self):
        """Update animation state"""
        if self.current_row >= self.num_rows:
            self.animation_timer.stop()
            self.state = 'thank_you'
            if self.wrapper:
                self.wrapper.stop_recording()  # Stop recording when animation ends
            QTimer.singleShot(self.thank_you_duration, self.cleanup)
            self.update()
            return
    def cleanup(self):
        """Clean up and close the widget"""
        self.hide()
        self.finished.emit()  # Emit signal when done
        self.deleteLater()
    def calculate_all_points(self):
        """Calculate all points for the pattern"""
        screen = QDesktopWidget().screenGeometry()
        width, height = screen.width(), screen.height()
        
        for row in range(self.num_rows):
            row_height = (height - 2 * self.margin) / (self.num_rows - 1)
            y = self.margin + row * row_height
            row_width = width - 2 * self.margin
            
            if row % 2 == 0:  # Even rows: left to right
                points = [QPoint(
                    int(self.margin + i * row_width/(self.points_per_row-1)),
                    int(y)
                ) for i in range(self.points_per_row)]
            else:  # Odd rows: right to left
                points = [QPoint(
                    int(width - self.margin - i * row_width/(self.points_per_row-1)),
                    int(y)
                ) for i in range(self.points_per_row)]
            
            self.points.append(points)

    def log_point(self, point):
        """Log point to CSV file"""
        screen = QDesktopWidget().screenGeometry()
        if self.start_time is None:
            self.start_time = time.time()
        
        timestamp_ms = int((time.time() - self.start_time) * 1000)
        
        with open(self.log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                timestamp_ms,
                self.current_row,
                self.current_point,
                point.x(),
                point.y(),
                screen.width(),
                screen.height()
            ])

    def update_countdown(self):
        """Update countdown timer"""
        self.countdown_value -= 1
        if self.countdown_value < 0:
            self.countdown_timer.stop()
            self.state = 'animation'
            self.start_time = time.time()  # Start timing when animation begins
            self.animation_timer.start(self.point_delay)
        self.update()

    def update_animation(self):
        """Update animation state"""
        if self.current_row >= self.num_rows:
            self.animation_timer.stop()
            self.state = 'thank_you'
            QTimer.singleShot(self.thank_you_duration, self.close)
            self.update()
            return

        current_point = self.points[self.current_row][self.current_point]
        self.tail_history.append(current_point)
        if len(self.tail_history) > self.tail_points:
            self.tail_history.pop(0)

        self.log_point(current_point)
        
        self.current_point += 1
        if self.current_point >= self.points_per_row:
            self.current_point = 0
            self.current_row += 1

        self.update()

    def paintEvent(self, event):
        """Handle paint event"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.state == 'countdown':
            self.paint_countdown(painter)
        elif self.state == 'animation':
            self.paint_animation(painter)
        elif self.state == 'thank_you':
            self.paint_thank_you(painter)

    def paint_countdown(self, painter):
        """Paint countdown screen"""
        text = str(self.countdown_value)
        font = QFont()
        font.setPointSize(72)
        painter.setFont(font)
        painter.setPen(self.text_color)
        
        rect = self.rect()
        painter.drawText(rect, Qt.AlignCenter, text)

    def paint_animation(self, painter):
        """Paint animation frame"""
        point_config = self.config['point']
        point_size = point_config['size']
        
        # Draw tail points
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.point_color)
        
        # Draw trail points
        for point in self.tail_history[:-1]:
            painter.drawEllipse(point, point_size, point_size)

        # Draw current point larger
        if self.tail_history:
            current_point = self.tail_history[-1]
            painter.drawEllipse(current_point, point_size * 2, point_size * 2)

    def paint_thank_you(self, painter):
        """Paint thank you screen"""
        text = random.choice(self.config['thank_you_text']['messages'])
        font = QFont()
        font.setPointSize(36)
        painter.setFont(font)
        painter.setPen(self.text_color)
        
        rect = self.rect()
        painter.drawText(rect, Qt.AlignCenter, text)
        
        # Draw heart
        heart_size = self.config['heart']['size']
        center = rect.center()
        self.draw_heart(painter, center.x() + 100, center.y(), heart_size)

    def draw_heart(self, painter, x, y, size):
        """Draw heart shape"""
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.heart_color)
        
        radius = size // 2
        # Draw circles for top of heart
        painter.drawEllipse(x - radius, y, radius, radius)
        painter.drawEllipse(x, y, radius, radius)
        
        # Draw triangle for bottom of heart
        points = [
            QPoint(x - size, y + radius//2),
            QPoint(x + size - radius, y + radius//2),
            QPoint(x + radius//2 - size//2, y + size)
        ]
        painter.drawPolygon(points)

def main():
    app = QApplication(sys.argv)
    widget = SmoothPursuitWidget("config/config_smooth.yaml")
    widget.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()