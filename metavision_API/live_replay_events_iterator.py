import os
import time
from metavision_core.event_io.raw_reader import initiate_device
from metavision_core.event_io import EventsIterator, LiveReplayEventsIterator, is_live_camera
from metavision_sdk_ui import EventLoop, BaseWindow, MTWindow, UIAction, UIKeyEvent
from metavision_core.event_io import EventsIterator, LiveReplayEventsIterator, is_live_camera
from metavision_sdk_core import PeriodicFrameGenerationAlgorithm, ColorPalette

from src.entities.bias_settings import BiasSettings

def convert_coordinates(coord):
    x1 = coord[0]
    y1 = coord[1]
    x2 = coord[2]
    y2 = coord[3]    
    x = min(x1, x2)
    y = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    return x, y, width, height


class LiveReplayEventsIteratorWrapper:
    def __init__(self, output_file, event_count, roi_coordinates, bias_file):
        self.output_file = output_file
        self.event_count = event_count
        self.roi_window_size = convert_coordinates(roi_coordinates)
        x = self.roi_window_size[0]
        y = self.roi_window_size[1]
        width = self.roi_window_size[0]
        height = self.roi_window_size[1]
        device = initiate_device("")

        if bias_file:
            bias_settings = BiasSettings.from_file(bias_file)
        else:
            bias_settings = BiasSettings.create_default()

        # Apply bias settings to device
        if bias_settings:
            biases = device.get_i_ll_biases()
            for name, bias in bias_settings.biases.items():
                biases.set(name, bias.value)

        if device.get_i_events_stream():
            log_path = "recording_" + time.strftime("%y%m%d_%H%M%S", time.localtime()) + ".raw"
            if self.output_file != "":
                log_path = os.path.join(self.output_file, log_path)
            print(f'Recording to {log_path}')
            device.get_i_events_stream().log_raw_data(log_path)
        
        self.mv_iterator = EventsIterator.from_device(device)
        device.get_i_erc_module().enable(True)
        device.get_i_erc_module().set_cd_event_count(event_count = event_count)
        self.device = device

        I_ROI = self.device.get_i_roi()
        roi_window = I_ROI.Window(x, y, width, height)
        I_ROI.set_window(roi_window)
        I_ROI.enable(True)

        self.height, self.width = self.mv_iterator.get_size()  # Camera Geometry
        
    def get_event_frame_gen(self):
        event_frame_gen = PeriodicFrameGenerationAlgorithm(sensor_width=self.width, sensor_height=self.height, fps=25,
                                                        palette=ColorPalette.Gray)
        return event_frame_gen
    
    def stop_recording(self):
        if self.device:
            self.device.get_i_events_stream().stop_log_raw_data()
    
    def initialize(self):
        pass
    
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

if __name__ == "__main__":
    metavision_displayer = LiveReplayEventsIteratorWrapper(event_count=10000, roi_coordinates=[400, 200, 800, 470])
    metavision_displayer.get_window()
