import cv2
import numpy as np
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QPushButton, 
                           QLabel, QLineEdit, QGroupBox, QFrame, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
from threading import Thread
from metavision_API.live_replay_events_iterator import *
from styles import StyleSheetMain
from widgets.csv_display_widget import CSVAnalysisWindow
from widgets.metavision_display_widget import DynamicROIDisplayWidget
from widgets.metavsion_widget import DynamicROIDisplayWidget
from widgets.smooth_pursuit_widget import SmoothPursuitWidget
from widgets.saccade_pursuit_widget import SaccadePursuitWidget
from PyQt5.QtGui import QIntValidator

class MetavisionWidget(QWidget):
    def __init__(self, wrapper, parent=None):
        super().__init__(parent)
        self.wrapper = wrapper
        self.current_log_filename = "recording.csv"
        self.current_record_filename = "recording.raw"
        self.base_filename = "recording"
        self.recording_waiting_time = 5
        self.roi = [400, 200, 800, 470]
        self.is_recording = False
        self.events = None
        self.current_pattern = None
        self.roi_control_mode = "drag"
        
        self.event_list = []
        self.setup_ui()
        # Set window background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(StyleSheetMain.BACKGROUND_COLOR))
        self.setPalette(palette)

    def confirm_file_names(self):
        """Handle file name confirmation and update UI"""
        
        x1, y1, x2, y2 =  self.wrapper.roi_coordinates
        coord_str = f"{x1}_{y1}_{x2}_{y2}"
        print(coord_str)
        self.base_filename = self.file_text_box.text()
        self.current_log_filename = f"{coord_str}_{self.base_filename}.csv"
        self.current_record_filename = f"{coord_str}_{self.base_filename}.raw"
        print(f"Log file: {self.current_log_filename}")
        print(f"Record file: {self.current_record_filename}")
        
        # Visual feedback
        self.confirm_button.setText("✓ Confirmed")
        self.confirm_button.setEnabled(False)
        
        # Reset button after 1 second
        QTimer.singleShot(1000, lambda: self.confirm_button.setEnabled(True))
        QTimer.singleShot(1000, lambda: self.confirm_button.setText("Confirm"))
        
        # Set window background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(StyleSheetMain.BACKGROUND_COLOR))
        self.setPalette(palette)

    def setup_ui(self):
        # Main layout with margins for better spacing
        main_layout = QHBoxLayout()  # Remove self here
        self.setLayout(main_layout)  # Set the layout separately
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)
        
        # Right panel first (to initialize displayer)
        right_panel = QFrame()
        right_panel.setStyleSheet(f"background-color: {StyleSheetMain.CARD_COLOR}; border-radius: 12px;")
        right_layout = QVBoxLayout()  # Remove right_panel here
        right_panel.setLayout(right_layout)  # Set the layout separately
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)
        
        # Camera section with icon
        camera_header = QHBoxLayout()
        camera_icon = QLabel("🎥")
        camera_icon.setFont(QFont("", 20))
        camera_label = QLabel("Live Camera Feed")
        camera_label.setStyleSheet(StyleSheetMain.DISPLAY_TITLE)
        camera_header.addWidget(camera_icon)
        camera_header.addWidget(camera_label)
        camera_header.addStretch()
        right_layout.addLayout(camera_header)
        
        # Initialize displayer first
        self.displayer = DynamicROIDisplayWidget()
        self.displayer.setStyleSheet(StyleSheetMain.DISPLAY_WIDGET)
        self.displayer.setMinimumSize(800, 600)
        
        self.coordinates_label = QLabel("ROI: Not set")
        self.coordinates_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-family: monospace;
            }
        """)
        self.coordinates_label.setMinimumWidth(300)
        self.coordinates_label.setAlignment(Qt.AlignCenter)
        
        self.displayer.coordinates_updated.connect(self.coordinates_label.setText)
        
        coordinates_container = QHBoxLayout()
        coordinates_container.addWidget(self.coordinates_label)
        coordinates_container.addStretch()
        
        right_layout.addWidget(self.displayer)
        right_layout.addLayout(coordinates_container)
        
        # Left panel setup
        left_panel = QFrame()
        left_panel.setStyleSheet(f"background-color: {StyleSheetMain.CARD_COLOR}; border-radius: 12px;")
        left_layout = QVBoxLayout()  # Remove left_panel here
        left_panel.setLayout(left_layout)  # Set the layout separately
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(20)
        
        # Title with icon-like label
        title_container = QHBoxLayout()
        icon_label = QLabel("📹")
        icon_label.setFont(QFont("", 24))
        title_label = QLabel("Camera Recording")
        title_label.setStyleSheet(StyleSheetMain.TITLE_LABEL)
        title_container.addWidget(icon_label)
        title_container.addWidget(title_label)
        title_container.addStretch()
        left_layout.addLayout(title_container)
        
        # Add recording controls
        recording_group = self.create_recording_group()
        left_layout.addWidget(recording_group)
        
        # Add file settings
        file_group = self.create_file_settings_group()
        left_layout.addWidget(file_group)

        roi_group = self.create_roi_control_group()
        left_layout.addWidget(roi_group)
        
        left_layout.addStretch()
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 3)

    def create_roi_control_group(self):
        roi_group = QGroupBox("ROI Control")
        roi_group.setStyleSheet(StyleSheetMain.GROUP_BOX)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 25, 15, 15)

        # Input method selection
        method_layout = QHBoxLayout()
        method_label = QLabel("Input Method:")
        self.manual_radio = QRadioButton("Manual Input")
        self.drag_radio = QRadioButton("Drag & Drop")
        self.drag_radio.setChecked(True)
        self.drag_radio.toggled.connect(self.set_drag_mode)
        
        method_layout.addWidget(method_label)
        method_layout.addWidget(self.manual_radio)
        method_layout.addWidget(self.drag_radio)
        layout.addLayout(method_layout)

        # Manual input fields
        input_grid = QGridLayout()
        input_grid.setSpacing(10)

        # X1, Y1 inputs
        input_grid.addWidget(QLabel("X1:"), 0, 0)
        self.x1_input = QLineEdit()
        self.x1_input.setText("400")
        self.x1_input = QLineEdit(str(self.roi[0]))
        self.x1_input.setPlaceholderText("0-1280")
        input_grid.addWidget(self.x1_input, 0, 1)

        input_grid.addWidget(QLabel("Y1:"), 0, 2)
        self.y1_input = QLineEdit()
        self.y1_input.setText("200")
        self.y1_input = QLineEdit(str(self.roi[1]))
        self.y1_input.setPlaceholderText("0-720")
        input_grid.addWidget(self.y1_input, 0, 3)

        # X2, Y2 inputs
        input_grid.addWidget(QLabel("X2:"), 1, 0)
        self.x2_input = QLineEdit()
        self.x2_input.setText("800")
        self.x2_input = QLineEdit(str(self.roi[2]))
        self.x2_input.setPlaceholderText("0-1280")
        input_grid.addWidget(self.x2_input, 1, 1)

        input_grid.addWidget(QLabel("Y2:"), 1, 2)
        self.y2_input = QLineEdit()
        self.y2_input.setText("470")
        self.y2_input = QLineEdit(str(self.roi[3]))
        self.y2_input.setPlaceholderText("0-720")
        input_grid.addWidget(self.y2_input, 1, 3)

        layout.addLayout(input_grid)

        # Apply button
        self.apply_roi_button = QPushButton("Apply ROI")
        self.apply_roi_button.setStyleSheet(StyleSheetMain.BUTTON)
        self.apply_roi_button.clicked.connect(self.apply_manual_roi)
        layout.addWidget(self.apply_roi_button)

        # Connect radio buttons to enable/disable input fields
        self.manual_radio.toggled.connect(self.toggle_input_method)
        self.toggle_input_method(False)  # Initially disable manual input

        roi_group.setLayout(layout)
        return roi_group
    
    def apply_manual_roi(self):
        """Apply ROI from manual input fields"""
        try:
            x1 = int(self.x1_input.text())
            y1 = int(self.y1_input.text())
            x2 = int(self.x2_input.text())
            y2 = int(self.y2_input.text())
            
            # Validate coordinates
            if not (0 <= x1 <= 1280 and 0 <= x2 <= 1280 and 
                   0 <= y1 <= 720 and 0 <= y2 <= 720):
                raise ValueError("Coordinates must be within bounds")
                
            new_roi = [x1, y1, x2, y2]
            self.roi = new_roi
            self.wrapper.update_roi(new_roi)
            self.displayer.set_roi(new_roi)
            self.roi_control_mode = "manual"
            
            
            self.x1_input.setText(str(new_roi[0]))
            self.y1_input.setText(str(new_roi[1]))
            self.x2_input.setText(str(new_roi[2]))
            self.y2_input.setText(str(new_roi[3]))

            # Update coordinate display
            coord_str = f"ROI: ({x1}, {y1}) to ({x2}, {y2})"
            self.coordinates_label.setText(coord_str)
            
        except ValueError as e:
            print(f"Invalid input: {str(e)}")
            # You might want to add a proper error dialog here

    def on_roi_changed_from_drag(self, new_roi):
        """Handle ROI updates from drag & drop"""
        
        self.wrapper.update_roi(new_roi)
        
        # Update input fields
        self.x1_input.setText(str(new_roi[0]))
        self.y1_input.setText(str(new_roi[1]))
        self.x2_input.setText(str(new_roi[2]))
        self.y2_input.setText(str(new_roi[3]))
        
        # Update coordinate display
        coord_str = f"ROI: ({new_roi[0]}, {new_roi[1]}) to ({new_roi[2]}, {new_roi[3]})"
        self.coordinates_label.setText(coord_str)


    def set_drag_mode(self, drag_mode):
        print(drag_mode)
        self.roi_control_mode = drag_mode
        
    def toggle_input_method(self, manual_enabled):
        """Enable/disable input fields based on selected method"""
        self.x1_input.setEnabled(manual_enabled)
        self.y1_input.setEnabled(manual_enabled)
        self.x2_input.setEnabled(manual_enabled)
        self.y2_input.setEnabled(manual_enabled)
        self.apply_roi_button.setEnabled(manual_enabled)
        self.displayer.set_drag_enabled(not manual_enabled)

    def create_recording_group(self):
        recording_group = QGroupBox("Recording Controls")
        recording_group.setStyleSheet(StyleSheetMain.GROUP_BOX)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 25, 15, 15)  # Top margin increased for title
        
        # Pattern selection label with icon
        pattern_header = QHBoxLayout()
        pattern_header.setContentsMargins(0, 0, 0, 5)
        pattern_icon = QLabel("🎯")
        pattern_icon.setFont(QFont("", 16))
        pattern_label = QLabel("Recording Style:")
        pattern_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #455A64;")
        pattern_header.addWidget(pattern_icon)
        pattern_header.addWidget(pattern_label)
        pattern_header.addStretch()
        layout.addLayout(pattern_header)
        
        # Radio buttons for pattern selection
        self.pattern_group = QButtonGroup(self)
        
        # Smooth Pursuit radio
        self.smooth_radio = QRadioButton("Smooth Pursuit")
        self.smooth_radio.setStyleSheet(StyleSheetMain.RADIO_BUTTON)
        self.smooth_radio.setChecked(True)
        self.pattern_group.addButton(self.smooth_radio)
        layout.addWidget(self.smooth_radio)
        
        # Saccade radio
        self.saccade_radio = QRadioButton("Saccade")
        self.saccade_radio.setStyleSheet(StyleSheetMain.RADIO_BUTTON)
        self.pattern_group.addButton(self.saccade_radio)
        layout.addWidget(self.saccade_radio)
        # Add waiting time label and text box
        waiting_label = QLabel("Waiting time:")
        waiting_label.setStyleSheet("color: #455A64;")
        layout.addWidget(waiting_label)

        self.waiting_time_input = QLineEdit()
        self.waiting_time_input.setFixedWidth(60)  # Set a fixed width for the text box
        self.waiting_time_input.setStyleSheet("QLineEdit { padding: 2px; border: 1px solid #ccc; border-radius: 3px; }")
        self.waiting_time_input.setText(str(self.recording_waiting_time))  # Default value

        # Add validator for integers only
        validator = QIntValidator()
        self.waiting_time_input.setValidator(validator)

        # Add focus out event to validate when leaving the text box
        self.waiting_time_input.focusOutEvent = self.validate_waiting_time
        # Add text changed event
        self.waiting_time_input.textChanged.connect(self.on_waiting_time_changed)

        layout.addWidget(self.waiting_time_input)
        layout.addStretch()  # Add stretch to keep elements left-aligned

        layout.addSpacing(10)  # Add space before buttons
        
        # Control buttons container
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Start button
        self.start_button = QPushButton("▶ Start Recording")
        self.start_button.setStyleSheet(StyleSheetMain.BUTTON)
        self.start_button.setFixedSize(150, 40)
        self.start_button.clicked.connect(self.start_selected_pattern)
        
        # Stop button
        self.stop_button = QPushButton("⬛ Stop")
        self.stop_button.setStyleSheet(StyleSheetMain.STOP_BUTTON)
        self.stop_button.setFixedSize(100, 40)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_recording)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        layout.addLayout(buttons_layout)
        
        recording_group.setLayout(layout)
        return recording_group
    
    def start_selected_pattern(self):
        """Start recording with the selected pattern"""
        if not self.pattern_group.checkedButton():
            # No pattern selected
            return
            
        if self.pattern_group.checkedButton() == self.smooth_radio:
            self.start_smooth_pursuit()
        else:
            self.start_saccade_pursuit()

    def create_file_settings_group(self):
        file_group = QGroupBox("File Settings")
        file_group.setStyleSheet(StyleSheetMain.GROUP_BOX)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 25, 15, 15)  # Top margin increased for title
        
        # File name input section
        file_header = QHBoxLayout()
        file_icon = QLabel("📄")
        file_icon.setFont(QFont("", 16))
        file_label = QLabel("File Name:")
        file_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #455A64;")
        file_header.addWidget(file_icon)
        file_header.addWidget(file_label)
        file_header.addStretch()
        layout.addLayout(file_header)
        
        # File name input
        self.file_text_box = QLineEdit()
        self.file_text_box.setText(self.base_filename)  # Base filename without extension
        self.file_text_box.setStyleSheet(StyleSheetMain.TEXTBOX)
        layout.addWidget(self.file_text_box)
        
        # Confirm button
        self.confirm_button = QPushButton('Confirm')
        self.confirm_button.setStyleSheet(StyleSheetMain.BUTTON)
        self.confirm_button.clicked.connect(self.confirm_file_names)
        layout.addWidget(self.confirm_button)
        
        # Add CSV Analysis button
        self.csv_analysis_button = QPushButton('CSV Analysis Tool')
        self.csv_analysis_button.setStyleSheet(StyleSheetMain.BUTTON_ANA)
        self.csv_analysis_button.clicked.connect(self.open_csv_analysis)
        # layout.addWidget(self.csv_analysis_button)
    

        file_group.setLayout(layout)
        return file_group
    
    def open_csv_analysis(self):
        """Open the CSV Analysis window"""
        self.csv_analysis_window = CSVAnalysisWindow()
        self.csv_analysis_window.show()

    def start_recording(self):
        self.wrapper.start_recording(self.current_record_filename)
        self.is_recording = True
        self.stop_button.setEnabled(True)
        self.start_button.setEnabled(False)
        self.smooth_radio.setEnabled(False)
        self.saccade_radio.setEnabled(False)

    def stop_recording(self):
        print("stop recording file ", self.current_record_filename)
        self.wrapper.stop_recording()
        self.is_recording = False
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)
        self.smooth_radio.setEnabled(True)
        self.saccade_radio.setEnabled(True)
            
        cv2.destroyAllWindows()
        # Close the pattern window if it exists
        if self.current_pattern is not None:
            self.current_pattern.hide()
            self.current_pattern.close()
            self.current_pattern = None
        
        self.show()

    def start_smooth_pursuit(self):
        """Start the smooth pursuit pattern"""
        self.start_recording()
        self.current_pattern = SmoothPursuitWidget(self, "config/config_smooth.yaml", self.wrapper)
        self.current_pattern.showFullScreen()
        
    def start_saccade_pursuit(self):
        """Start the saccade pattern"""
        self.start_recording()
        self.current_pattern = SaccadePursuitWidget(self, "config/config_saccade.yaml", self.wrapper)
        self.current_pattern.showFullScreen()

    def set_text_log_textbox(self, textbox: QLineEdit):
        self.current_log_filename = textbox.text()
        print(self.current_log_filename)

    def set_text_record_textbox(self, textbox: QLineEdit):
        self.current_record_filename = textbox.text()
        print(self.current_record_filename)

    def run_metavision(self):
        event_frame_gen = self.wrapper.get_event_frame_gen()

        def on_cd_frame_cb(ts, cd_frame):
            frame = np.copy(cd_frame)
            self.displayer.update_frame(frame, self.roi_control_mode)

        event_frame_gen.set_output_callback(on_cd_frame_cb)
        
        self.mv_thread = Thread(target=self.process_events, args=(event_frame_gen,), daemon=True)
        self.mv_thread.start()

    def process_events(self, event_frame_gen):
        try:
            for evs in self.wrapper.mv_iterator:
                EventLoop.poll_and_dispatch()
                self.events = evs
                event_frame_gen.process_events(evs)
        except Exception as e:
            print(f"Error in Metavision pipeline: {str(e)}")
    # Add the validation and change event methods to your class
    def validate_waiting_time(self, event):
        """Validate the waiting time when focus is lost"""
        try:
            value = int(self.waiting_time_input.text())
            if value < 0:
                self.waiting_time_input.setText("5")
        except ValueError:
            self.waiting_time_input.setText("5")
        # Call the parent class's focusOutEvent
        super(type(self), self).focusOutEvent(event)

    def on_waiting_time_changed(self, text):
        """Handle waiting time change event"""
        try:
            value = int(text) if text else 5
            # Do something with the new value
            print(f"Waiting time changed to: {value}")
            self.recording_waiting_time = value
            # You can emit a custom signal here or call other methods as needed
        except ValueError:
            pass  # Invalid input, will be handled by validator