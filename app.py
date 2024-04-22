import sys
import cv2
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QImage, QPixmap, QPainter, QPen, QColor
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QSizePolicy, QPushButton, QGridLayout, QDialog, QComboBox

class CameraSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Camera")

        layout = QVBoxLayout()

        self.camera_combobox = QComboBox()
        self.populate_camera_combobox()
        layout.addWidget(self.camera_combobox)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def populate_camera_combobox(self):
        num_cameras = 4  # Assume there are 4 cameras available
        for i in range(num_cameras):
            self.camera_combobox.addItem(f"Camera {i}")

    def selected_camera_index(self):
        return self.camera_combobox.currentIndex()

class DrawingCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.points = []

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)  # Imposta lo sfondo bianco
        pen = QPen()
        pen.setColor(Qt.blue)
        pen.setWidth(5)
        painter.setPen(pen)
        for i in range(1, len(self.points)):
            painter.drawLine(self.points[i - 1], self.points[i])

    def mousePressEvent(self, event):
        self.points.append(event.pos())
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIR WRITING")
        self.resize(1600, 600)  # Set initial size of the window

        # Creating the main layout
        layout = QGridLayout()

        # Placeholder label for the webcam video
        self.video_label = QLabel()
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #CCCCCC; color: black; font-size: 20px;")
        layout.addWidget(self.video_label, 0, 0, 1, 1)


        # Button to select camera
        self.select_camera_button = QPushButton("Select Camera")
        font = QFont("Arial", 14, QFont.Bold)
        self.select_camera_button.setFont(font)
        self.select_camera_button.setStyleSheet("QPushButton { text-transform: uppercase; }")
        self.select_camera_button.clicked.connect(self.select_camera)
        layout.addWidget(self.select_camera_button, 0, 0, 1, 1, Qt.AlignTop | Qt.AlignLeft)

        # Drawing canvas
        self.drawing_canvas = DrawingCanvas()
        layout.addWidget(self.drawing_canvas, 0, 1, 1, 1)

        # Button to exit the application
        self.exit_button = QPushButton("EXIT")
        self.exit_button.setFont(font)
        self.exit_button.setStyleSheet("QPushButton { text-transform: uppercase; }")
        self.exit_button.clicked.connect(self.close)
        layout.addWidget(self.exit_button, 1, 0, 1, 2)

        # Set column stretch to evenly distribute the width
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        # Widget for the main layout
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Initialize video capture
        self.video_capture = None
        self.selected_camera_index = None

        # Starting the timer to update the video frame
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30 milliseconds (approximately 30 fps)

    def update_frame(self):
        if self.video_capture is not None and self.selected_camera_index is not None:
            # Read a frame from the webcam
            ret, frame = self.video_capture.read()
            if ret:
                # Convert the frame to a format compatible with QImage
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

                # Resize the image to fit the placeholder label size
                q_image = q_image.scaled(self.placeholder_label.size(), Qt.KeepAspectRatio)

                # Update the image in the placeholder label
                pixmap = QPixmap.fromImage(q_image)
                self.placeholder_label.setPixmap(pixmap)
                # Hide the placeholder label when video is available
                self.placeholder_label.hide()
            else:
                # If reading the frame fails, show an error message
                self.placeholder_label.setText("Error reading frame from webcam")
        else:
            # Show the placeholder label when no camera is selected
            self.placeholder_label.show()


    def select_camera(self):
        dialog = CameraSelectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.selected_camera_index = dialog.selected_camera_index()
            if self.video_capture is not None:
                self.video_capture.release()
            self.video_capture = cv2.VideoCapture(self.selected_camera_index)
            if not self.video_capture.isOpened():
                print(f"Error: Cannot open camera {self.selected_camera_index}")
                self.selected_camera_index = None
            else:
                print(f"Using camera {self.selected_camera_index}")

    def update_frame(self):
        if self.video_capture is not None and self.selected_camera_index is not None:
            # Read a frame from the webcam
            ret, frame = self.video_capture.read()
            if ret:
                # Convert the frame to a format compatible with QImage
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

                # Resize the image to fit the label size
                q_image = q_image.scaled(self.video_label.size(), Qt.KeepAspectRatio)

                # Update the image in the video label
                pixmap = QPixmap.fromImage(q_image)
                self.video_label.setPixmap(pixmap)
            else:
                # If reading the frame fails, show an error message
                self.video_label.setText("Error reading frame from webcam")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
