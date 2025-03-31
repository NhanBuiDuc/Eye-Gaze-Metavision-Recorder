import os
import sys
import yaml
import csv
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QFileDialog, QTextEdit, QGroupBox,
                           QGridLayout, QFrame, QSplitter, QMessageBox, QSpinBox,
                           QTabWidget, QScrollArea, QDialog)
from PyQt5.QtGui import QFont, QColor, QPalette, QImage, QPixmap
from PyQt5.QtCore import Qt, QSize

from file_reader_app import FileReaderApp

def main():
    app = QApplication(sys.argv)
    window = FileReaderApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()