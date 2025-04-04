from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
import cv2

class DynamicROIDisplayWidget(QWidget):
    # Signals
    roi_changed = pyqtSignal(list)  # Emits [x1, y1, x2, y2]
    coordinates_updated = pyqtSignal(str)  # Emits coordinate string for display

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.setMinimumSize(640, 480)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        
        # ROI drawing states
        self.drawing = False
        self.dragging = False
        self.resizing = False
        self.roi_start = QPoint()
        self.roi_end = QPoint()
        self.drag_start = QPoint()
        self.resize_margin = 10  # pixels
        
        # Initial ROI coordinates
        self.roi_coords = [300,200,900,600]
        self.drag_enabled = True
        
        # Enable mouse tracking
        self.setMouseTracking(True)

    def set_drag_enabled(self, enabled):
        """Enable or disable drag functionality"""
        self.drag_enabled = enabled

    def set_roi(self, roi_coords):
        """Set ROI coordinates programmatically"""
        self.roi_coords = roi_coords
        self.update()
        scaled_roi = self.get_scaled_roi()
        self.roi_changed.emit(scaled_roi)
        
    def update_frame(self, frame, flag_mode=None):
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.image = QImage(frame.data, frame.shape[1], frame.shape[0],
                            frame.strides[0], QImage.Format_RGB888)
            
            # Calculate and store image boundaries within the widget
            scaled_img = self.image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_x_offset = (self.width() - scaled_img.width()) // 2
            self.img_y_offset = (self.height() - scaled_img.height()) // 2
            self.img_width = scaled_img.width()
            self.img_height = scaled_img.height()
            
            self.update()
            
            coords = self.get_scaled_roi(flag_mode)
            coord_str = f"ROI: ({coords[0]}, {coords[1]}, {coords[2]}, {coords[3]})"
            self.coordinates_updated.emit(coord_str)

    def get_scaled_roi(self, flag=None):
        """Convert ROI coordinates from widget space to image space"""
        if self.image is None:
            return self.roi_coords
        
        if flag == "manual":
            return self.roi_coords

        # Get the scaled image dimensions and position
        scaled_img = self.image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x_offset = (self.width() - scaled_img.width()) // 2
        y_offset = (self.height() - scaled_img.height()) // 2
        
        # print(self.width(), self.height())
        
        # Convert coordinates
        scale_x = self.image.width() / scaled_img.width()
        scale_y = self.image.height() / scaled_img.height()
        
        x1 = int((self.roi_coords[0] - x_offset) * scale_x)
        y1 = int((self.roi_coords[1] - y_offset) * scale_y)
        x2 = int((self.roi_coords[2] - x_offset) * scale_x)
        y2 = int((self.roi_coords[3] - y_offset) * scale_y)
        
        return [x1, y1, x2, y2]
    def is_inside_image(self, pos):
        """Check if a point is inside the displayed image area"""
        if not hasattr(self, 'img_x_offset'):
            return True  # Default to true if image hasn't been loaded yet
            
        return (self.img_x_offset <= pos.x() <= self.img_x_offset + self.img_width and
                self.img_y_offset <= pos.y() <= self.img_y_offset + self.img_height)
    
    def mousePressEvent(self, event):
        if not self.drag_enabled:
            return
        
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            
            # Check if we're clicking within the image area
            if not self.is_inside_image(pos):
                return
            
            # Check if clicking near ROI edges for resizing
            if self.is_near_roi_edge(pos):
                self.resizing = True
                self.resize_start = pos
                return
                
            # Check if clicking inside ROI for dragging
            if self.is_inside_roi(pos):
                self.dragging = True
                self.drag_start = pos
                return
                
            # Start drawing new ROI
            self.drawing = True
            self.roi_start = pos
            self.roi_end = pos
            self.roi_coords = [pos.x(), pos.y(), pos.x(), pos.y()]
            
    def mouseReleaseEvent(self, event):
        if not self.drag_enabled:
            return
        if event.button() == Qt.LeftButton:
            if any([self.drawing, self.dragging, self.resizing]):
                # Emit the new ROI coordinates
                scaled_roi = self.get_scaled_roi()
                self.roi_changed.emit(scaled_roi)
            
            self.drawing = False
            self.dragging = False
            self.resizing = False

    def mouseMoveEvent(self, event):
        if not self.drag_enabled:
            return
        pos = event.pos()
        
        # Get image boundaries
        img_left = self.img_x_offset
        img_right = self.img_x_offset + self.img_width
        img_top = self.img_y_offset
        img_bottom = self.img_y_offset + self.img_height
        
        if self.drawing:
            # When drawing, clamp the mouse position to the image boundaries
            clamped_x = max(img_left, min(pos.x(), img_right))
            clamped_y = max(img_top, min(pos.y(), img_bottom))
            self.roi_end = QPoint(clamped_x, clamped_y)
            
            self.roi_coords = [
                min(self.roi_start.x(), self.roi_end.x()),
                min(self.roi_start.y(), self.roi_end.y()),
                max(self.roi_start.x(), self.roi_end.x()),
                max(self.roi_start.y(), self.roi_end.y())
            ]
            self.update()
            
        elif self.dragging:
            dx = pos.x() - self.drag_start.x()
            dy = pos.y() - self.drag_start.y()
            
            # Calculate new ROI coordinates
            new_x1 = self.roi_coords[0] + dx
            new_y1 = self.roi_coords[1] + dy
            new_x2 = self.roi_coords[2] + dx
            new_y2 = self.roi_coords[3] + dy
            
            # Check if new coordinates will be within image boundaries
            if new_x1 < img_left:
                dx = img_left - self.roi_coords[0]
            elif new_x2 > img_right:
                dx = img_right - self.roi_coords[2]
                
            if new_y1 < img_top:
                dy = img_top - self.roi_coords[1]
            elif new_y2 > img_bottom:
                dy = img_bottom - self.roi_coords[3]
            
            # Apply the constrained movement
            self.roi_coords = [
                self.roi_coords[0] + dx,
                self.roi_coords[1] + dy,
                self.roi_coords[2] + dx,
                self.roi_coords[3] + dy
            ]
            
            self.drag_start = pos
            self.update()
            
        elif self.resizing:
            # Clamp the resize position to image boundaries
            clamped_x = max(img_left, min(pos.x(), img_right))
            clamped_y = max(img_top, min(pos.y(), img_bottom))
            
            self.roi_coords[2] = clamped_x
            self.roi_coords[3] = clamped_y
            self.update()
        
    def is_inside_roi(self, pos):
        return (self.roi_coords[0] <= pos.x() <= self.roi_coords[2] and
                self.roi_coords[1] <= pos.y() <= self.roi_coords[3])

    def is_near_roi_edge(self, pos):
        # Check if position is near any edge of the ROI
        x, y = pos.x(), pos.y()
        
        near_right = abs(x - self.roi_coords[2]) < self.resize_margin
        near_bottom = abs(y - self.roi_coords[3]) < self.resize_margin
        within_y = self.roi_coords[1] <= y <= self.roi_coords[3]
        within_x = self.roi_coords[0] <= x <= self.roi_coords[2]
        
        return (near_right and within_y) or (near_bottom and within_x)

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw the image
        if self.image is not None:
            scaled_img = self.image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled_img.width()) // 2
            y = (self.height() - scaled_img.height()) // 2
            
            # Draw the full image with reduced opacity
            painter.setOpacity(0.0)  # Make the background image semi-transparent
            painter.drawImage(x, y, scaled_img)
            
            # Reset opacity for the ROI
            painter.setOpacity(1.0)
            
            # Calculate the portion of the image to display at full opacity
            roi_x = self.roi_coords[0]
            roi_y = self.roi_coords[1]
            roi_width = self.roi_coords[2] - self.roi_coords[0]
            roi_height = self.roi_coords[3] - self.roi_coords[1]
            
            # Create a clipping region for the ROI area
            painter.setClipRect(roi_x, roi_y, roi_width, roi_height)
            
            # Draw the ROI portion at full opacity
            painter.drawImage(x, y, scaled_img)
            
            # Remove the clipping to draw the border
            painter.setClipping(False)
            
            # Draw the ROI rectangle outline
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.SolidLine))
            painter.drawRect(roi_x, roi_y, roi_width, roi_height)