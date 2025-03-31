import os
from metavision_core.event_io.raw_reader import initiate_device
from metavision_core.event_io import EventsIterator, LiveReplayEventsIterator, is_live_camera
from metavision_sdk_ui import EventLoop, BaseWindow, MTWindow, UIAction, UIKeyEvent
from metavision_core.event_io import EventsIterator, LiveReplayEventsIterator, is_live_camera
from metavision_sdk_core import PeriodicFrameGenerationAlgorithm, ColorPalette

from src.entities.bias_settings import BiasSettings

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
    
    print(f"ROI converted: ({x1},{y1},{x2},{y2}) -> ({x},{y},{width},{height})")
    return x, y, width, height


class LiveReplayEventsIteratorWrapper:
    def __init__(self, output_file, event_count, roi_coordinates, bias_file):
        self.output_folder = output_file
        self.event_count = event_count
        self.roi_coordinates = roi_coordinates
        self.bias_file = bias_file
        
        self.device = initiate_device("", do_time_shifting=False)
        
        # Apply bias settings if provided
        if self.bias_file:
            bias_settings = BiasSettings.from_file(self.bias_file)
            biases = self.device.get_i_ll_biases()
            for name, bias in bias_settings.biases.items():
                biases.set(name, bias.value)
                
        self.mv_iterator = EventsIterator.from_device(self.device, start_ts=0, n_events=event_count, delta_t=33333, mode="delta_t")
        # self.device.get_i_erc_module().enable(True)
        # self.device.get_i_erc_module().set_cd_event_count(event_count=self.event_count)
        
        # Get ROI module
        # self.I_ROI = self.device.get_i_roi()
        # self.update_roi(self.roi_coordinates)
        
        self.height, self.width = self.mv_iterator.get_size()
        
    # def update_roi(self, new_coordinates):
    #     """Update ROI window without recreating the device"""
    #     self.roi_coordinates = new_coordinates
    #     x, y, width, height = convert_coordinates(new_coordinates)
        
    #     # Create and set new ROI window
    #     roi_window = self.I_ROI.Window(x, y, width, height)
    #     self.I_ROI.set_window(roi_window)
    #     self.I_ROI.enable(True)


    def get_event_frame_gen(self):
        return PeriodicFrameGenerationAlgorithm(
            sensor_width=self.width, 
            sensor_height=self.height,
            fps=25,
            palette=ColorPalette.Gray
        )

    def start_recording(self, recording_path):
        if self.output_folder != "":
            # Create output folder if it doesn't exist
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)
                print(f'Created output directory: {self.output_folder}')
                
            recording_path = os.path.join(self.output_folder, recording_path)
        
        self.device.get_i_events_stream().log_raw_data(recording_path)
        print(f'Recording to {recording_path}')

    def stop_recording(self):
        if self.device:
            self.device.get_i_events_stream().stop_log_raw_data()

    def get_window(self):
        # Window - Graphical User Interface
        with MTWindow(title="Metavision Events Viewer", width=self.width, height=self.height,
                    mode=BaseWindow.RenderMode.BGR) as window:
            def keyboard_cb(key, scancode, action, mods):
                if key == UIKeyEvent.KEY_ESCAPE or key == UIKeyEvent.KEY_Q:
                    window.set_close_flag()

            window.set_keyboard_callback(keyboard_cb)

            # Event Frame Generator
            event_frame_gen = PeriodicFrameGenerationAlgorithm(sensor_width=self.width, sensor_height=self.height, fps=25,
                                                            palette=ColorPalette.Dark)

            def on_cd_frame_cb(ts, cd_frame):
                window.show_async(cd_frame)

            event_frame_gen.set_output_callback(on_cd_frame_cb)

            # Process events
            for evs in self.mv_iterator:
                # Dispatch system events to the window
                EventLoop.poll_and_dispatch()
                event_frame_gen.process_events(evs)

                if window.should_close():
                    break