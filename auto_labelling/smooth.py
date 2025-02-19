import random
import cv2
import numpy as np
import time
from screeninfo import get_monitors
import yaml
import csv
from datetime import datetime

from widgets.metavsion_widgetv1 import MetavisionWidget

class SmoothPursuitPattern:
    def __init__(self, config_path="config.yaml", widget: MetavisionWidget=None):
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Error reading config file: {e}")
            raise

        self.widget = widget
        self.is_fullscreen = True

        # Get screen dimensions
        self.monitor = get_monitors()[0]
        self.width = self.monitor.width
        self.height = self.monitor.height
        
        # Initialize pattern parameters from config
        pattern_config = self.config['pattern']
        self.num_rows = pattern_config['num_rows']
        self.points_per_row = pattern_config['points_per_row']
        self.margin = pattern_config['margin']
        self.tail_points = pattern_config['tail_points']
        
        # Initialize timing parameters
        timing_config = self.config['timing']
        self.point_delay = timing_config['point_delay']
        self.countdown_seconds = timing_config['countdown_seconds']
        self.thank_you_duration = timing_config['thank_you_duration']
        
        # Initialize window
        window_config = self.config['window']
        self.window_name = window_config['name']
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        # Initialize log file
        self.log_file = f"smooth_log.csv"
        with open(self.log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp_ms', 'Row', 'Point_Index', 'X', 'Y', 'Screen_Width', 'Screen_Height'])
        
        self.start_time = None

    def _handle_keyboard_input(self, key):
        """Handle keyboard events for window control"""
        if key == ord('f') or key == ord('F'):  # F key for fullscreen toggle
            self.is_fullscreen = not self.is_fullscreen
            if self.is_fullscreen:
                cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
            return True
        elif key == 27:  # ESC key to exit
            return False
        return True

    def log_point(self, timestamp_ms, row, point_index, x, y):
        """Log point data to CSV file"""
        with open(self.log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp_ms, row, point_index, x, y, self.width, self.height])

    def _create_blank_image(self):
        """Create white background image"""
        bg_color = self.config['colors']['background']
        return np.array(bg_color, dtype=np.uint8) * np.ones((self.height, self.width, 3))

    def _wait_key(self, duration):
        """Wait for keyboard input for specified duration"""
        start_time = time.time()
        while (time.time() - start_time) < duration:
            key = cv2.waitKey(1) & 0xFF
            if key != 255:  # If a key was pressed
                return self._handle_keyboard_input(key)
        return True

    def show_countdown(self):
        """Display countdown"""
        text_config = self.config['countdown_text']
        colors = self.config['colors']
        
        for i in range(self.countdown_seconds, 0, -1):
            image = self._create_blank_image()
            text = str(i)
            cv2.putText(image, text, 
                       tuple(text_config['position']),
                       getattr(cv2, self.config['font']['type']), 
                       text_config['font_scale'],
                       tuple(colors['text']),
                       text_config['thickness'])
            cv2.imshow(self.window_name, image)
            
            if not self._wait_key(1.0):
                return False
        return True

    def draw_heart(self, image, center, size):
        """Draw heart shape"""
        heart_color = tuple(self.config['colors']['heart'])
        x, y = center
        radius = size // 2
        
        cv2.circle(image, (x - radius, y), radius, heart_color, -1)
        cv2.circle(image, (x + radius, y), radius, heart_color, -1)
        
        triangle_pts = np.array([
            [x - size, y],
            [x + size, y],
            [x, y + size]
        ])
        cv2.fillPoly(image, [triangle_pts], heart_color)

    def show_thank_you(self):
        """Show thank you message with heart icon"""
        text_config = self.config['thank_you_text']
        heart_config = self.config['heart']
        colors = self.config['colors']
        
        image = self._create_blank_image()
        messages = text_config['messages']
        text = random.choice(messages)
        
        font = getattr(cv2, self.config['font']['type'])
        font_scale = text_config['font_scale']
        thickness = text_config['thickness']
        
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        heart_size = heart_config['size']
        
        total_width = text_size[0] + heart_config['offset'] + heart_size * 2
        center_x = self.width // 2
        center_y = self.height // 2
        
        text_x = center_x - total_width // 2
        text_y = center_y + text_size[1] // 2
        
        cv2.putText(image, text,
                    (text_x, text_y),
                    font,
                    font_scale,
                    tuple(colors['text']),
                    thickness)
        
        heart_x = text_x + text_size[0] + heart_config['offset']
        heart_y = text_y - text_size[1] // 2
        self.draw_heart(image, (heart_x, heart_y), heart_size)
        
        cv2.imshow(self.window_name, image)
        if not self._wait_key(self.thank_you_duration):
            return False
        return True

    def calculate_row_points(self, row_index):
        """Calculate coordinates for points in a row"""
        row_height = (self.height - 2 * self.margin) / (self.num_rows - 1)
        y = self.margin + row_index * row_height
        row_width = self.width - 2 * self.margin
        
        if row_index % 2 == 0:  # Even rows: left to right
            points = [(self.margin + i * row_width/(self.points_per_row-1), y) 
                     for i in range(self.points_per_row)]
        else:  # Odd rows: right to left
            points = [(self.width - self.margin - i * row_width/(self.points_per_row-1), y) 
                     for i in range(self.points_per_row)]
        
        return points

    def run(self):
        """Run main program"""
        # Initial window setup
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        if not self.show_countdown():
            return

        image = self._create_blank_image()
        point_config = self.config['point']
        point_color = tuple(self.config['colors']['point'])
        current_timestamp = 0
        
        try:
            tail_history = []
            point_count = 0
            
            for row in range(self.num_rows):
                points = self.calculate_row_points(row)
                
                for point_index, (x, y) in enumerate(points):
                    current_frame = image.copy()
                    try:
                        timestamp_ms = self.widget.events[-1][3]
                        current_timestamp = timestamp_ms
                    except Exception as e: 
                        timestamp_ms = current_timestamp

                    point_count += 1
                    self.log_point(timestamp_ms, row, point_index, int(x), int(y))
                    
                    tail_history.append((int(x), int(y)))
                    if len(tail_history) > self.tail_points:
                        tail_history.pop(0)
                    
                    # Draw trail points
                    for px, py in tail_history[:-1]:
                        cv2.circle(current_frame, (px, py),
                                 point_config['size'],
                                 point_color,
                                 point_config['thickness'])
                    
                    # Draw current point
                    if tail_history:
                        latest_x, latest_y = tail_history[-1]  
                        cv2.circle(current_frame, (latest_x, latest_y),
                                 point_config['size'] * 2,  
                                 point_color,
                                 point_config['thickness'])
                        
                    cv2.imshow(self.window_name, current_frame)
                    
                    if not self._wait_key(self.point_delay):
                        return
            
            return
        finally:
            cv2.destroyAllWindows()

def main():
    pattern = SmoothPursuitPattern("config/config_smooth.yaml")
    pattern.run()

if __name__ == "__main__":
    main()