import sys
import cv2
import mediapipe as mp
import math
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
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
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.trails = []  # Lista di tratti, ognuno rappresentato da una lista di punti
        self.current_trail = []  # Tratto corrente, iniziato ma non ancora completato
        self.pointer_position = QPoint(0, 0)
        
        # Set the main window reference
        self.main_window = main_window

        # Connection
        if self.main_window:
            self.main_window.pointer_position_changed.connect(self.update_pointer_position)
        else:
            print("Error: MainWindow reference not provided.")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)  # Set the white background
        pen = QPen()
        pen.setColor(Qt.blue)
        pen.setWidth(5)
        painter.setPen(pen)
        for trail in self.trails:
            for i in range(1, len(trail)):
                painter.drawLine(trail[i - 1], trail[i])

        # Disegna anche il tratto corrente
        for i in range(1, len(self.current_trail)):
            painter.drawLine(self.current_trail[i - 1], self.current_trail[i])

        # Draw pointer
        pointer_size = 2  # Dimensione del puntatore
        painter.drawEllipse(self.pointer_position, pointer_size, pointer_size)


    def add_point(self, point):
        # Aggiungi il punto al tratto corrente
        self.current_trail.append(point)
        self.update()

    def start_new_line(self, point):
        # Aggiungi il tratto corrente alla lista di tratti
        if self.current_trail:
            self.trails.append(self.current_trail)
        # Crea un nuovo tratto con il punto fornito
        self.current_trail = [point]
        self.update()

    def update_pointer_position(self, position):
        self.pointer_position = position
        self.update()

class MainWindow(QMainWindow):

    pointer_position_changed = pyqtSignal(QPoint)

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
        self.drawing_canvas = DrawingCanvas(main_window=self)
        layout.addWidget(self.drawing_canvas, 0, 1, 1, 1)

        self.max_writing_distance = 30  # Set the maximum distance value for writing
        self.new_line = False

        self.prev_thumb_tip = None
        self.prev_index_tip = None
        
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

        # Button to clear the drawing canvas
        self.clear_button = QPushButton("Clear")
        self.clear_button.setFont(font)
        self.clear_button.setStyleSheet("QPushButton { text-transform: uppercase; }")
        self.clear_button.clicked.connect(self.clear_canvas)
        layout.addWidget(self.clear_button, 1, 1, 1, 1, Qt.AlignBottom | Qt.AlignRight)
        
        # Initialize video capture
        self.video_capture = None
        self.selected_camera_index = None

        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands()
        self.mp_drawing_utils = mp.solutions.drawing_utils
        
        # Starting the timer to update the video frame
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(10)  # Update every 10 milliseconds


    
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

    
    def clear_canvas(self):
        self.drawing_canvas.trails = []  # Svuota la lista dei tratti
        self.drawing_canvas.current_trail = []  # Svuota anche il tratto corrente
        self.drawing_canvas.update()  # Aggiorna la visualizzazione


    def update_frame(self):
        if self.video_capture is not None:
            # Read a frame from the webcam
            ret, frame = self.video_capture.read()
            if ret:
                # Flip the frame horizontally (mirror effect)
                frame = cv2.flip(frame, 1)
                
                # Process the frame with MediaPipe Hands
                result = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                
                # Draw landmarks on the frame if hands are detected
                if result.multi_hand_landmarks:
                    for hand_landmark in result.multi_hand_landmarks:
                        # Compute the distance between the tip of the thumb and index
                        thumb_tip = hand_landmark.landmark[4]
                        index_tip = hand_landmark.landmark[8]
                        distance = math.sqrt((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2) * frame.shape[1] / 2
                        
                        # Draw detection with blue color if distance is greater than the maximum writing value
                        if distance < self.max_writing_distance:
                            self.mp_drawing_utils.draw_landmarks(frame, hand_landmark, self.mp_hands.HAND_CONNECTIONS, landmark_drawing_spec=self.mp_drawing_utils.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=4))
                        else:
                            self.mp_drawing_utils.draw_landmarks(frame, hand_landmark, self.mp_hands.HAND_CONNECTIONS, landmark_drawing_spec=self.mp_drawing_utils.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=4)) 
                        
                        # Compute the average position between the tip of the thumb and index
                        cx = int((thumb_tip.x + index_tip.x) * frame.shape[1] / 2)
                        cy = int((thumb_tip.y + index_tip.y) * frame.shape[0] / 2)
                        
                        # Convert coordinates to be on the right side of the application
                        canvas_height = self.drawing_canvas.height()
                        canvas_width = self.drawing_canvas.width()
                        cx_canvas = int(cx * canvas_width / frame.shape[1])
                        cy_canvas = int(cy * canvas_height / frame.shape[0])

                        # Aggiorna il puntatore con la posizione media
                        self.pointer_position_changed.emit(QPoint(cx_canvas, cy_canvas))
                        
                        # Aggiunge il punto al canvas di disegno se la distanza è inferiore al valore massimo di scrittura
                        if distance < self.max_writing_distance:
                            if not self.new_line:
                                self.drawing_canvas.add_point(QPoint(cx_canvas, cy_canvas))
                            else:
                                self.drawing_canvas.start_new_line(QPoint(cx_canvas, cy_canvas))
                                self.new_line = False  # Imposta il flag su False per continuare il tratto esistente
                        else:
                            self.new_line = True  # Imposta il flag su True per iniziare un nuovo tratto

                # Convert the frame to QImage format
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