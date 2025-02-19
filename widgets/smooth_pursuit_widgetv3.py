import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import yaml
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtWidgets import QDesktopWidget
import csv
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QTimer, QPoint

class CountdownPainter(QWidget):
    countdown_finished = pyqtSignal()  # Signal when countdown ends

    def __init__(self, countdown_value=15, parent=None):
        super().__init__(parent)
        self.countdown_value = countdown_value
        self.text_color = QColor(255, 0, 0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)  # Update every second

    def update_countdown(self):
        if self.countdown_value > 0:
            self.countdown_value -= 1
            self.update()
        else:
            self.timer.stop()
            self.countdown_finished.emit()  # Emit signal when finished

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont()
        font.setPointSize(72)
        painter.setFont(font)
        painter.setPen(self.text_color)
        painter.drawText(self.rect(), Qt.AlignCenter, str(self.countdown_value))
    

class Animation(QWidget):
    def __init__(self, point_config, point_color, pattern_points, point_delay):
        super().__init__()
        # Configuration
        self.point_config = point_config
        self.point_color = point_color
        self.pattern_points = pattern_points
        self.point_delay = point_delay
        
        # Animation state
        self.tail_history = []
        self.current_row = 0
        self.current_point = 0
        
        # Set window attributes
        self.setAttribute(Qt.WA_StyledBackground)
        self.setAutoFillBackground(True)
        
        # Setup animation timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(self.point_delay)

    def paintEvent(self, event):
        """Override paintEvent to handle the widget's painting"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get point size from config
        point_size = self.point_config['size']
        
        # Draw tail points
        painter.setPen(Qt.NoPen)
        
        # Draw trail points with fade effect
        if self.tail_history:
            num_points = len(self.tail_history)
            for i, point in enumerate(self.tail_history[:-1]):
                # Calculate opacity based on position in trail
                opacity = (i + 1) / num_points
                color = QColor(self.point_color)
                color.setAlphaF(opacity)
                painter.setBrush(color)
                
                # Draw the point
                painter.drawEllipse(point, point_size, point_size)

            # Draw current point larger and fully opaque
            painter.setBrush(self.point_color)
            current_point = self.tail_history[-1]
            painter.drawEllipse(current_point, point_size * 2, point_size * 2)

    def update_animation(self):
        """Update the animation state"""
        if self.current_row >= len(self.pattern_points):
            self.animation_timer.stop()
            return

        # Get current point from pattern
        current_point = self.pattern_points[self.current_row][self.current_point]
        self.tail_history.append(current_point)
        
        # Limit tail length
        max_tail_length = self.point_config.get('tail_length', 10)
        if len(self.tail_history) > max_tail_length:
            self.tail_history = self.tail_history[-max_tail_length:]
            
        # Move to next point
        self.current_point += 1
        if self.current_point >= len(self.pattern_points[self.current_row]):
            self.current_point = 0
            self.current_row += 1
            
        self.update()  # Request a repaint

    def stop_animation(self):
        """Stop the animation timer"""
        self.animation_timer.stop()

    def start_animation(self):
        """Start the animation timer"""
        self.animation_timer.start(self.point_delay)
            
class DummyWidget(QWidget):
    """Widget to replace countdown and display when finished"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: lightgray;")  # Just to visualize
        

class SmoothPursuitWidget(QWidget):
    def __init__(self, display_widget, config_path="config.yaml", wrapper=None):
        super().__init__()
        self.setWindowTitle("Full Screen Countdown")

        self.load_config(config_path)
        self.init_variables()
        # Create a vertical layout
        self.current_layout = QVBoxLayout()

        # Add the countdown widget
        self.countdown_painter = CountdownPainter()
        self.current_layout.addWidget(self.countdown_painter, stretch=1)

        # Add the display widget below the countdown
        self.display_widget = display_widget
        self.current_layout.addWidget(self.display_widget.displayer, stretch=3)

        # Connect countdown finished signal to hide countdown and display
        self.countdown_painter.countdown_finished.connect(self.on_countdown_finished)

        self.setLayout(self.current_layout)


    def init_variables(self):
        """Initialize variables for animation"""
        self.tail_history = []
        self.current_row = 0
        self.current_point = 0
        self.state = 'countdown'
        self.countdown_value = self.countdown_seconds
        self.points = []
        self.patterns_point = self.calculate_all_points()

    def on_countdown_finished(self):
        """Replace countdown and display with animation widget"""
        self.countdown_painter.hide()
        self.display_widget.displayer.hide()

        # Add the animation widget with all necessary parameters
        self.animation_widget = Animation(
            point_config=self.config['point'],
            point_color=self.point_color,
            pattern_points=self.patterns_point,
            point_delay=self.point_delay
        )
        self.current_layout.addWidget(self.animation_widget, stretch=1)
        
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

    def calculate_all_points(self):
        """Calculate all points for the pattern"""
        all_points = []  # Create a list to store all rows of points
        screen = QDesktopWidget().screenGeometry()
        width, height = screen.width(), screen.height()
        
        for row in range(self.num_rows):
            row_points = []  # Create a list for each row's points
            row_height = (height - 2 * self.margin) / (self.num_rows - 1)
            y = self.margin + row * row_height
            row_width = width - 2 * self.margin
            
            if row % 2 == 0:  # Even rows: left to right
                row_points = [QPoint(
                    int(self.margin + i * row_width/(self.points_per_row-1)),
                    int(y)
                ) for i in range(self.points_per_row)]
            else:  # Odd rows: right to left
                row_points = [QPoint(
                    int(width - self.margin - i * row_width/(self.points_per_row-1)),
                    int(y)
                ) for i in range(self.points_per_row)]
            
            all_points.append(row_points)  # Append each row's points to the main list
        
        return all_points
        
    def init_logging(self):
        """Initialize logging"""
        self.log_file = f"smooth_log.csv"
        with open(self.log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp_ms', 'Row', 'Point_Index', 'X', 'Y', 'Screen_Width', 'Screen_Height'])

class DummyDisplayWidget(QWidget):
    """A placeholder widget to simulate display functionality"""
    def __init__(self):
        super().__init__()
        self.displayer = QWidget()
        self.displayer.setStyleSheet("background-color: lightblue;")  # Just to visualize it


def main():
    app = QApplication(sys.argv)

    # Create a dummy display widget (replace this with actual content)
    display_widget = DummyDisplayWidget()

    # Pass it to SmoothPursuitWidget
    window = SmoothPursuitWidget(display_widget)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
