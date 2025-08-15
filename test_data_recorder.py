import cv2
import numpy as np
import time
from screeninfo import get_monitors
import csv
from datetime import datetime
import math
from metavision_core.event_io.raw_reader import initiate_device
from src.entities.bias_settings import BiasSettings
import os
from metavision_core.event_io import EventsIterator
from metavision_sdk_core import PeriodicFrameGenerationAlgorithm, ColorPalette
from metavision_sdk_ui import EventLoop, BaseWindow, MTWindow, UIAction, UIKeyEvent
from threading import Thread

class SaccadePursuitPattern:
    def __init__(self,  folder, person_id=1, total_people=5, part=1, parts_count=3, points_per_part=100, monitor_index=1):
        self.public_path = "public/test_data/"
        self.folder = folder
        if self.folder != "":
            self.current_store_path = os.path.join(self.public_path, self.folder)
            os.makedirs(self.current_store_path, exist_ok=True)
            self.record_path =  os.path.join(self.current_store_path, "record")
            os.makedirs(self.record_path, exist_ok=True)
            self.label_path =  os.path.join(self.current_store_path, "label")
            os.makedirs(self.label_path, exist_ok=True)
        self.recording_file = ""
        self.is_fullscreen = True
        self.person_id = person_id  # 1-based index for person
        self.total_people = total_people
        self.part = part  # Current part (1, 2, or 3)
        self.parts_count = parts_count  # Total number of parts
        self.points_per_part = points_per_part  # Points per part
        
        # Get screen dimensions for the selected monitor
        monitors = get_monitors()
        if len(monitors) <= monitor_index:
            print(f"Warning: Monitor index {monitor_index} not available. Found {len(monitors)} monitors.")
            print("Using primary monitor instead.")
            self.monitor = monitors[0]
        else:
            self.monitor = monitors[monitor_index]
            
        self.width = self.monitor.width
        self.height = self.monitor.height
        
        # Initialize window
        self.window_name = f'Saccade Pattern - Person {person_id} - Part {part}/{parts_count}'
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        # Position window on the correct monitor
        cv2.moveWindow(self.window_name, self.monitor.x, self.monitor.y)
        
        # Click tracking
        self.current_click_count = 0
        self.required_click_count = 3
        self.mouse_callback_set = False
        self.current_point_index = 0
        
        # Circle properties
        self.circle_radius = 10  # Radius for hit detection
        self.display_radius = 10   # Visual radius
        
        # Log file
        self.log_file = f"{self.folder}_id_{person_id}_part_{part}_label.csv"
        self.label_file = os.path.join(self.label_path, self.log_file)
        with open(self.label_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp_ms', 'Point_Index', 'X', 'Y', 'Click_Count', 'Click_X', 'Click_Y', "Status", "Raw_Path"])
        
        # Calculate all possible points on the screen
        self.all_grid_points = self.calculate_all_grid_points()
        
        # Select points for this specific person and part
        self.person_points = self.select_points_for_person_and_part()
        self.bias_file = "eye_tracking_b1.bias"
        self.event_count = 100000
        self.init_metavision()

    def init_metavision(self):
        self.device = initiate_device("")
        # Apply bias settings if provided
        if self.bias_file:
            bias_settings = BiasSettings.from_file(self.bias_file)
            biases = self.device.get_i_ll_biases()
            for name, bias in bias_settings.biases.items():
                biases.set(name, bias.value)
        self.device.get_i_erc_module().enable(True)
        self.device.get_i_erc_module().set_cd_event_count(event_count=self.event_count)
        
        self.mv_iterator = EventsIterator.from_device(device=self.device)
        self.running = True
        self.mv_thread = Thread(target=self.event_loop_and_display, daemon=True)
        self.mv_thread.start()

    def event_loop_and_display(self):
        # Window - Graphical User Interface
        height, width = self.mv_iterator.get_size()  # Camera Geometry
        try:
            with MTWindow(title="Metavision Events Viewer", width=width, height=height,
                        mode=BaseWindow.RenderMode.BGR) as window:
                def keyboard_cb(key, scancode, action, mods):
                    if key == UIKeyEvent.KEY_ESCAPE or key == UIKeyEvent.KEY_Q:
                        window.set_close_flag()
                        self.running = False

                window.set_keyboard_callback(keyboard_cb)

                # Event Frame Generator - use the exact same parameters as in the example
                event_frame_gen = PeriodicFrameGenerationAlgorithm(
                    sensor_width=width, 
                    sensor_height=height, 
                    fps=25,
                    palette=ColorPalette.Dark  # Use Dark palette as in the example
                )

                def on_cd_frame_cb(ts, cd_frame):
                    if not window.should_close():
                        try:
                            window.show_async(cd_frame)
                        except ValueError as e:
                            print(f"Error showing frame: {e}")
                            print(f"Frame shape: {cd_frame.shape if hasattr(cd_frame, 'shape') else 'unknown'}")

                event_frame_gen.set_output_callback(on_cd_frame_cb)

                # Process events
                for evs in self.mv_iterator:
                    if not self.running or window.should_close():
                        break
                    # Store the current event timestamp
                    if len(evs) > 0:
                        self.current_event_timestamp = evs[-1][3]
                    # Dispatch system events to the window
                    EventLoop.poll_and_dispatch()
                    event_frame_gen.process_events(evs)
        except Exception as e:
            print(f"Error in event loop: {e}")


    def start_recording(self, recording_path):
            
        recording_path = os.path.join(self.record_path, recording_path)
        
        self.device.get_i_events_stream().log_raw_data(recording_path)
        print(f'Recording to {recording_path}')

    def stop_recording(self):
        if self.device:
            self.device.get_i_events_stream().stop_log_raw_data()

    def calculate_all_grid_points(self):
        """Calculate all possible grid points on the screen"""
        all_points = []
        
        # For circles of radius 10, each needs a 20×20 pixel square
        self.step_size = 20
        
        # Calculate rows and columns
        self.cols = self.width // self.step_size
        self.rows = self.height // self.step_size
        
        print(f"Grid size: {self.cols}x{self.rows} = {self.cols*self.rows} possible points")
        
        # Generate all grid points
        for row in range(self.rows):
            for col in range(self.cols):
                x = col * self.step_size + (self.step_size // 2)  # Center of the cell
                y = row * self.step_size + (self.step_size // 2)
                all_points.append((x, y, col, row))  # Store x, y coordinates and grid position
        
        return all_points

    def select_points_for_person_and_part(self):
        """Select points for this specific person based on grid distribution and part"""
        # First divide the grid into parts
        rows_per_part = self.rows // self.parts_count
        remaining_rows = self.rows % self.parts_count
        
        # Calculate start and end rows for this part
        start_row = (self.part - 1) * rows_per_part
        end_row = start_row + rows_per_part
        
        # Distribute any remaining rows to the parts
        if self.part <= remaining_rows:
            start_row += (self.part - 1)
            end_row += self.part
        else:
            start_row += remaining_rows
            end_row += remaining_rows
            
        print(f"Person {self.person_id}, Part {self.part}: Using rows {start_row} to {end_row-1}")
        
        # Collect points for this part's grid section
        part_grid_points = []
        for x, y, col, row in self.all_grid_points:
            if start_row <= row < end_row:
                part_grid_points.append((x, y, col, row))
        
        # Now filter points for this specific person within this part's grid
        person_points = []
        
        # Get modular value for this person (0 to total_people-1)
        person_mod = (self.person_id - 1) % self.total_people
        
        # Walk through the grid and select points that match this person's pattern
        for x, y, col, row in part_grid_points:
            # Calculate the position in the pattern cycle
            position_in_cycle = (row * self.cols + col) % self.total_people
            
            # If this position matches this person's assignment, add it
            if position_in_cycle == person_mod:
                person_points.append((x, y, col, row))
        
        # Calculate total points for this person in this part
        total_points = len(person_points)
        print(f"Person {self.person_id}, Part {self.part}: Total {total_points} points available")
        
        # If we have more points than needed, select a subset
        if total_points > self.points_per_part:
            # Select points evenly distributed across the available points
            indices = np.linspace(0, total_points - 1, self.points_per_part, dtype=int)
            selected_points = [person_points[i] for i in indices]
        else:
            selected_points = person_points
            
        print(f"Person {self.person_id}, Part {self.part}: Selected {len(selected_points)} points")
        return selected_points

    def run(self):
        """Run main program"""
        # Initial window setup
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        # Position window on the correct monitor
        cv2.moveWindow(self.window_name, self.monitor.x, self.monitor.y)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        # Show countdown
        self.show_countdown(3)
        
        # Set up mouse callback for clicks
        self.setup_mouse_callback()

        try:
            # Main loop - continue until all points are processed
            while self.current_point_index < len(self.person_points):
                # Get current point
                current_point = self.person_points[self.current_point_index]
                
                # Create a fresh background image
                image = self.create_background()
                
                # Show current point until it gets 3 clicks
                self.display_current_point(image, current_point)
                
                # Reset click count for next point
                self.current_click_count = 0
                self.current_point_index += 1
                
                # Check for exit key
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC key to exit
                    break
                    
            # Show completion message
            self.show_completion_message()
            
        finally:
            self.cleanup()

    def is_point_in_circle(self, click_x, click_y, circle_x, circle_y):
        """Check if a point is inside the circle"""
        distance = math.sqrt((click_x - circle_x)**2 + (click_y - circle_y)**2)
        return distance <= self.circle_radius

    def mouse_callback(self, event, x, y, flags, param):
        """Mouse event callback to handle clicks"""
        if event == cv2.EVENT_LBUTTONDOWN and self.current_point_index < len(self.person_points):

            # Get current point
            current_point = self.person_points[self.current_point_index]
            # Check if click is inside the circle
            is_hit = self.is_point_in_circle(x, y, current_point[0], current_point[1])
            if is_hit:
                status  = ""
                if self.current_click_count < 3:
                    if self.current_click_count == 0:
                        self.recording_file = f"{self.folder}_{self.person_id}_part_{self.part}_{current_point[0]}_{current_point[1]}_record.raw"
                        self.start_recording(self.recording_file)
                        status = "start"
                        print(f"Recording started at event timestamp: {self.current_event_timestamp}")
                    elif self.current_click_count == 1:
                        status = "process"
                    elif self.current_click_count == 2:
                        self.stop_recording()
                        status = "end"
                        print(f"Recording stopped at event timestamp: {self.current_event_timestamp}")

                    # Log every click attempt
                    self.log_point(self.current_event_timestamp, self.current_point_index + 1, 
                                current_point, self.current_click_count, x, y, status, self.recording_file)
                    # Increment click count
                    self.current_click_count += 1
                    print(f"Hit! Click {self.current_click_count}/{self.required_click_count} on point {self.current_point_index + 1}")
            else:
                print(f"Miss! Click outside circle for point {self.current_point_index + 1}")

    def setup_mouse_callback(self):
        """Set up the mouse callback"""
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

    def log_point(self, timestamp_ms, point_index, point, click_count, click_x=None, click_y=None, status = "", file_path = ""):
        """Log point data to CSV file with click count"""
        with open(self.label_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp_ms, point_index, point[0], point[1], click_count, click_x, click_y, status, file_path])

    def create_background(self):
        """Create dark background image"""
        bg_color = [0, 0, 0]  # Black background (BGR)
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        image[:] = bg_color
        return image

    def display_current_point(self, image, point):
        """Display current point until it receives required clicks"""
        x, y, grid_x, grid_y = point
        
        while self.current_click_count < self.required_click_count:
            # Create a fresh copy of the background
            current_frame = image.copy()
            
            # Draw the point
            cv2.circle(current_frame, (x, y), self.display_radius, (0, 0, 255), -1)  # Red filled circle
            
            # Optionally, draw a subtle outline to show clickable area
            cv2.circle(current_frame, (x, y), int(self.display_radius / 2), (0, 100, 255), 1)  # Red outline for hit area
            
            # Display click count
            click_text = f"Clicks: {self.current_click_count}/{self.required_click_count}"
            progress_text = f"Point: {self.current_point_index + 1}/{len(self.person_points)}"
            grid_text = f"Grid: ({grid_x}, {grid_y})"
            overall_text = f"Person {self.person_id} - Part {self.part}/{self.parts_count}"
            
            cv2.putText(current_frame, click_text,
                        (x - 50, y + 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (255, 255, 255), 2)
            
            cv2.putText(current_frame, progress_text,
                        (x - 50, y - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (255, 255, 255), 2)
                        
            cv2.putText(current_frame, grid_text,
                        (x - 50, y - 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (255, 255, 255), 2)
                        
            cv2.putText(current_frame, overall_text,
                        (30, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (255, 255, 255), 2)
            
            # Show the frame
            cv2.imshow(self.window_name, current_frame)
            
            # Check for key press
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key to exit
                self.cleanup()
                exit()
            
            # Small sleep to avoid hogging CPU
            time.sleep(0.01)

    def show_countdown(self, seconds):
        """Display countdown before starting"""
        for i in range(seconds, 0, -1):
            image = self.create_background()
            cv2.putText(image, str(i),
                       (self.width // 2 - 50, self.height // 2),
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       5, (255, 255, 255), 5)
                       
            # Show which person's session this is
            cv2.putText(image, f"Person {self.person_id} - Part {self.part}/{self.parts_count}",
                       (self.width // 2 - 250, self.height // 2 + 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (255, 255, 255), 2)
                       
            cv2.imshow(self.window_name, image)
            cv2.waitKey(1000)
    
    def show_completion_message(self):
        """Show a completion message when all points are processed"""
        image = self.create_background()
        
        # Draw completion message
        cv2.putText(image, "Part Complete!",
                   (self.width // 2 - 200, self.height // 2 - 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 
                   2, (0, 255, 0), 3)
                   
        cv2.putText(image, f"You completed Part {self.part} of {self.parts_count}",
                   (self.width // 2 - 300, self.height // 2 + 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 
                   1, (255, 255, 255), 2)
                   
        next_part_text = "Press any key to exit" if self.part == self.parts_count else f"Next: Run Part {self.part + 1}"
        cv2.putText(image, next_part_text,
                   (self.width // 2 - 200, self.height // 2 + 150),
                   cv2.FONT_HERSHEY_SIMPLEX, 
                   1, (255, 255, 255), 2)
                   
        cv2.imshow(self.window_name, image)
        cv2.waitKey(0)  # Wait for any key press
    
    def cleanup(self):
        """Clean up resources and close windows"""
        cv2.destroyAllWindows()


def main():
    # Get person ID
    try:
        person_id = int(input("Enter person ID (1-20): "))
        if person_id < 1 or person_id > 20:
            print("Person ID must be between 1 and 20")
            return
            
        part = int(input("Enter part (1-3): "))
        if part < 1 or part > 3:
            print("Part must be between 1 and 3")
            return
    except ValueError:
        print("Please enter valid numbers")
        return
    
    # Create and run the pattern for this person and part
    pattern = SaccadePursuitPattern(
        folder="hoang",
        person_id=person_id,
        total_people=20,
        part=part,
        parts_count=3,
        points_per_part=100,
        monitor_index=1  # Use second monitor
    )
    
    # Print available monitors for debugging
    monitors = get_monitors()
    print(f"Found {len(monitors)} monitors:")
    for i, m in enumerate(monitors):
        print(f"Monitor {i}: {m.width}x{m.height} at position ({m.x},{m.y})")
    
    pattern.run()
    
if __name__ == "__main__":
    main()
    

