import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QDesktopWidget
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
import yaml
import cv2
from auto_labelling.saccade import SaccadePattern  # Assuming this is the correct import path

class SaccadeAnimation(QWidget):
    def __init__(self, point_config, colors, pattern_points, point_duration, show_direction=True):
        super().__init__()
        # Configuration
        self.point_config = point_config
        self.colors = colors
        self.pattern_points = pattern_points
        self.point_duration = point_duration
        self.show_direction = show_direction
        
        # Animation state
        self.current_point_index = 0
        
        # Set window attributes
        self.setAttribute(Qt.WA_StyledBackground)
        self.setAutoFillBackground(True)
        
        # Setup animation timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(self.point_duration)

    def paintEvent(self, event):
        if self.current_point_index >= len(self.pattern_points):
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get current point
        current_point = self.pattern_points[self.current_point_index]
        
        # Get next point if available
        next_point = None
        if self.current_point_index < len(self.pattern_points) - 1:
            next_point = self.pattern_points[self.current_point_index + 1]

        # Draw direction arrow if enabled and next point exists
        if self.show_direction and next_point:
            arrow_color = QColor(*self.colors['direction_arrow'])
            painter.setPen(arrow_color)
            painter.drawLine(current_point, next_point)
            
            # Draw arrow head
            angle = 30  # Arrow head angle
            arrow_length = 20  # Arrow head length
            dx = next_point.x() - current_point.x()
            dy = next_point.y() - current_point.y()
            line_length = (dx*dx + dy*dy)**0.5
            
            if line_length > 0:
                dx, dy = dx/line_length, dy/line_length
                x1 = next_point.x() - arrow_length * (dx*0.866 + dy*0.5)
                y1 = next_point.y() - arrow_length * (-dx*0.5 + dy*0.866)
                x2 = next_point.x() - arrow_length * (dx*0.866 - dy*0.5)
                y2 = next_point.y() - arrow_length * (dx*0.5 + dy*0.866)
                
                points = [next_point, QPoint(int(x1), int(y1)), QPoint(int(x2), int(y2))]
                painter.setBrush(arrow_color)
                painter.drawPolygon(*points)

        # Draw current point
        point_color = QColor(*self.colors['current_point'])
        painter.setPen(Qt.NoPen)
        painter.setBrush(point_color)
        point_size = self.point_config['size'] * self.point_config.get('size_multiplier', 1)
        painter.drawEllipse(current_point, point_size, point_size)

    def update_animation(self):
        """Update the animation state"""
        if self.current_point_index >= len(self.pattern_points):
            self.animation_timer.stop()
            return

        self.current_point_index += 1
        self.update()

    def stop_animation(self):
        """Stop the animation timer"""
        self.animation_timer.stop()

    def start_animation(self):
        """Start the animation timer"""
        self.animation_timer.start(self.point_duration)

class SaccadePursuitWidget(QWidget):
    def __init__(self, display_widget, config_path="config.yaml", wrapper=None):
        super().__init__()
        self.setWindowTitle("Saccade Pattern")
        
        self.load_config(config_path)
        self.init_variables()
        self.display_widget = display_widget
        
        self.pattern = SaccadePattern(config_path, self.display_widget, self.display_widget.current_saccade_part)


    def init_variables(self):
        """Initialize variables for animation"""
        self.current_point_index = 0
        self.state = 'countdown'
        self.countdown_value = self.countdown_seconds
        self.pattern_points = self._generate_grid_points()

    def start_animation(self):
        self.hide()
        self.close()
        self.pattern.run()

    def end_animation(self):
        print("End of animation")
        cv2.destroyAllWindows()
        # Close itself after animation ends
        self.close()
        self.hide()

        if self.display_widget.is_recording:
            self.display_widget.stop_recording()

    def on_countdown_finished(self):
        pass

    def load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Error reading config file: {e}")
            raise

        # Initialize pattern parameters from config
        pattern_config = self.config['pattern']
        self.num_rows = pattern_config['num_rows']
        self.num_cols = pattern_config['num_cols']
        self.num_points = min(pattern_config['num_points'], self.num_rows * self.num_cols)
        self.margin = pattern_config['margin']
        self.show_direction = pattern_config.get('show_direction', True)

        # Timing configuration
        timing_config = self.config['timing']
        self.point_duration = int(timing_config['point_duration'] * 1000)  # Convert to milliseconds
        self.countdown_seconds = timing_config['countdown_seconds']
        self.thank_you_duration = int(timing_config['thank_you_duration'] * 1000)

        # Colors
        self.colors = self.config['colors']
        self.bg_color = QColor(*self.colors['background'])
        self.point_color = QColor(*self.colors['current_point'])
        self.text_color = QColor(*self.colors['text'])
        self.heart_color = QColor(*self.colors['heart'])

    def _generate_grid_points(self):
        """Generate grid points for the pattern"""
        points = []
        screen = QDesktopWidget().screenGeometry()
        width, height = screen.width(), screen.height()
        
        row_spacing = (height - 2 * self.margin) / (self.num_rows - 1)
        col_spacing = (width - 2 * self.margin) / (self.num_cols - 1)
        
        for row in range(self.num_rows):
            y = self.margin + row * row_spacing
            for col in range(self.num_cols):
                x = self.margin + col * col_spacing
                points.append(QPoint(int(x), int(y)))
        
        # Randomly select required points if specified
        if hasattr(self, 'num_points'):
            import random
            random.shuffle(points)
            points = points[:self.num_points]
            
        return points

    # def closeEvent(self, event):
    #     # Make sure to clean up CV2 windows when widget is closed
    #     cv2.destroyAllWindows()
    #     # self.display_widget.show()  # Show the main window again
    #     super().closeEvent(event)
    #     self.close()


# def main():
#     app = QApplication(sys.argv)

#     # Create a dummy display widget
#     display_widget = QWidget()
#     display_widget.setStyleSheet("background-color: lightblue;")

#     # Create and show the Saccade widget
#     window = SaccadePursuitWidget(display_widget)
#     window.show()

#     sys.exit(app.exec_())