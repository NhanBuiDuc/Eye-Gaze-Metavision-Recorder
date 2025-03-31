import cv2
import time
import numpy as np
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QBrush, QColor
from PyQt5.QtCore import Qt, QRectF

class EventDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.frame_count = 0
        self.last_update_time = time.time()
        self.current_point = None
        self.next_point = None
        
        # Set minimum size
        self.setMinimumSize(320, 240)
        
        # Background color for when no image is present
        self.background_color = QColor(40, 40, 40)
        
        # Image positioning
        self.image_x = 0
        self.image_y = 0
        self.image_width = 0
        self.image_height = 0
    
    def update_image_boundaries(self):
        """Calculate image position and size to maintain aspect ratio"""
        if self.image is None:
            return
            
        widget_width = self.width()
        widget_height = self.height()
        
        image_width = self.image.width()
        image_height = self.image.height()
        
        # Calculate aspect ratios
        widget_ratio = widget_width / widget_height
        image_ratio = image_width / image_height
        
        if widget_ratio > image_ratio:
            # Widget is wider than image - fit image to height
            self.image_height = widget_height
            self.image_width = image_height * image_ratio
            self.image_y = 0
            self.image_x = int((widget_width - self.image_width) / 2)
        else:
            # Widget is taller than image - fit image to width
            self.image_width = widget_width
            self.image_height = image_width / image_ratio
            self.image_x = 0
            self.image_y = int((widget_height - self.image_height) / 2)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(event.rect(), QBrush(self.background_color))
        
        # Draw image if available
        if self.image:
            target_rect = QRectF(self.image_x, self.image_y, self.image_width, self.image_height)
            painter.drawImage(target_rect, self.image)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image_boundaries()
    
    def set_current_point(self, point, next_point=None):
        """Set the current point to display"""
        self.current_point = point
        self.next_point = next_point
    
    def update_frame(self, frame):
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        
        if time_diff < 0.1:
            return
            
        self.last_update_time = current_time
        self.frame_count += 1
        
        if frame is not None:
            try:
                if len(frame.shape) == 2:
                    height, width = frame.shape
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                    
                    frame_rgb = cv2.flip(frame_rgb, 1)

                    # Draw current point on frame if available
                    if self.current_point:
                        # Scale point from 1920x1080 to frame size
                        x_scale = width / 1920
                        y_scale = height / 1080
                        
                        x = int(self.current_point[0] * x_scale)
                        y = int(self.current_point[1] * y_scale)
                        
                        # Draw current point
                        cv2.circle(frame_rgb, (x, y), max(3, int(10 * x_scale)), (0, 0, 255), -1)
                        
                        # Draw next point and connecting line if available
                        if self.next_point:
                            next_x = int(self.next_point[0] * x_scale)
                            next_y = int(self.next_point[1] * y_scale)
                            
                            cv2.circle(frame_rgb, (next_x, next_y), max(2, int(6 * x_scale)), (0, 255, 0), -1)
                            cv2.line(frame_rgb, (x, y), (next_x, next_y), (255, 0, 0), max(1, int(2 * x_scale)))
                    
                    bytes_per_line = frame_rgb.strides[0]
                    self.image = QImage(
                        frame_rgb.data, width, height, 
                        bytes_per_line, QImage.Format_RGB888
                    )
                else:
                    height, width = frame.shape[:2]
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Draw current point on frame if available
                    if self.current_point:
                        # Scale point from 1920x1080 to frame size
                        x_scale = width / 1920
                        y_scale = height / 1080
                        
                        x = int(self.current_point[0] * x_scale)
                        y = int(self.current_point[1] * y_scale)
                        
                        # Draw current point
                        cv2.circle(frame_rgb, (x, y), max(3, int(10 * x_scale)), (0, 0, 255), -1)
                        
                        # Draw next point and connecting line if available
                        if self.next_point:
                            next_x = int(self.next_point[0] * x_scale)
                            next_y = int(self.next_point[1] * y_scale)
                            
                            cv2.circle(frame_rgb, (next_x, next_y), max(2, int(6 * x_scale)), (0, 255, 0), -1)
                            cv2.line(frame_rgb, (x, y), (next_x, next_y), (255, 0, 0), max(1, int(2 * x_scale)))
                    
                    bytes_per_line = frame_rgb.strides[0]
                    self.image = QImage(
                        frame_rgb.data, width, height, 
                        bytes_per_line, QImage.Format_RGB888
                    )
                
                self.update_image_boundaries()
                self.update()
            except Exception as e:
                print(f"Error in update_frame: {e}")