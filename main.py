import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from metavision_API.live_replay_events_iterator import *
from widgets.metavsion_widget import MetavisionWidget

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eye Gaze Recording Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create wrapper instance with initial ROI
        self.wrapper = LiveReplayEventsIteratorWrapper(
            output_file="public/recordings",
            event_count=100000,
            roi_coordinates=[400, 200, 800, 470],
            bias_file=None
        )
        
        # Create and set up the metavision widget
        self.metavision_widget = MetavisionWidget(self.wrapper, self)
        self.setCentralWidget(self.metavision_widget)
        
        # Connect ROI update signal
        self.metavision_widget.displayer.roi_changed.connect(self.update_roi)
        
        # Start the metavision pipeline
        self.metavision_widget.run_metavision()

    def update_roi(self, new_roi):
        """Update the ROI in the existing wrapper"""
        self.wrapper.update_roi(new_roi)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainApp()
    mainWin.showMaximized()
    sys.exit(app.exec_())