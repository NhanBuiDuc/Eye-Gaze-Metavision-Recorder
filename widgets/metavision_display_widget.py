from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                            QWidget, QPushButton, QLabel)
from PyQt5.QtGui import QImage, QPainter, QFont, QPen, QColor
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
import cv2

class MetavisionDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.setMinimumSize(640, 480)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)

    def update_frame(self, frame):
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.image = QImage(frame.data, frame.shape[1], frame.shape[0],
                              frame.strides[0], QImage.Format_RGB888)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.image is not None:
            scaled_img = self.image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled_img.width()) // 2
            y = (self.height() - scaled_img.height()) // 2
            painter.drawImage(x, y, scaled_img)