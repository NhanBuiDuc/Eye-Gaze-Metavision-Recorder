import os
import time
import numpy as np
from metavision_core.event_io.raw_reader import initiate_device
from metavision_core.event_io import EventsIterator
from metavision_sdk_ui import EventLoop, BaseWindow, MTWindow, UIAction, UIKeyEvent
from metavision_sdk_core import PeriodicFrameGenerationAlgorithm, ColorPalette
import cv2
from src.entities.bias_settings import BiasSettings

class EventFrame:
    """Class wrapper for event frames"""
    def __init__(self, img):
        self.img = img

def convert_coordinates(coord, max_width=1280, max_height=720):
    x1, y1, x2, y2 = coord
    
    x1 = max(0, min(x1, max_width))
    y1 = max(0, min(y1, max_height))
    x2 = max(0, min(x2, max_width))
    y2 = max(0, min(y2, max_height))
    
    x = min(x1, x2)
    y = min(y1, y2)
    
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    
    if x + width > max_width:
        width = max_width - x
    if y + height > max_height:
        height = max_height - y
        
    width = max(20, width)
    height = max(20, height)
    
    # print(f"ROI converted: ({x1},{y1},{x2},{y2}) -> ({x},{y},{width},{height})")
    return x, y, width, height


class LiveReplayEventsIteratorWrapper:
    def __init__(self, output_file, event_count, roi_coordinates, bias_file=None):
        self.output_folder = output_file
        self.event_count = event_count
        self.roi_coordinates = roi_coordinates
        self.bias_file = bias_file
        self.is_recording = False
        
        self._buffer = None
        
        self.device = initiate_device("")
        
        if self.bias_file:
            bias_settings = BiasSettings.from_file(self.bias_file)
            biases = self.device.get_i_ll_biases()
            for name, bias in bias_settings.biases.items():
                biases.set(name, bias.value)
                
        self.device.get_i_erc_module().enable(True)
        self.device.get_i_erc_module().set_cd_event_count(event_count=self.event_count)
                
        self.mv_iterator = EventsIterator.from_device(self.device)
        
        self.height, self.width = self.mv_iterator.get_size()
        
        self.crop_coordinates = self.get_crop_coordinates_from_roi()

    def get_crop_coordinates_from_roi(self):
        x1, y1, x2, y2 = self.roi_coordinates
        return [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
        
    def update_roi(self, new_coordinates):
        self.roi_coordinates = new_coordinates
        self.crop_coordinates = self.get_crop_coordinates_from_roi()
        # print(f"Crop coordinates updated: {self.crop_coordinates}")

    def create_frame(self, events, reuse_buffer=True):
        if events.dtype != [('x', '<u2'), ('y', '<u2'), ('p', '<i2'), ('t', '<i8')]:
            events = np.array(events, 
                            dtype=[('x', '<u2'), ('y', '<u2'), 
                                ('p', '<i2'), ('t', '<i8')])

        if self._buffer is None or not reuse_buffer:
            img = np.ones((self.height, self.width, 3), dtype=np.uint8) * 127
        else:
            img = self._buffer
            img[...] = 127

        if events.size:
            max_x = events['x'].max() if events.size > 0 else 0
            max_y = events['y'].max() if events.size > 0 else 0
            
            if max_x >= self.width or max_y >= self.height:
                valid_events = events[(events['x'] < self.width) & (events['y'] < self.height)]
                
                positive_events = valid_events[valid_events['p'] > 0]
                negative_events = valid_events[valid_events['p'] <= 0]
                
                if positive_events.size:
                    img[positive_events['y'], positive_events['x']] = [255, 255, 255]  
                    
                if negative_events.size:
                    img[negative_events['y'], negative_events['x']] = [0, 0, 0]  
            else:
                positive_events = events[events['p'] > 0]
                negative_events = events[events['p'] <= 0]
                
                if positive_events.size:
                    img[positive_events['y'], positive_events['x']] = [255, 255, 255] 
                    
                if negative_events.size:
                    img[negative_events['y'], negative_events['x']] = [0, 0, 0]  

        if hasattr(self, 'crop_coordinates') and self.crop_coordinates:
            x1, y1, x2, y2 = self.crop_coordinates
            cropped_img = img.copy()
            cv2.rectangle(cropped_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            mask = np.ones_like(img, dtype=np.uint8) * 127
            mask[y1:y2, x1:x2] = img[y1:y2, x1:x2]
            cropped_img = mask
            img = cropped_img

        if reuse_buffer:
            self._buffer = img

        return EventFrame(img)
    
    def get_event_frame_gen(self):
        return PeriodicFrameGenerationAlgorithm(
            sensor_width=self.width, 
            sensor_height=self.height,
            fps=25,
            palette=ColorPalette.Gray
        )

    def start_recording(self, recording_path):
        if self.output_folder != "":
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
                print(f'Created output directory: {self.output_folder}')
                
            recording_path = os.path.join(self.output_folder, recording_path)
        
        self.device.get_i_events_stream().log_raw_data(recording_path)
        self.is_recording = True
        print(f'Recording FULL events to {recording_path} (Crop only affects display, not recording)')

    def stop_recording(self):
        """Dừng ghi"""
        if self.device and self.is_recording:
            self.device.get_i_events_stream().stop_log_raw_data()
            self.is_recording = False
            print("Recording stopped")

    def get_window(self):
        with MTWindow(title="Metavision Events Viewer", width=self.width, height=self.height,
                    mode=BaseWindow.RenderMode.BGR) as window:
            def keyboard_cb(key, scancode, action, mods):
                if key == UIKeyEvent.KEY_ESCAPE or key == UIKeyEvent.KEY_Q:
                    window.set_close_flag()
                elif key == UIKeyEvent.KEY_R and action == UIAction.PRESS:
                    if not self.is_recording:
                        self.start_recording(f"recording_{int(time.time())}.raw")
                    else:
                        self.stop_recording()

            window.set_keyboard_callback(keyboard_cb)

            event_frame_gen = PeriodicFrameGenerationAlgorithm(
                sensor_width=self.width, 
                sensor_height=self.height, 
                fps=25,
                palette=ColorPalette.Dark
            )

            def on_cd_frame_cb(ts, cd_frame):
                window.show_async(cd_frame)

            event_frame_gen.set_output_callback(on_cd_frame_cb)

            for evs in self.mv_iterator:
                EventLoop.poll_and_dispatch()
                
                frame = self.create_frame(evs)
                window.show_async(frame.img)

                if window.should_close():
                    if self.is_recording:
                        self.stop_recording()
                    break

if __name__ == "__main__":
    import cv2  
    
    metavision_displayer = LiveReplayEventsIteratorWrapper(
        output_file="recordings", 
        event_count=10000, 
        roi_coordinates=[400, 200, 800, 470]
    )
    metavision_displayer.get_window()