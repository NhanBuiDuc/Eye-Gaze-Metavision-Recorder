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
    def __init__(self, config_path="config.yaml", widget=None):
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
        
        self.root_path = self.config['save']['root_path']
        os.makedirs(self.root_path, exist_ok=True)

        # Initialize pattern parameters from config
        pattern_config = self.config['pattern']
        self.num_points = pattern_config['num_points']
        self.margin = pattern_config['margin']
        self.seed = pattern_config.get('seed', 42)  # Default seed if not specified
        self.show_direction = pattern_config.get('show_direction', True)
        
        # Center-based pattern config
        self.num_circles = 6  # Number of concentric circles
        self.points_per_circle = self.num_points // self.num_circles
        self.max_radius = min(self.width, self.height) // 2 - self.margin
        
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
        
        # Generate concentric circle points
        random.seed(self.seed)
        self.points = self._generate_concentric_circle_points()
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

    def _generate_concentric_circle_points(self):
        """Generate points in concentric circles around the center of the screen"""
        center_x = self.width // 2
        center_y = self.height // 2
        all_points = []
        
        # Create points for each concentric circle
        for circle_idx in range(self.num_circles):
            # Calculate radius for this circle
            radius = (circle_idx + 1) * (self.max_radius / self.num_circles)
            
            # Calculate number of points for this circle
            # More points for outer circles to maintain roughly equal spacing
            num_points_in_circle = int(self.points_per_circle * (circle_idx + 1))
            
            # Generate points in a clockwise order around the circle
            for point_idx in range(num_points_in_circle):
                angle = 2 * math.pi * point_idx / num_points_in_circle
                x = center_x + int(radius * math.cos(angle))
                y = center_y + int(radius * math.sin(angle))
                all_points.append((x, y))
        
        # Limit to the requested number of points
        return all_points[:self.num_points]

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

                try:
                    timestamp_ms = self.widget.events[-1][3] if self.widget else int(time.time() * 1000)
                    current_timestamp = timestamp_ms
                except Exception as e:
                    timestamp_ms = current_timestamp

                point_count += 1
                self.log_point(timestamp_ms, i, current_point, next_point)
                
                # Start time for this specific point
                point_start_time = time.time()
                
                # Display this point with countdown until point_delay is reached
                while True:
                    current_frame = image.copy()
                    
                    # Calculate remaining time for this point
                    elapsed = time.time() - point_start_time
                    remaining = max(0, self.point_delay - elapsed)
                    
                    # Draw current point
                    cv2.circle(current_frame, current_point,
                            int(point_config['size'] * point_config.get('size_multiplier', 1)),
                            tuple(colors['current_point']),
                            point_config['thickness'])

                    # Draw direction arrow if enabled
                    if self.show_direction and next_point:
                        cv2.arrowedLine(current_frame, current_point, next_point,
                                    tuple(colors['direction_arrow']), 2, tipLength=0.2)
                    
                    # Calculate which circle this point belongs to for display purposes
                    center_x = self.width // 2
                    center_y = self.height // 2
                    current_circle = 0
                    
                    for circle_idx in range(self.num_circles):
                        points_so_far = 0
                        for c in range(circle_idx + 1):
                            points_so_far += int(self.points_per_circle * (c + 1))
                            if i < points_so_far:
                                current_circle = c + 1
                                break
                        if current_circle > 0:
                            break
                            
                    # Display countdown text and circle info
                    running_time_text = f"{remaining:.1f}s"
                    circle_text = f"Circle {current_circle}/{self.num_circles}"
                    countdown_text = f"{int(point_count)}/{len(self.points)}"

                    running_time_text_x = current_point[0] - 30
                    running_time_text_y = current_point[1] + 40

                    circle_text_x = current_point[0] - 30
                    circle_text_y = current_point[1] + 70

                    countdown_text_x = current_point[0] - 30
                    countdown_text_y = current_point[1] - 40

                    cv2.putText(current_frame, running_time_text,
                                (running_time_text_x, running_time_text_y),
                                getattr(cv2, self.config['font']['type']),
                                0.8,  # Font scale
                                tuple(colors['text']),
                                2)  # Thickness
                                
                    cv2.putText(current_frame, circle_text,
                                (circle_text_x, circle_text_y),
                                getattr(cv2, self.config['font']['type']),
                                0.8,  # Font scale
                                tuple(colors['text']),
                                2)  # Thickness

                    cv2.putText(current_frame, countdown_text,
                                (countdown_text_x, countdown_text_y),
                                getattr(cv2, self.config['font']['type']),
                                0.8,  # Font scale
                                tuple(colors['text']),
                                2)  # Thickness
                    
                    cv2.imshow(self.window_name, current_frame)
                    
                    # Check for key press and handle it
                    key = cv2.waitKey(1) & 0xFF
                    if key != 255 and not self._handle_keyboard_input(key):
                        return
                    
                    # Break the loop when point_delay is reached
                    if remaining <= 0:
                        break
                    
                    # Small sleep to avoid hogging CPU
                    time.sleep(0.01)

            # # Show thank you message at the end
            # self.show_thank_you()
            return
        
        finally:
            self.cleanup()

# def main():
#     pattern = SaccadePattern("config/config_saccade.yaml")
#     pattern.run()

# if __name__ == "__main__":
#     main()