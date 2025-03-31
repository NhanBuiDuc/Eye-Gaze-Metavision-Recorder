import os
import random
import cv2
import numpy as np
import time
from screeninfo import get_monitors
import yaml
import csv
from datetime import datetime

class SmoothPursuitPattern:
    def __init__(self, config_path="config\config_saccade.yaml", widget=None, horizontal_direction="left2right", vertical_direction="top2bottom", direction_first = "Horizontal"):
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(f"Error reading config file: {e}")
            raise

        self.widget = widget
        self.is_fullscreen = True
        
        # Set direction parameters
        self.horizontal_direction = horizontal_direction
        self.vertical_direction = vertical_direction
        self.direction_first = direction_first

        if horizontal_direction not in ["left2right", "right2left"]:
            raise ValueError("horizontal_direction must be 'left2right' or 'right2left'")
            
        if vertical_direction not in ["top2bottom", "bottom2top"]:
            raise ValueError("vertical_direction must be 'top2bottom' or 'bottom2top'")

        # Get screen dimensions
        self.monitor = get_monitors()[0]
        self.width = self.monitor.width
        self.height = self.monitor.height

        # Set countdown position based on starting corner
        if self.horizontal_direction == "left2right" and self.vertical_direction == "top2bottom":
            # Top-left corner
            self.countdown_xy = [40, 120]
        elif self.horizontal_direction == "right2left" and self.vertical_direction == "top2bottom":
            # Top-right corner
            self.countdown_xy = [self.width - 150, 120]
        elif self.horizontal_direction == "left2right" and self.vertical_direction == "bottom2top":
            # Bottom-left corner
            self.countdown_xy = [50, self.height - 80]
        elif self.horizontal_direction == "right2left" and self.vertical_direction == "bottom2top":
            # Bottom-right corner
            self.countdown_xy = [self.width - 150, self.height - 80]

        self.root_path = self.config['save']['root_path']
        os.makedirs(self.root_path, exist_ok=True)

        # Initialize pattern parameters from config
        pattern_config = self.config['pattern']
        self.num_rows = pattern_config['num_rows']
        self.points_per_row = pattern_config['points_per_row']
        self.margin = pattern_config['margin']
        self.tail_points = pattern_config['tail_points']
        
        # Initialize timing parameters
        timing_config = self.config['timing']
        self.point_delay = timing_config['point_delay']
        try:
            self.countdown_seconds = widget.recording_waiting_time
        except:
            self.countdown_seconds = timing_config['countdown_seconds']
        
        # Initialize window
        window_config = self.config['window']
        self.window_name = window_config['name']
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        # Initialize log file
        self.log_file = os.path.join(self.root_path, widget.current_label_filename) if widget else "saccade_log.csv"
        with open(self.log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp_ms', 'Point_Index', 'X', 'Y', 'Next_X', 'Next_Y', 'Screen_Width', 'Screen_Height'])
        
        self.start_time = None
        
        # Pre-calculate all points
        self.all_points = self.calculate_all_points()

    def calculate_all_points(self):
        """
        Calculate all points for the smooth pursuit pattern.
        The pattern can start either horizontally or vertically based on direction_first parameter.
        
        Returns:
            List of tuples (row, point_index, x, y) for each point in the pattern.
        """
        all_points = []
        
        # Calculate the effective area dimensions (taking margins into account)
        effective_width = self.width - 2 * self.margin
        effective_height = self.height - 2 * self.margin
        
        # Calculate spacing between points
        horizontal_spacing = effective_width / (self.points_per_row - 1) if self.points_per_row > 1 else 0
        vertical_spacing = effective_height / (self.num_rows - 1) if self.num_rows > 1 else 0
        
        # If the first direction is horizontal, use the original snake pattern
        if self.direction_first == "Horizontal":
            # Case 1: right2left & top2bottom
            if self.horizontal_direction == "right2left" and self.vertical_direction == "top2bottom":
                # Start from top-right, move left, then down and right, etc.
                for row in range(self.num_rows):
                    # For even rows (0, 2, 4...), go right to left
                    # For odd rows (1, 3, 5...), go left to right
                    is_left_to_right = row % 2 == 1  # True for odd rows, False for even rows
                    
                    # Calculate y-coordinate (top to bottom)
                    y = self.margin + row * vertical_spacing
                    
                    # Generate points for this row
                    for point_index in range(self.points_per_row):
                        # Calculate x-coordinate based on direction
                        if is_left_to_right:
                            x = self.margin + point_index * horizontal_spacing
                        else:
                            x = self.width - self.margin - point_index * horizontal_spacing
                        
                        # Add the point to our list
                        all_points.append((row, point_index, x, y))
            
            # Case 2: left2right & bottom2top
            elif self.horizontal_direction == "left2right" and self.vertical_direction == "bottom2top":
                # Start from bottom-left, move right, then up and left, etc.
                for row in range(self.num_rows):
                    # For even rows (0, 2, 4...), go left to right
                    # For odd rows (1, 3, 5...), go right to left
                    is_left_to_right = row % 2 == 0  # True for even rows, False for odd rows
                    
                    # Calculate y-coordinate (bottom to top)
                    y = self.height - self.margin - row * vertical_spacing
                    
                    # Generate points for this row
                    for point_index in range(self.points_per_row):
                        # Calculate x-coordinate based on direction
                        if is_left_to_right:
                            x = self.margin + point_index * horizontal_spacing
                        else:
                            x = self.width - self.margin - point_index * horizontal_spacing
                        
                        # Add the point to our list
                        all_points.append((row, point_index, x, y))
            
            # Case 3: right2left & bottom2top
            elif self.horizontal_direction == "right2left" and self.vertical_direction == "bottom2top":
                # Start from bottom-right, move left, then up and right, etc.
                for row in range(self.num_rows):
                    # For even rows (0, 2, 4...), go right to left
                    # For odd rows (1, 3, 5...), go left to right
                    is_left_to_right = row % 2 == 1  # True for odd rows, False for even rows
                    
                    # Calculate y-coordinate (bottom to top)
                    y = self.height - self.margin - row * vertical_spacing
                    
                    # Generate points for this row
                    for point_index in range(self.points_per_row):
                        # Calculate x-coordinate based on direction
                        if is_left_to_right:
                            x = self.margin + point_index * horizontal_spacing
                        else:
                            x = self.width - self.margin - point_index * horizontal_spacing
                        
                        # Add the point to our list
                        all_points.append((row, point_index, x, y))
            
            # Case 4: left2right & top2bottom (default case)
            else:
                # Start from top-left, move right, then down and left, etc.
                for row in range(self.num_rows):
                    # For even rows (0, 2, 4...), go left to right
                    # For odd rows (1, 3, 5...), go right to left
                    is_left_to_right = row % 2 == 0  # True for even rows, False for odd rows
                    
                    # Calculate y-coordinate (top to bottom)
                    y = self.margin + row * vertical_spacing
                    
                    # Generate points for this row
                    for point_index in range(self.points_per_row):
                        # Calculate x-coordinate based on direction
                        if is_left_to_right:
                            x = self.margin + point_index * horizontal_spacing
                        else:
                            x = self.width - self.margin - point_index * horizontal_spacing
                        
                        # Add the point to our list
                        all_points.append((row, point_index, x, y))
        
        else:  # self.direction_first == "Vertical"
            # REVERSE THE NUMBER OF POINTS: 
            # Use points_per_row for vertical count and num_rows for horizontal count
            vertical_points = self.points_per_row  # More points vertically
            horizontal_points = self.num_rows      # Fewer points horizontally
            
            # Calculate spacing with reversed point counts
            horizontal_spacing = effective_width / (horizontal_points - 1) if horizontal_points > 1 else 0
            vertical_spacing = effective_height / (vertical_points - 1) if vertical_points > 1 else 0
            
            # Case 1: right2left & top2bottom
            if self.horizontal_direction == "right2left" and self.vertical_direction == "top2bottom":
                # Start from top-right, move down, then left and up, etc.
                for col in range(horizontal_points):
                    # For even columns, go top to bottom; for odd columns, go bottom to top
                    is_top_to_bottom = col % 2 == 0
                    
                    # Calculate x-coordinate (right to left)
                    x = self.width - self.margin - col * horizontal_spacing
                    
                    # Generate points for this column with more vertical points
                    for row_index in range(vertical_points):
                        # Calculate y-coordinate based on direction
                        if is_top_to_bottom:
                            y = self.margin + row_index * vertical_spacing
                        else:
                            y = self.height - self.margin - row_index * vertical_spacing
                        
                        # Add the point to our list
                        all_points.append((col, row_index, x, y))
            
            # Case 2: left2right & bottom2top
            elif self.horizontal_direction == "left2right" and self.vertical_direction == "bottom2top":
                # Start from bottom-left, move up, then right and down, etc.
                for col in range(horizontal_points):
                    # For even columns, go bottom to top; for odd columns, go top to bottom
                    is_top_to_bottom = col % 2 == 1
                    
                    # Calculate x-coordinate (left to right)
                    x = self.margin + col * horizontal_spacing
                    
                    # Generate points for this column with more vertical points
                    for row_index in range(vertical_points):
                        # Calculate y-coordinate based on direction
                        if is_top_to_bottom:
                            y = self.margin + row_index * vertical_spacing
                        else:
                            y = self.height - self.margin - row_index * vertical_spacing
                        
                        # Add the point to our list
                        all_points.append((col, row_index, x, y))
            
            # Case 3: right2left & bottom2top
            elif self.horizontal_direction == "right2left" and self.vertical_direction == "bottom2top":
                # Start from bottom-right, move up, then left and down, etc.
                for col in range(horizontal_points):
                    # For even columns, go bottom to top; for odd columns, go top to bottom
                    is_top_to_bottom = col % 2 == 1
                    
                    # Calculate x-coordinate (right to left)
                    x = self.width - self.margin - col * horizontal_spacing
                    
                    # Generate points for this column with more vertical points
                    for row_index in range(vertical_points):
                        # Calculate y-coordinate based on direction
                        if is_top_to_bottom:
                            y = self.margin + row_index * vertical_spacing
                        else:
                            y = self.height - self.margin - row_index * vertical_spacing
                        
                        # Add the point to our list
                        all_points.append((col, row_index, x, y))
            
            # Case 4: left2right & top2bottom (default case)
            else:
                # Start from top-left, move down, then right and up, etc.
                for col in range(horizontal_points):
                    # For even columns, go top to bottom; for odd columns, go bottom to top
                    is_top_to_bottom = col % 2 == 0
                    
                    # Calculate x-coordinate (left to right)
                    x = self.margin + col * horizontal_spacing
                    
                    # Generate points for this column with more vertical points
                    for row_index in range(vertical_points):
                        # Calculate y-coordinate based on direction
                        if is_top_to_bottom:
                            y = self.margin + row_index * vertical_spacing
                        else:
                            y = self.height - self.margin - row_index * vertical_spacing
                        
                        # Add the point to our list
                        all_points.append((col, row_index, x, y))
        return all_points
        
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
            writer.writerow([timestamp_ms, point_index, x, y, 0, 0, self.width, self.height])

    def _create_blank_image(self):
        """Create dark royal blue background image"""
        bg_color = self.config['colors']['background']
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
        text_config = self.config['countdown_text']
        colors = self.config['colors']
        
        for i in range(self.countdown_seconds, 0, -1):
            image = self._create_blank_image()
            text = str(i)
            cv2.putText(image, text, 
                       tuple(self.countdown_xy),
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
        # Add any additional cleanup needed

    def run(self):
        """Run main program"""
        # Initial window setup
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        if not self.show_countdown():
            return False

        image = self._create_blank_image()
        point_config = self.config['point']
        point_color = tuple(self.config['colors']['point'])
        current_timestamp = 0
        
        try:
            tail_history = []
            global_point_index = 0
            
            for row, point_index, x, y in self.all_points:
                # Check if we should continue running
                if hasattr(self.widget, 'is_recording') and not self.widget.is_recording:
                    self.cleanup()
                    return False
                    
                current_frame = image.copy()
                try:
                    timestamp_ms = self.widget.events[-1][3]
                    current_timestamp = timestamp_ms
                except Exception as e: 
                    timestamp_ms = current_timestamp

                global_point_index += 1

                print(timestamp_ms)
                self.log_point(timestamp_ms, row, point_index, int(x), int(y))
                
                tail_history.append((int(x), int(y)))
                if len(tail_history) > self.tail_points:
                    tail_history.pop(0)
                
                # Draw current point
                if tail_history:
                    latest_x, latest_y = tail_history[-1]  
                    cv2.circle(current_frame, (latest_x, latest_y),
                             point_config['size'] * 2,  
                             point_color,
                             point_config['thickness'])
                    
                cv2.imshow(self.window_name, current_frame)
                
                if not self._wait_key(self.point_delay):
                    return False
            
            return True
        finally:
            self.cleanup()

# Example usage:
# pattern = SmoothPursuitPattern("config/config_smooth.yaml", 
#                                horizontal_direction="left2right", 
#                                vertical_direction="top2bottom")
# pattern.run()