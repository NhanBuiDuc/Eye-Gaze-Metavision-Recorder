import h5py
import numpy as np
import cv2
from pathlib import Path
import os
import time

RECORDINGS_DIR = r"C:\Users\nhanb\OneDrive\Desktop\eye_gaze_software\recordings"

import h5py
import numpy as np
import cv2
from pathlib import Path
import os
import time

RECORDINGS_DIR = r"C:\Users\nhanb\OneDrive\Desktop\eye_gaze_software\recordings"

class EventReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.frame_width = None
        self.frame_height = None
        self.events = None
        self.accumulation_time = 40*100000000000  # 40ms window
        self.target_fps = 30
        self.frame_time = 1.0 / self.target_fps
        
    def load_file(self):
        with h5py.File(self.file_path, 'r') as f:
            self.frame_width = 1200
            self.frame_height = 1200
            print(f"Frame dimensions: {self.frame_width}x{self.frame_height}")
            
            self.events = f['events'][:]
            print(f"Loaded {len(self.events)} events")
            
            if len(self.events) > 0:
                start_time = self.events[0]['timestamp']
                end_time = self.events[-1]['timestamp']
                duration_ms = (end_time - start_time) / 1000
                print(f"Recording duration: {duration_ms:.2f}ms")
        
    def play_events(self):
        if len(self.events) == 0:
            print("No events to display")
            return
            
        start_time = self.events[0]['timestamp']
        end_time = self.events[-1]['timestamp']
        current_time = start_time
        
        cv2.namedWindow('Events', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Events', 800, 600)
        
        frame_start_time = time.time()
        frames = 0
        
        while current_time < end_time:
            # Create frame and get events in current time window
            frame = np.zeros((self.frame_height, self.frame_width), dtype=np.uint8)
            mask = (self.events['timestamp'] >= current_time) & (self.events['timestamp'] < current_time + self.accumulation_time)
            current_events = self.events[mask]
            
            # Plot events
            for event in current_events:
                frame[event['y'], event['x']] = 255 if event['polarity'] == 1 else 128
            
            # Add frame info and FPS
            frame_display = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            frames += 1
            if frames % 30 == 0:  # Update FPS every 30 frames
                fps = frames / (time.time() - frame_start_time)
                print(f"FPS: {fps:.1f}")
            
            cv2.putText(frame_display, f"Events: {len(current_events)}", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display and handle keys
            cv2.imshow('Events', frame_display)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            current_time += self.accumulation_time
        
        cv2.destroyAllWindows()

# Rest of the code remains the same...

def main():
    # List all HDF5 files in the recordings directory
    hdf5_files = [f for f in os.listdir(RECORDINGS_DIR) if f.endswith('.hdf5')]
    
    if not hdf5_files:
        print("No HDF5 files found in recordings directory")
        return
        
    print("Available recordings:")
    for i, file in enumerate(hdf5_files):
        print(f"{i+1}. {file}")
        
    while True:
        try:
            choice = int(input("\nEnter the number of the file to play (or 0 to exit): "))
            if choice == 0:
                return
            if 1 <= choice <= len(hdf5_files):
                break
            print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
            
    selected_file = hdf5_files[choice-1]
    file_path = os.path.join(RECORDINGS_DIR, selected_file)
    
    print(f"\nPlaying: {selected_file}")
    print("Press 'q' to quit, 's' to save current frame")
    
    reader = EventReader(file_path)
    reader.load_file()
    reader.play_events()

if __name__ == "__main__":
    main()