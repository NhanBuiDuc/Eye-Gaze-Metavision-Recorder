from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFileDialog, QFrame, QProgressBar, QGridLayout,
                           QSpinBox, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
import os
from metavision_core.event_io import EventsIterator
from styles import StyleSheetMain
from tqdm import tqdm

class ConversionWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, input_file, output_file, start_ts, max_duration, delta_t):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.start_ts = start_ts
        self.max_duration = max_duration
        self.delta_t = delta_t
        self.is_running = True

    def run(self):
        try:
            # Create EventsIterator
            mv_iterator = EventsIterator(
                input_path=self.input_file,
                delta_t=self.delta_t,
                start_ts=self.start_ts,
                max_duration=self.max_duration
            )

            total_steps = self.max_duration // self.delta_t
            current_step = 0

            with open(self.output_file, 'w') as csv_file:
                # Write header
                csv_file.write("x,y,p,t\n")
                
                # Process events
                for evs in mv_iterator:
                    if not self.is_running:
                        break
                        
                    for (x, y, p, t) in evs:
                        csv_file.write(f"{x},{y},{p},{t}\n")
                    
                    current_step += 1
                    self.progress.emit(int(100 * current_step / total_steps))

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self.is_running = False


class CSVConverterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RAW to CSV Converter")
        self.conversion_worker = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # File Selection Section
        file_frame = QFrame()
        file_frame.setStyleSheet(f"background-color: {StyleSheetMain.CARD_COLOR}; border-radius: 12px;")
        file_layout = QVBoxLayout(file_frame)

        # Title
        title_layout = QHBoxLayout()
        title_icon = QLabel("🔄")
        title_icon.setFont(QFont("", 20))
        title_label = QLabel("RAW to CSV Converter")
        title_label.setStyleSheet(StyleSheetMain.TITLE_LABEL)
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        file_layout.addLayout(title_layout)

        # Input file selection
        input_layout = QHBoxLayout()
        self.input_label = QLabel("Input: Not selected")
        self.input_label.setStyleSheet(StyleSheetMain.LABEL)
        self.input_btn = QPushButton("Select RAW/DAT File")
        self.input_btn.setStyleSheet(StyleSheetMain.BUTTON)
        self.input_btn.clicked.connect(self.select_input_file)
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_btn)
        file_layout.addLayout(input_layout)



        main_layout.addWidget(file_frame)

        # Parameters Section
        params_frame = QFrame()
        params_frame.setStyleSheet(f"background-color: {StyleSheetMain.CARD_COLOR}; border-radius: 12px;")
        params_layout = QVBoxLayout(params_frame)

        # Parameters title
        params_title = QLabel("Conversion Parameters")
        params_title.setStyleSheet(StyleSheetMain.DISPLAY_TITLE)
        params_layout.addWidget(params_title)

        # Parameters grid
        params_grid = QGridLayout()
        
        # Start time
        params_grid.addWidget(QLabel("Start Time (μs):"), 0, 0)
        self.start_time = QSpinBox()
        self.start_time.setRange(0, 1000000000)
        self.start_time.setValue(0)
        self.start_time.setStyleSheet(StyleSheetMain.TEXTBOX)
        params_grid.addWidget(self.start_time, 0, 1)

        # Duration
        params_grid.addWidget(QLabel("Duration (μs):"), 1, 0)
        self.duration = QSpinBox()
        self.duration.setRange(1, 1000000000)
        self.duration.setValue(60000000)  # 60 seconds default
        self.duration.setStyleSheet(StyleSheetMain.TEXTBOX)
        params_grid.addWidget(self.duration, 1, 1)

        # Delta T
        params_grid.addWidget(QLabel("Delta T (μs):"), 2, 0)
        self.delta_t = QSpinBox()
        self.delta_t.setRange(1000, 1000000)
        self.delta_t.setValue(1000000)  # 1 second default
        self.delta_t.setStyleSheet(StyleSheetMain.TEXTBOX)
        params_grid.addWidget(self.delta_t, 2, 1)

        params_layout.addLayout(params_grid)
        main_layout.addWidget(params_frame)

        # Conversion Controls
        controls_frame = QFrame()
        controls_frame.setStyleSheet(f"background-color: {StyleSheetMain.CARD_COLOR}; border-radius: 12px;")
        controls_layout = QVBoxLayout(controls_frame)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.convert_btn = QPushButton("Start Conversion")
        self.convert_btn.setStyleSheet(StyleSheetMain.BUTTON)
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setEnabled(False)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet(StyleSheetMain.STOP_BUTTON)
        self.stop_btn.clicked.connect(self.stop_conversion)
        self.stop_btn.setEnabled(False)

        buttons_layout.addWidget(self.convert_btn)
        buttons_layout.addWidget(self.stop_btn)
        controls_layout.addLayout(buttons_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(StyleSheetMain.PROGRESS_BAR)
        controls_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(StyleSheetMain.LABEL)
        self.status_label.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(self.status_label)

        main_layout.addWidget(controls_frame)

        # Set window background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(StyleSheetMain.BACKGROUND_COLOR))
        self.setPalette(palette)

    def select_input_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Input File", "", "RAW/DAT Files (*.raw *.dat)")
        if filename:
            self.input_label.setText(f"Input: {filename}")
            self.check_conversion_ready()

    def check_conversion_ready(self):
        input_ready = "Not selected" not in self.input_label.text()
        self.convert_btn.setEnabled(input_ready)

    def start_conversion(self):
        # Get input file path
        input_file = self.input_label.text().replace("Input: ", "")
        
        # Get directory and filename from input path
        input_dir = os.path.dirname(input_file)
        input_filename = os.path.basename(input_file)
        name_without_ext = os.path.splitext(input_filename)[0]
        
        # Create output path in same directory as input
        output_file = os.path.join(input_dir, f"{name_without_ext}.csv")
        
        print(f"Converting {input_filename} to {name_without_ext}.csv")
        

        self.conversion_worker = ConversionWorker(
            input_file=input_file,
            output_file=output_file,
            start_ts=self.start_time.value(),
            max_duration=self.duration.value(),
            delta_t=self.delta_t.value()
        )

        self.conversion_worker.progress.connect(self.update_progress)
        self.conversion_worker.finished.connect(self.conversion_finished)
        self.conversion_worker.error.connect(self.conversion_error)

        self.conversion_worker.start()
        
        self.convert_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Converting...")
        self.progress_bar.setValue(0)

    def stop_conversion(self):
        if self.conversion_worker:
            self.conversion_worker.stop()
            self.conversion_worker.wait()
            self.conversion_finished()
            self.status_label.setText("Conversion stopped")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def conversion_finished(self):
        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if self.status_label.text() != "Conversion stopped":
            self.status_label.setText("Conversion completed")
        self.progress_bar.setValue(100)

    def conversion_error(self, error_msg):
        self.status_label.setText(f"Error: {error_msg}")
        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)