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
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QMessageBox
import csv
import os
from datetime import datetime
import yaml
from PyQt5.QtWidgets import QComboBox


label_mode = ["smooth", "saccadde"]
# Get current date in dd_mm_yyyy format
current_date = datetime.now().strftime("%d_%m_%Y")

class MetavisionWidget(QWidget):
    def __init__(self, wrapper, parent=None):
        super().__init__(parent)
        self.wrapper = wrapper
        self.current_label_mode = label_mode[0]
        self.default_filename = f"name_eyeID_mode_{current_date}"
        self.current_label_filename = f"label_name_eyeID_mode_{current_date}.csv"
        self.current_record_filename = f"record_name_eyeID_mode_{current_date}.raw"
        self.current_config_filename = f"config_name_eyeID_mode_{current_date}.yaml"

        self.config_yaml_path = "public/config"
        os.makedirs(self.config_yaml_path, exist_ok=True)
        
        self.recording_waiting_time = 5
        self.current_saccade_part = 1
        self.current_starting_timestamp = 0
        self.roi = [300,200,900,600]
        self.is_recording = False
        self.events = None
        self.current_pattern_obj = None
        self.roi_control_mode = "drag"
        
        # Flags for tracking confirmation states
        self.filename_confirmed = False
        self.part_confirmed = False

        self.horizontal_direction = "left2right"
        self.vertical_direction = "top2bottom"
        self.direction_first = "Horizontal"
        self.direction_confirmed = False

        self.event_list = []
        self.setup_ui()
        # Set window background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(StyleSheetMain.BACKGROUND_COLOR))
        self.setPalette(palette)
        
        # Initially disable start button until file name is confirmed
        self.update_start_button_state()

    def confirm_file_names(self):
        """Handle file name confirmation and update UI"""
        
        # Check if the filename is still the default
        if self.file_text_box.text() == self.default_filename:
            QMessageBox.warning(
                self, 
                "Invalid Filename", 
                "Please enter a custom filename before confirming."
            )
            return
            
        x1, y1, x2, y2 = self.wrapper.roi_coordinates
        coord_str = f"{x1}_{y1}_{x2}_{y2}"
        print(coord_str)
        self.current_label_filename = f"label_{coord_str}_{self.file_text_box.text()}.csv"
        self.current_record_filename = f"record_{coord_str}_{self.file_text_box.text()}.raw"
        self.current_config_filename = f"config_{coord_str}_{self.file_text_box.text()}.yaml"

        print(f"Log file: {self.current_label_filename}")
        print(f"Record file: {self.current_record_filename}")
        
        # Set confirmation flag
        self.filename_confirmed = True
        
        # Visual feedback
        self.confirm_button.setText("✓ Confirmed")
        self.confirm_button.setEnabled(False)
        
        # Reset button after 1 second
        QTimer.singleShot(1000, lambda: self.confirm_button.setEnabled(True))
        QTimer.singleShot(1000, lambda: self.confirm_button.setText("Confirm"))
        
        # Update start button state
        self.update_start_button_state()
        
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
        
        # Add file settings first (since it needs to be confirmed before recording)
        file_group = self.create_file_settings_group()
        left_layout.addWidget(file_group)
        
        # Add recording controls
        recording_group = self.create_recording_group()
        left_layout.addWidget(recording_group)

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
        self.manual_radio.setChecked(True)

        self.drag_radio = QRadioButton("Drag & Drop")
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
        self.toggle_input_method(True)  # Initially disable manual input

        roi_group.setLayout(layout)
        return roi_group
    
    def confirm_saccade_part(self):
        """Handle the saccade part confirmation"""
        try:
            part_value = int(self.saccade_part_input.text())
            if 1 <= part_value <= 6:
                # Convert from 1-10 to 0-9 for internal use
                self.current_saccade_part = part_value - 1
                QMessageBox.information(
                    self, 
                    "Saccade Part", 
                    f"Saccade pattern part {part_value} selected successfully."
                )
                self.part_confirmed = True
                self.update_start_button_state()
            else:
                QMessageBox.warning(
                    self, 
                    "Invalid Input", 
                    "Please enter a number between 1 and 6."
                )
        except ValueError:
            QMessageBox.warning(
                self, 
                "Invalid Input", 
                "Please enter a valid number."
            )

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
            # self.wrapper.update_roi(new_roi)
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

        # Connect pattern selection changes
        self.smooth_radio.toggled.connect(self.on_pattern_changed)
        self.saccade_radio.toggled.connect(self.on_pattern_changed)
        
        # Create container for direction settings (for smooth pursuit)
        self.direction_settings_container = QWidget()
        direction_layout = QVBoxLayout(self.direction_settings_container)
        direction_layout.setContentsMargins(10, 5, 10, 5)
        direction_layout.setSpacing(8)
        
        # Add a subtle background to the container
        self.direction_settings_container.setStyleSheet("""
            QWidget {
                background-color: rgba(240, 240, 240, 0.5);
                border-radius: 5px;
            }
        """)
        
        # Direction settings label
        direction_header = QLabel("Direction Settings:")
        direction_header.setStyleSheet("color: #455A64; font-weight: bold; background: transparent;")
        direction_layout.addWidget(direction_header)
        
        # Horizontal direction selection
        h_direction_layout = QHBoxLayout()
        h_direction_label = QLabel("Horizontal:")
        h_direction_label.setStyleSheet("color: #455A64; background: transparent;")
        
        self.h_direction_combo = QComboBox()
        self.h_direction_combo.addItems(["left2right", "right2left"])
        self.h_direction_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
        """)
        
        h_direction_layout.addWidget(h_direction_label)
        h_direction_layout.addWidget(self.h_direction_combo)
        direction_layout.addLayout(h_direction_layout)
        
        # Vertical direction selection
        v_direction_layout = QHBoxLayout()
        v_direction_label = QLabel("Vertical:")
        v_direction_label.setStyleSheet("color: #455A64; background: transparent;")
        
        self.v_direction_combo = QComboBox()
        self.v_direction_combo.addItems(["top2bottom", "bottom2top"])
        self.v_direction_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
        """)
        
        v_direction_layout.addWidget(v_direction_label)
        v_direction_layout.addWidget(self.v_direction_combo)
        direction_layout.addLayout(v_direction_layout)

        # Direction first selection
        direction_first_layout = QHBoxLayout()
        direction_first_label = QLabel("Horizontal or Vertical First:")
        direction_first_label.setStyleSheet("color: #455A64; background: transparent;")
        
        self.direction_first_combo = QComboBox()
        self.direction_first_combo.addItems(["Horizontal", "Vertical"])
        self.direction_first_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
        """)
        
        direction_first_layout.addWidget(direction_first_label)
        direction_first_layout.addWidget(self.direction_first_combo)
        direction_layout.addLayout(direction_first_layout)


        # Confirm button for direction settings
        self.confirm_direction_button = QPushButton("Confirm Directions")
        self.confirm_direction_button.setStyleSheet(StyleSheetMain.BUTTON)
        self.confirm_direction_button.clicked.connect(self.confirm_direction_settings)
        direction_layout.addWidget(self.confirm_direction_button)
        
        layout.addWidget(self.direction_settings_container)
        
        # Create a container for saccade-specific settings
        self.saccade_settings_container = QWidget()
        saccade_layout = QVBoxLayout(self.saccade_settings_container)
        saccade_layout.setContentsMargins(10, 5, 10, 5)
        saccade_layout.setSpacing(8)
        
        # Add a subtle background to the container
        self.saccade_settings_container.setStyleSheet("""
            QWidget {
                background-color: rgba(240, 240, 240, 0.5);
                border-radius: 5px;
            }
        """)
        
        # Saccade part selection
        saccade_part_layout = QHBoxLayout()
        saccade_part_label = QLabel("Saccade Part:")
        saccade_part_label.setStyleSheet("color: #455A64; background: transparent;")
        
        self.saccade_part_input = QLineEdit("1")
        self.saccade_part_input.setFixedWidth(50)
        self.saccade_part_input.setValidator(QIntValidator(1, 10))  # Limit to numbers 1-10
        self.saccade_part_input.setAlignment(Qt.AlignCenter)
        self.saccade_part_input.setToolTip("Choose a saccade pattern part (1-10)")
        self.saccade_part_input.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
        """)
        
        self.confirm_part_button = QPushButton("Apply")
        self.confirm_part_button.setStyleSheet(StyleSheetMain.BUTTON)
        self.confirm_part_button.setFixedWidth(70)
        self.confirm_part_button.clicked.connect(self.confirm_saccade_part)
        
        saccade_part_layout.addWidget(saccade_part_label)
        saccade_part_layout.addWidget(self.saccade_part_input)
        saccade_part_layout.addWidget(self.confirm_part_button)
        saccade_part_layout.addStretch()
        
        saccade_layout.addLayout(saccade_part_layout)
        layout.addWidget(self.saccade_settings_container)
        
        # Initially hide saccade settings
        self.saccade_settings_container.setVisible(False)
        
        # Add waiting time section with improved styling
        waiting_section = QHBoxLayout()
        waiting_label = QLabel("Countdown Time:")
        waiting_label.setStyleSheet("color: #455A64;")
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        self.start_button = QPushButton("▶ Start Recording")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.start_button.setFixedSize(160, 40)
        self.start_button.clicked.connect(self.start_selected_pattern)
        
        # Stop button
        self.stop_button = QPushButton("⬛ Stop")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.stop_button.setFixedSize(100, 40)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_recording)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        recording_group.setLayout(layout)
        return recording_group
    # def create_recording_group(self):
    #     recording_group = QGroupBox("Recording Controls")
    #     recording_group.setStyleSheet(StyleSheetMain.GROUP_BOX)
    #     layout = QVBoxLayout()
    #     layout.setSpacing(15)
    #     layout.setContentsMargins(15, 25, 15, 15)  # Top margin increased for title
        
    #     # Pattern selection label with icon
    #     pattern_header = QHBoxLayout()
    #     pattern_header.setContentsMargins(0, 0, 0, 5)
    #     pattern_icon = QLabel("🎯")
    #     pattern_icon.setFont(QFont("", 16))
    #     pattern_label = QLabel("Recording Style:")
    #     pattern_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #455A64;")
    #     pattern_header.addWidget(pattern_icon)
    #     pattern_header.addWidget(pattern_label)
    #     pattern_header.addStretch()
    #     layout.addLayout(pattern_header)
        
    #     # Radio buttons for pattern selection
    #     self.pattern_group = QButtonGroup(self)
        
    #     # Smooth Pursuit radio
    #     self.smooth_radio = QRadioButton("Smooth Pursuit")
    #     self.smooth_radio.setStyleSheet(StyleSheetMain.RADIO_BUTTON)
    #     self.smooth_radio.setChecked(True)
    #     self.pattern_group.addButton(self.smooth_radio)
    #     layout.addWidget(self.smooth_radio)
        
    #     # Saccade radio
    #     self.saccade_radio = QRadioButton("Saccade")
    #     self.saccade_radio.setStyleSheet(StyleSheetMain.RADIO_BUTTON)
    #     self.pattern_group.addButton(self.saccade_radio)
    #     layout.addWidget(self.saccade_radio)

    #     # Connect pattern selection changes
    #     self.smooth_radio.toggled.connect(self.on_pattern_changed)
    #     self.saccade_radio.toggled.connect(self.on_pattern_changed)

    #     # Create a container for saccade-specific settings
    #     self.saccade_settings_container = QWidget()
    #     saccade_layout = QVBoxLayout(self.saccade_settings_container)
    #     saccade_layout.setContentsMargins(10, 5, 10, 5)
    #     saccade_layout.setSpacing(8)
        
    #     # Add a subtle background to the container
    #     self.saccade_settings_container.setStyleSheet("""
    #         QWidget {
    #             background-color: rgba(240, 240, 240, 0.5);
    #             border-radius: 5px;
    #         }
    #     """)
        
    #     # Saccade part selection
    #     saccade_part_layout = QHBoxLayout()
    #     saccade_part_label = QLabel("Saccade Part:")
    #     saccade_part_label.setStyleSheet("color: #455A64; background: transparent;")
        
    #     self.saccade_part_input = QLineEdit("1")
    #     self.saccade_part_input.setFixedWidth(50)
    #     self.saccade_part_input.setValidator(QIntValidator(1, 10))  # Limit to numbers 1-10
    #     self.saccade_part_input.setAlignment(Qt.AlignCenter)
    #     self.saccade_part_input.setToolTip("Choose a saccade pattern part (1-10)")
    #     self.saccade_part_input.setStyleSheet("""
    #         QLineEdit {
    #             padding: 4px;
    #             border: 1px solid #ccc;
    #             border-radius: 3px;
    #             background-color: white;
    #         }
    #     """)
        
    #     self.confirm_part_button = QPushButton("Apply")
    #     self.confirm_part_button.setStyleSheet(StyleSheetMain.BUTTON)
    #     self.confirm_part_button.setFixedWidth(70)
    #     self.confirm_part_button.clicked.connect(self.confirm_saccade_part)
        
    #     saccade_part_layout.addWidget(saccade_part_label)
    #     saccade_part_layout.addWidget(self.saccade_part_input)
    #     saccade_part_layout.addWidget(self.confirm_part_button)
    #     saccade_part_layout.addStretch()
        
    #     saccade_layout.addLayout(saccade_part_layout)
    #     layout.addWidget(self.saccade_settings_container)
        
    #     # Initially hide saccade settings
    #     self.saccade_settings_container.setVisible(False)
        
    #     # Add waiting time section with improved styling
    #     waiting_section = QHBoxLayout()
    #     waiting_label = QLabel("Countdown Time:")
    #     waiting_label.setStyleSheet("color: #455A64;")
        
    #     self.waiting_time_input = QLineEdit()
    #     self.waiting_time_input.setFixedWidth(60)
    #     self.waiting_time_input.setAlignment(Qt.AlignCenter)
    #     self.waiting_time_input.setStyleSheet("""
    #         QLineEdit {
    #             padding: 4px;
    #             border: 1px solid #ccc;
    #             border-radius: 3px;
    #             background-color: white;
    #         }
    #     """)
    #     self.waiting_time_input.setText(str(self.recording_waiting_time))
        
    #     waiting_seconds_label = QLabel("seconds")
    #     waiting_seconds_label.setStyleSheet("color: #455A64;")
        
    #     # Add validator for integers only
    #     validator = QIntValidator(1, 60)  # Limit to reasonable countdown values
    #     self.waiting_time_input.setValidator(validator)
    #     self.waiting_time_input.setToolTip("Set countdown time before recording (1-60 seconds)")
        
    #     # Add focus out event to validate when leaving the text box
    #     self.waiting_time_input.focusOutEvent = self.validate_waiting_time
    #     # Add text changed event
    #     self.waiting_time_input.textChanged.connect(self.on_waiting_time_changed)
        
    #     waiting_section.addWidget(waiting_label)
    #     waiting_section.addWidget(self.waiting_time_input)
    #     waiting_section.addWidget(waiting_seconds_label)
    #     waiting_section.addStretch()
        
    #     layout.addLayout(waiting_section)
    #     layout.addSpacing(15)  # Add space before buttons
        
    #     # Control buttons container with improved styling
    #     buttons_layout = QHBoxLayout()
    #     buttons_layout.setSpacing(10)
        
    #     # Start button
    #     self.start_button = QPushButton("▶ Start Recording")
    #     self.start_button.setStyleSheet("""
    #         QPushButton {
    #             background-color: #4CAF50;
    #             color: white;
    #             border: none;
    #             border-radius: 5px;
    #             padding: 8px 16px;
    #             font-weight: bold;
    #         }
    #         QPushButton:hover {
    #             background-color: #45a049;
    #         }
    #         QPushButton:pressed {
    #             background-color: #3d8b40;
    #         }
    #         QPushButton:disabled {
    #             background-color: #cccccc;
    #             color: #666666;
    #         }
    #     """)
    #     self.start_button.setFixedSize(160, 40)
    #     self.start_button.clicked.connect(self.start_selected_pattern)
        
    #     # Stop button
    #     self.stop_button = QPushButton("⬛ Stop")
    #     self.stop_button.setStyleSheet("""
    #         QPushButton {
    #             background-color: #f44336;
    #             color: white;
    #             border: none;
    #             border-radius: 5px;
    #             padding: 8px 16px;
    #             font-weight: bold;
    #         }
    #         QPushButton:hover {
    #             background-color: #d32f2f;
    #         }
    #         QPushButton:pressed {
    #             background-color: #b71c1c;
    #         }
    #         QPushButton:disabled {
    #             background-color: #cccccc;
    #             color: #666666;
    #         }
    #     """)
    #     self.stop_button.setFixedSize(100, 40)
    #     self.stop_button.setEnabled(False)
    #     self.stop_button.clicked.connect(self.stop_recording)
        
    #     buttons_layout.addWidget(self.start_button)
    #     buttons_layout.addWidget(self.stop_button)
    #     buttons_layout.addStretch()
        
    #     layout.addLayout(buttons_layout)
        
    #     recording_group.setLayout(layout)
    #     return recording_group
    
    def confirm_direction_settings(self):
        """Handle direction settings confirmation"""
        self.horizontal_direction = self.h_direction_combo.currentText()
        self.vertical_direction = self.v_direction_combo.currentText()
        self.direction_first = self.direction_first_combo.currentText()

        QMessageBox.information(
            self, 
            "Direction Settings", 
            f"Direction settings confirmed:\nHorizontal: {self.horizontal_direction}\nVertical: {self.vertical_direction} \n Direction {self.direction_first}"
        )
        self.direction_confirmed = True
        
        # Visual feedback
        self.confirm_direction_button.setText("✓ Confirmed")
        self.confirm_direction_button.setEnabled(False)
        
        # Reset button after 1 second
        QTimer.singleShot(1000, lambda: self.confirm_direction_button.setEnabled(True))
        QTimer.singleShot(1000, lambda: self.confirm_direction_button.setText("Confirm Directions"))
        
        self.update_start_button_state()

    def on_pattern_changed(self):
        """Handle pattern selection changed"""
        is_saccade_mode = self.saccade_radio.isChecked()
        is_smooth_mode = self.smooth_radio.isChecked()
        
        if is_smooth_mode:
            self.current_label_mode = label_mode[0]
            self.direction_confirmed = False  # Reset direction confirmation when switching modes
        else:
            self.current_label_mode = label_mode[1]
        
        # Toggle visibility of settings containers
        self.saccade_settings_container.setVisible(is_saccade_mode)
        self.direction_settings_container.setVisible(is_smooth_mode)
        
        self.update_start_button_state()

    # def on_pattern_changed(self):
    #     """Handle pattern selection changed"""
    #     is_saccade_mode = self.saccade_radio.isChecked()
    #     is_smooth_mode = self.smooth_radio.isChecked()
    #     if is_smooth_mode:
    #         self.current_label_mode = label_mode[0]
    #         self.update_start_button_state()
    #     else:
    #         self.update_start_button_state()
    #         self.current_label_mode = label_mode[1]

    #     self.saccade_settings_container.setVisible(is_saccade_mode)
        
    #     # If switching to saccade mode and part wasn't set yet, ensure we have a default
    #     if is_saccade_mode and not hasattr(self, 'current_saccade_part'):
    #         self.current_saccade_part = 0  # Default to first part (0-based index)


    def start_selected_pattern(self):
        """Start recording with the selected pattern"""
        if not self.pattern_group.checkedButton():
            # No pattern selected
            return
        self.show()
        if self.pattern_group.checkedButton() == self.smooth_radio:
            self.start_smooth_pursuit()
        else:
            self.start_saccade_pursuit()
        self.show()
        if self.current_pattern_obj is not None:            
            self.current_pattern_obj.end_animation()
        self.show()

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
        self.file_text_box.setText(self.default_filename) # Base filename without extension
        self.file_text_box.setStyleSheet(StyleSheetMain.TEXTBOX)
        # Connect text change to reset confirmation flag
        self.file_text_box.textChanged.connect(self.on_filename_changed)
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
    
    def on_filename_changed(self, text):
        """Reset filename confirmation when text is changed"""
        self.filename_confirmed = False
        self.update_start_button_state()
    
    def open_csv_analysis(self):
        """Open the CSV Analysis window"""
        self.csv_analysis_window = CSVAnalysisWindow()
        self.csv_analysis_window.show()

    def start_recording(self):
        if self.pattern_group.checkedButton() == self.saccade_radio:
            part = self.current_saccade_part
            x1, y1, x2, y2 =  self.wrapper.roi_coordinates
            coord_str = f"{x1}_{y1}_{x2}_{y2}"
            print(coord_str)
            self.current_label_filename = f"label_{coord_str}_{self.file_text_box.text()}_part{part+1}.csv"
            self.current_record_filename = f"record_{coord_str}_{self.file_text_box.text()}_part{part+1}.raw"
            self.current_config_filename = f"config_{coord_str}_{self.file_text_box.text()}_part{part+1}.yaml"

        print(f"Log file: {self.current_label_filename}")
        print(f"Record file: {self.current_record_filename}")
        print("Start recoding at timestamp: ", self.events[-1][3])
        self.current_starting_timestamp = self.events[-1][3]
        self.write_yaml_file()
        self.wrapper.start_recording(self.current_record_filename)
        self.is_recording = True
        print("Is recording: ", self.is_recording)
        self.stop_button.setEnabled(True)
        self.start_button.setEnabled(False)
        self.smooth_radio.setEnabled(False)
        self.saccade_radio.setEnabled(False)

    def write_yaml_file(self):
        if self.current_label_mode == label_mode[0]:
            config_data = {
                'label_mode': self.current_label_mode,
                'files': {
                    'default_filename': self.default_filename,
                    'label_filename': self.current_label_filename,
                    'record_filename': self.current_record_filename,
                    'config_filename': self.current_config_filename,
                    'config_yaml_path': self.config_yaml_path
                },
                'recording': {
                    'waiting_time': self.recording_waiting_time,
                    'is_recording': self.is_recording,
                    'starting_timestamp': int(self.current_starting_timestamp),
                    'horizontal_direction': self.horizontal_direction,
                    'vertical_direction': self.vertical_direction,
                    "horizontal_first": self.direction_first
                },
                'display': {
                    'roi': self.roi,
                    'roi_control_mode': self.roi_control_mode
                },
                'states': {
                    'filename_confirmed': self.filename_confirmed
                }
            }
        else:
            config_data = {
                'label_mode': self.current_label_mode,
                'files': {
                    'default_filename': self.default_filename,
                    'label_filename': self.current_label_filename,
                    'record_filename': self.current_record_filename,
                    'config_filename': self.current_config_filename,
                    'config_yaml_path': self.config_yaml_path
                },
                'recording': {
                    'waiting_time': self.recording_waiting_time,
                    'is_recording': self.is_recording,
                    'saccade_part': self.current_saccade_part,
                    'starting_timestamp': int(self.current_starting_timestamp)
                },
                'display': {
                    'roi': self.roi,
                    'roi_control_mode': self.roi_control_mode
                },
                'states': {
                    'filename_confirmed': self.filename_confirmed
                }
            }

        with open(os.path.join(self.config_yaml_path, self.current_config_filename), 'w') as file:
            
            yaml.dump(config_data, file, default_flow_style=False, sort_keys=False)

    def stop_recording(self):
        print("stop recording file ", self.current_record_filename)
        self.wrapper.stop_recording()
        self.is_recording = False
        print("Is recording: ", self.is_recording)
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)
        self.smooth_radio.setEnabled(True)
        self.saccade_radio.setEnabled(True)
            
        cv2.destroyAllWindows()
        # Close the pattern window if it exists
        if self.current_pattern_obj is not None:
            self.current_pattern_obj.end_animation()
            self.current_pattern_obj.hide()
            self.current_pattern_obj.close()
            self.current_pattern_obj = None
            
        self.part_confirmed = False
        self.update_start_button_state()

    # def start_smooth_pursuit(self):
    #     """Start the smooth pursuit pattern"""
    #     self.start_recording()
    #     self.current_pattern_obj = SmoothHorizontalPursuitWidget(self, "config/config_smooth.yaml", self.wrapper)
    #     if self.current_pattern_obj is not None:
    #         self.current_pattern_obj.showFullScreen()
    #         self.current_pattern_obj.start_animation()

    def start_smooth_pursuit(self):
        """Start the smooth pursuit pattern"""
        self.start_recording()
        self.current_pattern_obj = SmoothPursuitWidget(
            self, 
            "config/config_smooth.yaml", 
            self.wrapper,
            horizontal_direction=self.horizontal_direction,
            vertical_direction=self.vertical_direction,
            direction_first = self.direction_first
        )
        if self.current_pattern_obj is not None:
            self.current_pattern_obj.showFullScreen()
            self.current_pattern_obj.start_animation()

    def start_saccade_pursuit(self):
        """Start the saccade pattern"""
        self.start_recording()
        self.current_pattern_obj = SaccadePursuitWidget(self, "config/config_saccade.yaml", self.wrapper)
        if self.current_pattern_obj is not None:
            self.current_pattern_obj.showFullScreen()
            self.current_pattern_obj.start_animation()

    def set_text_log_textbox(self, textbox: QLineEdit):
        self.current_label_filename = textbox.text()
        print(self.current_label_filename)

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

    # def process_events(self, event_frame_gen, output_dir=None, max_events=None):
    #     """
    #     Process events and optionally write them to a CSV file.
        
    #     Args:
    #         event_frame_gen: The event frame generator
    #         output_dir: Directory to save the CSV file (default: None)
    #         max_events: Maximum number of events to save (default: None, save all)
    #     """
    #     try:
            
    #         # Create output directory if it doesn't exist
    #         if self.csv_record_path:
    #             os.makedirs(self.csv_record_path, exist_ok=True)
    #             csv_path = os.path.join(self.csv_record_path, self.current_csv_record_filename)
                
    #             with open(csv_path, 'w', newline='') as csv_file:
    #                 # Create CSV writer with appropriate headers for event data
    #                 # Assuming events have x, y, p (polarity), and t (timestamp) attributes
    #                 csv_writer = csv.writer(csv_file)
    #                 csv_writer.writerow(['x', 'y', 'p', 't'])
                    
    #                 for evs in self.wrapper.mv_iterator:
    #                     EventLoop.poll_and_dispatch()
    #                     self.events = evs
    #                     event_frame_gen.process_events(evs)
                        
    #                     # Write events to CSV
    #                     for ev in evs:
    #                         csv_writer.writerow([self.events.x, ev.y, ev.p, ev.t])
    #                         event_count += 1
                    
    #         print(f"Successfully wrote {event_count} events to {csv_path}")
                    
    #     except Exception as e:
    #         print(f"Error in Metavision pipeline: {str(e)}")

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

    def update_start_button_state(self):
        """Update the state of the start button based on current conditions"""
        # Check if filename is confirmed
        if not self.filename_confirmed:
            self.start_button.setEnabled(False)
            self.start_button.setToolTip("Please confirm the file name first")
            return
        
        # If in smooth mode, check direction confirmation
        if self.smooth_radio.isChecked() and not self.direction_confirmed:
            self.start_button.setEnabled(False)
            self.start_button.setToolTip("Please confirm direction settings first")
            return
        
        # If in saccade mode, check part confirmation
        if self.saccade_radio.isChecked() and not self.part_confirmed:
            self.start_button.setEnabled(False)
            self.start_button.setToolTip("Please confirm the saccade part first")
            return
        
        # If all conditions are met
        self.start_button.setEnabled(True)
        self.start_button.setToolTip("Start recording")

    # def update_start_button_state(self):
    #     """Update the state of the start button based on current conditions"""
    #     # Check if filename is confirmed
    #     if not self.filename_confirmed:
    #         self.start_button.setEnabled(False)
    #         self.start_button.setToolTip("Please confirm the file name first")
    #         return
            
    #     # If in saccade mode, also check part confirmation
    #     if self.saccade_radio.isChecked() and not self.part_confirmed:
    #         self.start_button.setEnabled(False)
    #         self.start_button.setToolTip("Please confirm the saccade part first")
    #         return
            
    #     # If all conditions are met
    #     self.start_button.setEnabled(True)
    #     self.start_button.setToolTip("Start recording")