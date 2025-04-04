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
import time

class SaccadePursuitPattern:
    def __init__(self, part, config_path=None, widget=None):
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Error reading config file: {e}")
            raise
        
        self.widget = widget
        self.is_fullscreen = True
        if part == 1:
            self.direction_first = "horizontal"
            self.margin_size = "small"
        if part == 2:
            self.direction_first = "horizontal"
            self.margin_size = "medium"
        if part == 3:
            self.direction_first = "horizontal"
            self.margin_size = "large"
        if part == 4:
            self.direction_first = "vertical"
            self.margin_size = "small"
        if part == 5:
            self.direction_first = "vertical"
            self.margin_size = "medium"
        if part == 6:
            self.direction_first = "vertical"
            self.margin_size = "large"
        self.total_num_points = self.config['pattern'].get('num_points', 50)
        # Get screen dimensions
        self.monitor = get_monitors()[0]
        self.width = self.monitor.width
        self.height = self.monitor.height

        self.countdown_xy = [50, 200]
        # Initialize pattern parameters from config
        pattern_config = self.config['pattern']
        self.num_rows = pattern_config.get('num_rows', 10)
        self.points_per_row = pattern_config.get('points_per_row', pattern_config.get('num_cols', 20))
        self.margin = pattern_config.get('margin', 50)
        self.tail_points = pattern_config.get('tail_points', 10)
        
        # Initialize timing parameters based on margin size
        timing_config = self.config['timing']
        if self.margin_size == "small":
            self.point_delay = 1.2 # 0.5 seconds for medium margin
        elif self.margin_size == "medium":
            self.point_delay = 1.5  # 0.5 seconds for medium margin
        else:  # large
            self.point_delay = 1.5  # 1.0 second for large margin
            
        try:
            self.countdown_seconds = widget.recording_waiting_time if widget else timing_config.get('countdown_seconds', 3)
        except:
            self.countdown_seconds = timing_config.get('countdown_seconds', 3)
            
        # Initialize window
        window_config = self.config['window']
        self.window_name = window_config.get('name', 'Smooth Pursuit Pattern')
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        # Initialize log file
        self.log_file = widget.current_label_filename if widget else "saccade_log.csv"
        with open(self.log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp_ms', 'Point_Index', 'X', 'Y', 'Next_X', 'Next_Y', 'Screen_Width', 'Screen_Height'])
        
        self.start_time = None
        
        # Pre-calculate all points
        self.all_points = self.calculate_all_points()

    def calculate_all_points(self):
        """
        Calculate all points for the zigzag pattern based on the margin_size parameter
        and direction_first parameter.
        
        Returns:
            List of tuples (row, point_index, x, y) for each point in the pattern.
        """
        all_points = []


        current_point = [50, 50]  # Start from top-left with margin
        starting_x = 50
        starting_y = 50 
        # Extract x and y from the starting point
        x, y = current_point
        if self.margin_size == "small":
            h_quarter_step_full = int(self.width * 0.25)  # 25% of screen width
            v_quarter_step_full = int(self.height * 0.25)  # 25% of screen height 
        # Calculate step sizes based on margin_size and total_num_points
        elif self.margin_size == "medium":
            h_half_step_full = int(self.width * 0.5)  # 50% of screen width
            v_half_step_full = int(self.height * 0.5)  # 50% of screen height
        else:  # large
            h_step_full = int(self.width - starting_x - 50)
            v_step_full = int(self.height - starting_x - 50)
        
        # Calculate vertical and horizontal steps to distribute points evenly
        if self.direction_first == "horizontal":
            if self.margin_size == "small":
                quater_num_points = self.total_num_points // 4
                current_usable_height = self.height - starting_y - 50
                v_step = int(current_usable_height // quater_num_points)            
            elif self.margin_size == "medium":
                half_num_points = self.total_num_points // 2
                current_usable_height = self.height - starting_y - 50
                v_step = int(current_usable_height // half_num_points)
            elif self.margin_size == "large":
                current_usable_height = self.height - starting_y
                v_step = int(current_usable_height // self.total_num_points)
        else:  # vertical
            if self.margin_size == "small":
                quater_num_points = self.total_num_points // 4
                current_usable_width = self.width - starting_x - 50
                h_step = int(current_usable_width // quater_num_points)
            elif self.margin_size == "medium":
                half_num_points = self.total_num_points // 2
                current_usable_width = self.width - starting_x - 50
                h_step = int(current_usable_width // half_num_points)
            elif self.margin_size == "large":
                current_usable_width = self.width - starting_x - 50
                h_step = int(current_usable_width // self.total_num_points)
        
        left = True # Alternate between left and right
        up = True

        x = starting_x
        y = starting_y
        touch_boundary = False
        nth_boundary_tourch = 0
        for i in range(self.total_num_points):
            if self.direction_first == "horizontal":
                if self.margin_size == "small":
                    if nth_boundary_tourch == 0:
                        if left:
                            x = starting_x  # half screen size
                            left = False
                        else:
                            x = h_quarter_step_full - 50 # half screen size
                            left = True
                        y = y + v_step
                    elif nth_boundary_tourch == 1:
                        if left:
                            x = h_quarter_step_full # half screen size
                            left = False
                        else:
                            x = h_quarter_step_full * 2  - 50  # half screen size
                            left = True
                        y = y - v_step
                    elif nth_boundary_tourch == 2:
                        if left:
                            x = h_quarter_step_full * 2 # half screen size
                            left = False
                        else:
                            x = h_quarter_step_full * 3 - 50  # half screen size
                            left = True
                        y = y + v_step
                    elif nth_boundary_tourch == 3:
                        if left:
                            x = h_quarter_step_full * 3 # half screen size
                            left = False
                        else:
                            x = h_quarter_step_full * 4 - 50 # half screen size
                            left = True
                        y = y - v_step
                    if nth_boundary_tourch % 2 == 0:
                        if (y + v_step) > self.height - 50:
                            nth_boundary_tourch += 1
                            left = True
                    else:
                        if (y - v_step) < 50:
                            nth_boundary_tourch += 1
                            left = True
                if self.margin_size == "medium":
                    if not touch_boundary:
                        if left:
                            x = starting_x  # half screen size
                            left = False
                        else:
                            x = starting_x + h_half_step_full - 50 # half screen size
                            left = True
                        y = y + v_step
                    else:
                        if left:
                            x = h_half_step_full  # half screen size
                            left = False
                        else:
                            x = h_half_step_full + h_half_step_full - 50 # half screen size
                            left = True
                        y = y - v_step
                    if (y + v_step) > self.height - 50:
                        touch_boundary = True
                        left = True
                elif self.margin_size == "large":
                    if left:
                        x = starting_x  # half screen size
                        left = False
                    else:
                        x = starting_x + h_step_full - 50  # half screen size
                        left = True
                    y = y + v_step
        
            elif self.direction_first == "vertical":
                if self.margin_size == "small":
                    if nth_boundary_tourch == 0:
                        if up:
                            y = starting_y  # half screen size
                            up = False
                        else:
                            y= v_quarter_step_full - 50 # half screen size
                            up = True
                        x = x + h_step
                    elif nth_boundary_tourch == 1:
                        if up:
                            y = v_quarter_step_full # half screen size
                            up = False
                        else:
                            y = v_quarter_step_full * 2  - 50  # half screen size
                            up = True
                        x = x - h_step
                    elif nth_boundary_tourch == 2:
                        if up:
                            y = v_quarter_step_full * 2 # half screen size
                            up = False
                        else:
                            y = v_quarter_step_full * 3 - 50  # half screen size
                            up = True
                        x = x + h_step
                    elif nth_boundary_tourch == 3:
                        if up:
                            y = v_quarter_step_full * 3 # half screen size
                            up = False
                        else:
                            y = v_quarter_step_full * 4 - 50 # half screen size
                            up = True
                        x = x - h_step
                    if nth_boundary_tourch % 2 == 0:
                        if (x + h_step) > self.width - 50:
                            nth_boundary_tourch += 1
                            up = True
                    else:
                        if (x - h_step) < 50:
                            nth_boundary_tourch += 1
                            up = True
                if self.margin_size == "medium":
                    if not touch_boundary:
                        if up:
                            y = starting_y
                            up = False
                        else:
                            y = starting_y + v_half_step_full - 50 # half screen size
                            up = True
                        x = x + h_step
                    else:
                        if up:
                            y = v_half_step_full  # half screen size
                            up = False
                        else:
                            y = v_half_step_full + v_half_step_full - 50 # half screen size
                            up = True
                        x = x - h_step
                    if (x + h_step) > self.width - 50:
                        touch_boundary = True
                        up = True
                elif self.margin_size == "large":
                    if up:
                        y = starting_y  # half screen size
                        up = False
                    else:
                        y = starting_y + v_step_full  # half screen size
                        up = True
                    x = x + h_step
            
            # Add the new point to the list
            all_points.append([x, y])
        
        return all_points
                
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
        line_colors = self.config['colors']["line"]
        try:
            point_count = 0
            
            for i, current_point in enumerate(self.all_points):
                # Check if we should continue running
                if hasattr(self.widget, 'is_recording') and not self.widget.is_recording:
                    self.cleanup()
                    return False

                next_point = self.all_points[i+1] if i < len(self.all_points) - 1 else None

                try:
                    timestamp_ms = self.widget.events[-1][3] if self.widget else int(time.time() * 1000)
                    current_timestamp = timestamp_ms
                except Exception as e:
                    timestamp_ms = current_timestamp

                point_count += 1
                self.log_point(timestamp_ms, point_count, current_point, next_point)
                
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
                    if next_point:
                        cv2.line(current_frame, current_point, next_point, line_colors, 1, cv2.LINE_AA)

                    # Display countdown text below the circle

                    running_time_text = f"{remaining:.1f}s"
                    countdown_text = f"{int(point_count)}/{len(self.all_points) }"

                    running_time_text_x = current_point[0] - 30  # Adjust for text width
                    running_time_text_y = current_point[1] + 40  # Position below the circle


                    countdown_text_x = current_point[0] - 30  # Adjust for text width
                    countdown_text_y = current_point[1] - 40  # Position below the circle

                    cv2.putText(current_frame, running_time_text,
                                (running_time_text_x, running_time_text_y),
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

    def log_point(self, timestamp_ms, point_index, current_point, next_point=None):
        """Log point data to CSV file"""
        if next_point:
            with open(self.log_file, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([timestamp_ms, point_index, current_point[0], current_point[1], next_point[0], next_point[1], self.width, self.height])
        else:
            with open(self.log_file, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([timestamp_ms, point_index, current_point[0], current_point[1], 0, 0, self.width, self.height])        
    def _create_blank_image(self):
        """Create dark royal blue background image"""
        bg_color = self.config.get('colors', {}).get('background', [50, 20, 205])
        print(f"Creating background with color: {bg_color}")
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        image[:] = bg_color
        # Check a pixel to verify
        print(f"Pixel color check: {image[0,0]}")
        return image

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
        text_config = self.config.get('countdown_text', {})
        colors = self.config.get('colors', {})
        text_color = colors.get('text', [255, 255, 255])  # Default white if not specified
        
        for i in range(self.countdown_seconds, 0, -1):
            image = self._create_blank_image()
            text = str(i)

            # Calculate center position
            text_size = cv2.getTextSize(
                text, 
                getattr(cv2, self.config.get('font', {}).get('type', 'FONT_HERSHEY_SIMPLEX')), 
                text_config.get('font_scale', 5),
                text_config.get('thickness', 5)
            )[0]

            position = self.countdown_xy
            
            cv2.putText(image, text, 
                       tuple(position),
                       getattr(cv2, self.config.get('font', {}).get('type', 'FONT_HERSHEY_SIMPLEX')), 
                       text_config.get('font_scale', 5),
                       tuple(text_color),
                       text_config.get('thickness', 5))
            cv2.imshow(self.window_name, image)
            
            if not self._wait_key(1.0):
                return False
        return True
    
    def cleanup(self):
        """Clean up resources and close windows"""
        cv2.destroyAllWindows()
        # Add any additional cleanup needed

# Example usage:
# pattern = SaccadePursuitPattern(
#     config_path="config/config_saccade.yaml",
#     part=4
# )
# pattern.run()