import os
import random
import cv2
import numpy as np
import time
from screeninfo import get_monitors
import yaml
import csv
from datetime import datetime
import math

class SaccadePattern:
    def __init__(self, config_path="config.yaml", widget=None, random_part_no=0):
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Error reading config file: {e}")
            raise

        self.widget = widget
        self.is_fullscreen = True
        self.random_part_no = random_part_no  # New parameter for part selection

        # Get screen dimensions
        self.monitor = get_monitors()[0]
        self.width = self.monitor.width
        self.height = self.monitor.height
        
        self.root_path = self.config['save']['root_path']
        os.makedirs(self.root_path, exist_ok=True)

        # Initialize pattern parameters from config
        pattern_config = self.config['pattern']
        self.num_rows = pattern_config['num_rows']
        self.num_cols = pattern_config['num_cols']
        self.num_points = min(pattern_config['num_points'], self.num_rows * self.num_cols)
        self.margin = pattern_config['margin']
        self.seed = pattern_config.get('seed', 42)  # Default seed if not specified
        self.show_direction = pattern_config.get('show_direction', True)
        
        # Initialize timing parameters
        timing_config = self.config['timing']
        self.point_delay = timing_config['point_duration']
        
        try:
            self.countdown_seconds = widget.recording_waiting_time
        except:
            self.countdown_seconds = timing_config['countdown_seconds']

        self.thank_you_duration = timing_config['thank_you_duration']
        
        # Initialize window
        window_config = self.config['window']
        self.window_name = window_config['name']
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        # Initialize log file
        self.log_file = os.path.join(self.root_path, widget.current_log_filename) if widget else "saccade_log.csv"
        
        with open(self.log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp_ms', 'Point_Index', 'X', 'Y', 'Next_X', 'Next_Y', 'Screen_Width', 'Screen_Height'])
        
        # Generate grid points
        random.seed(self.seed)
        self.points = self._generate_grid_points()
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
        return True

    def _generate_grid_points(self):
        """Generate grid points and select random required number of points"""
        # Generate all grid points
        all_points = []
        row_spacing = (self.height - 2 * self.margin) / (self.num_rows - 1)
        col_spacing = (self.width - 2 * self.margin) / (self.num_cols - 1)
        
        for row in range(self.num_rows):
            y = self.margin + row * row_spacing
            for col in range(self.num_cols):
                x = self.margin + col * col_spacing
                all_points.append((int(x), int(y)))
        
        # Randomly shuffle all points with fixed seed
        random.seed(self.seed)
        random.shuffle(all_points)
        
        # Take only the number of points we need
        filtered_points = all_points[:self.num_points]
        
        # Divide points into 10 equal parts
        points_per_part = math.ceil(len(filtered_points) / 10)
        
        # Ensure random_part_no is between 0 and 9
        part_index = max(0, min(9, self.random_part_no))
        
        # Get the points for the selected part
        start_idx = part_index * points_per_part
        end_idx = min(start_idx + points_per_part, len(filtered_points))
        
        selected_points = filtered_points[start_idx:end_idx]
        
        return selected_points

    def log_point(self, timestamp_ms, point_index, current_point, next_point=None):
        """Log point data to CSV file"""
        with open(self.log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            next_x = next_point[0] if next_point else None
            next_y = next_point[1] if next_point else None
            writer.writerow([timestamp_ms, point_index, current_point[0], current_point[1], 
                           next_x, next_y, self.width, self.height])

    def _create_blank_image(self):
        """Create blank background image"""
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

    def cleanup(self):
        """Clean up resources and close windows"""
        cv2.destroyAllWindows()

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

    def run(self):
        """Run main program"""
        # Initial window setup
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        if not self.show_countdown():
            return

        image = self._create_blank_image()
        point_config = self.config['point']
        colors = self.config['colors']
        current_timestamp = 0
        
        try:
            point_count = 0
            
            for i, current_point in enumerate(self.points):
                # Check if we should continue running
                if hasattr(self.widget, 'is_recording') and not self.widget.is_recording:
                    self.cleanup()
                    return False

                next_point = self.points[i + 1] if i < len(self.points) - 1 else None
                current_frame = image.copy()

                try:
                    timestamp_ms = self.widget.events[-1][3] if self.widget else int(time.time() * 1000)
                    current_timestamp = timestamp_ms
                except Exception as e:
                    timestamp_ms = current_timestamp

                point_count += 1
                self.log_point(timestamp_ms, i, current_point, next_point)

                # Draw current point
                cv2.circle(current_frame, current_point,
                          int(point_config['size'] * point_config.get('size_multiplier', 1)),
                          tuple(colors['current_point']),
                          point_config['thickness'])

                # Draw direction arrow if enabled
                if self.show_direction and next_point:
                    cv2.arrowedLine(current_frame, current_point, next_point,
                                  tuple(colors['direction_arrow']), 2, tipLength=0.2)

                cv2.imshow(self.window_name, current_frame)
                
                if not self._wait_key(self.point_delay):
                    return

            # Show thank you message at the end
            self.show_thank_you()
            
        finally:
            self.cleanup()

def main():
    # You can specify the part number (0-9) as the third parameter
    pattern = SaccadePattern("config/config_saccade.yaml", random_part_no=0)
    pattern.run()

if __name__ == "__main__":
    main()