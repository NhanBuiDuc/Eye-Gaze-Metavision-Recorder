import cv2
import numpy as np
import time
from screeninfo import get_monitors
import csv
from datetime import datetime
from metavision_core.event_io.raw_reader import initiate_device
from src.entities.bias_settings import BiasSettings
import os
from metavision_core.event_io import EventsIterator
from metavision_sdk_core import PeriodicFrameGenerationAlgorithm, ColorPalette
from metavision_sdk_ui import EventLoop, BaseWindow, MTWindow, UIAction, UIKeyEvent
from threading import Thread

class SimplifiedEyeTracker:
    def __init__(self, folder, person_id=1, part=1, parts_count=3, monitor_index=1):
        self.public_path = "public/test_data/"
        self.folder = folder
        if self.folder != "":
            self.current_store_path = os.path.join(self.public_path, self.folder)
            os.makedirs(self.current_store_path, exist_ok=True)
            self.record_path = os.path.join(self.current_store_path, "record")
            os.makedirs(self.record_path, exist_ok=True)
            self.label_path = os.path.join(self.current_store_path, "label")
            os.makedirs(self.label_path, exist_ok=True)
        self.recording_file = ""
        self.is_fullscreen = True
        self.person_id = person_id
        self.part = part
        self.parts_count = parts_count
        
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
        self.window_name = f'Eye Tracker - Person {person_id} - Part {part}/{parts_count}'
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.moveWindow(self.window_name, self.monitor.x, self.monitor.y)
        
        # Click tracking
        self.current_click_count = 0
        self.required_click_count = 3
        
        # Circle properties
        self.circle_radius = 10  # Radius for hit detection
        self.display_radius = 10  # Visual radius
        
        # Log file
        self.log_file = f"{self.folder}_id_{person_id}_part_{part}_label.csv"
        self.label_file = os.path.join(self.label_path, self.log_file)
        with open(self.label_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp_ms', 'Point_Index', 'X', 'Y', 'Click_Count', 'Click_X', 'Click_Y', "Status", "Raw_Path"])
        
        # Single point coordinates (will be set by user input)
        self.point_x = 0
        self.point_y = 0
        
        # Metavision settings
        self.bias_file = "eye_tracking_b1.bias"
        self.event_count = 100000
        self.current_event_timestamp = 0
        self.init_metavision()

    def init_metavision(self):
        """Initialize the Metavision camera and event processing"""
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
        """Event processing loop for Metavision camera"""
        height, width = self.mv_iterator.get_size()
        try:
            with MTWindow(title="Metavision Events Viewer", width=width, height=height,
                        mode=BaseWindow.RenderMode.BGR) as window:
                def keyboard_cb(key, scancode, action, mods):
                    if key == UIKeyEvent.KEY_ESCAPE or key == UIKeyEvent.KEY_Q:
                        window.set_close_flag()
                        self.running = False

                window.set_keyboard_callback(keyboard_cb)

                event_frame_gen = PeriodicFrameGenerationAlgorithm(
                    sensor_width=width, 
                    sensor_height=height, 
                    fps=25,
                    palette=ColorPalette.Dark
                )

                def on_cd_frame_cb(ts, cd_frame):
                    if not window.should_close():
                        try:
                            window.show_async(cd_frame)
                        except ValueError as e:
                            print(f"Error showing frame: {e}")
                            print(f"Frame shape: {cd_frame.shape if hasattr(cd_frame, 'shape') else 'unknown'}")

                event_frame_gen.set_output_callback(on_cd_frame_cb)

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
        """Start recording raw event data"""
        recording_path = os.path.join(self.record_path, recording_path)
        self.device.get_i_events_stream().log_raw_data(recording_path)
        print(f'Recording to {recording_path}')

    def stop_recording(self):
        """Stop recording raw event data"""
        if self.device:
            self.device.get_i_events_stream().stop_log_raw_data()

    def mouse_callback(self, event, x, y, flags, param):
        """Mouse event callback to handle clicks"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Check if click is inside the circle
            distance = np.sqrt((x - self.point_x)**2 + (y - self.point_y)**2)
            is_hit = distance <= self.circle_radius
            
            if is_hit:
                status = ""
                if self.current_click_count < self.required_click_count:
                    if self.current_click_count == 0:
                        self.recording_file = f"{self.folder}_{self.person_id}_part_{self.part}_{self.point_x}_{self.point_y}_record.raw"
                        self.start_recording(self.recording_file)
                        status = "start"
                        print(f"Recording started at event timestamp: {self.current_event_timestamp}")
                    elif self.current_click_count == 1:
                        status = "process"
                    elif self.current_click_count == 2:
                        self.stop_recording()
                        status = "end"
                        print(f"Recording stopped at event timestamp: {self.current_event_timestamp}")

                    # Log click attempt
                    self.log_point(self.current_event_timestamp, 1, 
                                  self.current_click_count, x, y, status, self.recording_file)
                    # Increment click count
                    self.current_click_count += 1
                    print(f"Hit! Click {self.current_click_count}/{self.required_click_count}")
            else:
                print(f"Miss! Click outside circle")

    def log_point(self, timestamp_ms, point_index, click_count, click_x=None, click_y=None, status="", file_path=""):
        """Log point data to CSV file with click count"""
        with open(self.label_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp_ms, point_index, self.point_x, self.point_y, click_count, click_x, click_y, status, file_path])

    def create_background(self):
        """Create dark background image"""
        bg_color = [0, 0, 0]  # Black background (BGR)
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        image[:] = bg_color
        return image

    def display_point(self):
        """Display the point until it receives required clicks"""
        # Set up mouse callback for clicks
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        # Show countdown
        self.show_countdown(3)
        
        while self.current_click_count < self.required_click_count:
            # Create a fresh background image
            image = self.create_background()
            
            # Draw the point
            cv2.circle(image, (self.point_x, self.point_y), self.display_radius, (0, 0, 255), -1)  # Red filled circle
            cv2.circle(image, (self.point_x, self.point_y), int(self.display_radius / 2), (0, 100, 255), 1)  # Red outline
            
            # Display click count and info
            click_text = f"Clicks: {self.current_click_count}/{self.required_click_count}"
            coord_text = f"Coordinates: ({self.point_x}, {self.point_y})"
            overall_text = f"Person {self.person_id} - Part {self.part}/{self.parts_count}"
            
            cv2.putText(image, click_text,
                       (self.point_x - 50, self.point_y + 40),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.8, (255, 255, 255), 2)
            
            cv2.putText(image, coord_text,
                       (self.point_x - 50, self.point_y - 20),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.8, (255, 255, 255), 2)
                       
            cv2.putText(image, overall_text,
                       (30, 30),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.8, (255, 255, 255), 2)
            
            # Show the frame
            cv2.imshow(self.window_name, image)
            
            # Check for key press
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key to exit
                self.cleanup()
                return
            
            # Small sleep to avoid hogging CPU
            time.sleep(0.01)
        
        # Show completion message
        self.show_completion_message()

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
        """Show a completion message when all clicks are processed"""
        image = self.create_background()
        
        # Draw completion message
        cv2.putText(image, "Complete!",
                   (self.width // 2 - 150, self.height // 2 - 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 
                   2, (0, 255, 0), 3)
                   
        cv2.putText(image, f"You completed Part {self.part} of {self.parts_count}",
                   (self.width // 2 - 300, self.height // 2 + 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 
                   1, (255, 255, 255), 2)
                   
        next_part_text = "Press any key to exit"
        cv2.putText(image, next_part_text,
                   (self.width // 2 - 200, self.height // 2 + 150),
                   cv2.FONT_HERSHEY_SIMPLEX, 
                   1, (255, 255, 255), 2)
                   
        cv2.imshow(self.window_name, image)
        cv2.waitKey(0)  # Wait for any key press
    
    def cleanup(self):
        """Clean up resources and close windows"""
        if self.device:
            self.stop_recording()
        self.running = False
        cv2.destroyAllWindows()

    def run(self):
        """Run the main program"""
        # Make sure the window is visible
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.moveWindow(self.window_name, self.monitor.x, self.monitor.y)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        # Display the point
        self.display_point()
        
        # Clean up when done
        self.cleanup()


def main():
    # Get person ID and part
    try:
        person_id = int(input("Enter person ID (1-5): "))
        if person_id < 1 or person_id > 5:
            print("Person ID must be between 1 and 5")
            return
            
        part = int(input("Enter part (1-3): "))
        if part < 1 or part > 3:
            print("Part must be between 1 and 3")
            return
        
        # Get point coordinates
        x = int(input("Enter point X coordinate: "))
        y = int(input("Enter point Y coordinate: "))
    except ValueError:
        print("Please enter valid numbers")
        return
    
    # Create and run the tracker for this person and part
    tracker = SimplifiedEyeTracker(
        folder="dicky",
        person_id=person_id,
        part=part,
        parts_count=3,
        monitor_index=1  # Use second monitor
    )
    
    # Print available monitors for debugging
    monitors = get_monitors()
    print(f"Found {len(monitors)} monitors:")
    for i, m in enumerate(monitors):
        print(f"Monitor {i}: {m.width}x{m.height} at position ({m.x},{m.y})")
    
    # Set the user-specified point
    tracker.point_x = x
    tracker.point_y = y
    
    # Run the program
    tracker.run()
    
if __name__ == "__main__":
    main()