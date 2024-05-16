import sys
import cv2
import mediapipe as mp
import math
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QFont, QImage, QPixmap, QPainter, QPen, QColor, QBrush
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QPushButton, QGridLayout, QDialog, QComboBox, QFrame, QMessageBox

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
    

class PointWithThickness:
    def __init__(self, point, thickness, color):
        self.point = point
        self.thickness = thickness
        self.color = color


class DrawingCanvas(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.trails = []  # List of trails, each represented by a list of points
        self.current_trail = []  # Current trail, started but not yet completed
        self.pointer_position = QPoint(0, 0)
        self.pointer_color = Qt.blue
        self.trail_thickness = 5  # Initial thickness of the trail
        
        # Set the main window reference
        self.main_window = main_window

        # Connection
        if self.main_window:
            self.main_window.pointer_position_changed.connect(self.update_pointer_position)
            self.main_window.pointer_color_and_thickness_changed.connect(self.update_pointer_color_and_thickness)
        else:
            print("Error: MainWindow reference not provided.")
        
        # Ensure that the pointer widget stays on top
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(210, 210, 210))  # Set the white background
        
        # Draw trails with variable thicknesses
        for trail in self.trails:
            for i in range(1, len(trail)):
                pen = QPen(trail[i].color)  # Use the color of the current trail
                pen.setWidth(int(trail[i].thickness))  # Set the thickness of the trail
                painter.setPen(pen)
                # Extract points and pass them to the drawLine method
                p1 = trail[i - 1].point
                p2 = trail[i].point
                painter.drawLine(p1, p2)

        # Draw the current trail
        for i in range(1, len(self.current_trail)):
            pen = QPen(self.current_trail[i].color)  # Use the color of the current trail
            pen.setWidth(int(self.current_trail[i].thickness))  # Set the thickness of the trail
            painter.setPen(pen)
            # Extract points and pass them to the drawLine method
            p1 = self.current_trail[i - 1].point
            p2 = self.current_trail[i].point
            painter.drawLine(p1, p2)

        # Draw the pointer
        pointer_size = math.sqrt(self.trail_thickness)  # Pointer size
        pen = QPen(self.pointer_color)  # Set the outline color of the pointer
        if self.trail_thickness > 2:
            self.trail_thickness -= 2
        pen.setWidth(self.trail_thickness)  # Set the outline width
        brush = QBrush(self.pointer_color)  # Set the fill color of the pointer
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawEllipse(self.pointer_position, pointer_size, pointer_size)

    def draw_trail(self, painter, trail):
        for i in range(1, len(trail)):
            pen = QPen(trail[i].color)
            pen.setWidth(trail[i].thickness)
            painter.setPen(pen)
            painter.drawLine(trail[i - 1].point, trail[i].point)

    def add_point(self, point, thickness, color):
        # Add the point to the current trail with the specified thickness and color
        self.current_trail.append(PointWithThickness(point, thickness, color))
        self.update()

    def start_new_line(self, point, thickness, color):
        # Create a new trail with the provided point, thickness, and color
        self.current_trail = [PointWithThickness(point, thickness, color)]
        self.update()

    def close_line(self):
        if len(self.current_trail) >= 2:
            self.trails.append(self.current_trail)
        self.current_trail = []  # Clear the current trail

    def update_pointer_position(self, position):
        self.pointer_position = position
        self.update()

    def update_pointer_color_and_thickness(self, color, thickness):
        self.pointer_color = color
        self.trail_thickness = thickness  # Use the trail thickness as the outline width
        self.update()


class MainWindow(QMainWindow):

    pointer_position_changed = pyqtSignal(QPoint)
    pointer_color_and_thickness_changed = pyqtSignal(QColor, int)

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
        self.select_camera_button.setStyleSheet("QPushButton { text-transform: uppercase; background-color: black; color: white}")
        font = QFont("Arial", 14, QFont.Bold)
        self.select_camera_button.setFont(font)
        self.select_camera_button.clicked.connect(self.select_camera)
        layout.addWidget(self.select_camera_button, 0, 0, 1, 1, Qt.AlignTop | Qt.AlignLeft)

        #Info button
        self.info_button = QPushButton("Info")
        self.info_button.setFont(font)
        self.info_button.setStyleSheet("QPushButton { text-transform: uppercase; background-color: black; color: white; }")
        self.info_button.clicked.connect(self.show_info)
        layout.addWidget(self.info_button, 0, 0, 1, 1, Qt.AlignTop | Qt.AlignRight)
        
        # Drawing canvas
        self.drawing_canvas = DrawingCanvas(main_window=self)
        layout.addWidget(self.drawing_canvas, 0, 1, 1, 1)

        self.distance_costant = 70
        self.new_line = False

        self.punch_treshold = 20

        self.max_hand_distance = 160  # Maximum distance of the hand from the camera
        self.min_hand_distance = 20  # Minimum distance of the hand from the camera
        self.max_stroke_thickness = 15  # Maximum stroke thickness
        self.min_stroke_thickness = 1  # Minimum stroke thickness
        
        # Button to exit the application
        self.exit_button = QPushButton("EXIT")
        self.exit_button.setFont(font)
        self.exit_button.setStyleSheet("QPushButton { text-transform: uppercase; }")
        self.exit_button.clicked.connect(self.close)
        layout.addWidget(self.exit_button, 1, 0, 1, 2)
        
        # Set column stretch to evenly distribute the width
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        # Add buttons
        self.buttonBLUE = QPushButton("BLUE")
        self.buttonBLUE.setStyleSheet("color: white; background-color: rgba(0, 0, 255, 160); height: 80px;") 
        self.buttonBLUE.setFont(QFont("Arial", 16, QFont.Bold))  
        self.buttonRED = QPushButton("RED")
        self.buttonRED.setStyleSheet("color: white; background-color: rgba(255, 0, 0, 160); height: 80px;")
        self.buttonRED.setFont(QFont("Arial", 16, QFont.Bold))  
        self.buttonGREEN = QPushButton("GREEN")
        self.buttonGREEN.setStyleSheet("color: white; background-color: rgba(0, 255, 0, 160); height: 80px;")
        self.buttonGREEN.setFont(QFont("Arial", 16, QFont.Bold))  

        self.buttonUNDO = QPushButton("UNDO")
        self.buttonUNDO.setStyleSheet("color: white; background-color: rgba(180, 180, 180, 160); height: 80px;")
        self.buttonUNDO.setFont(QFont("Arial", 16, QFont.Bold))  

        self.current_color = Qt.blue

        # Connect buttons to select stroke color
        self.buttonBLUE.clicked.connect(lambda: self.select_color(Qt.blue))
        self.buttonRED.clicked.connect(lambda: self.select_color(Qt.red))
        self.buttonGREEN.clicked.connect(lambda: self.select_color(Qt.green))

        self.buttonUNDO.clicked.connect(self.undo_last_stroke)

        self.undo_enabled = True  

        # Create a QFrame to contain the buttons
        button_frame = QFrame()
        button_frame.setFrameShape(QFrame.Panel)
        button_frame.setFrameShadow(QFrame.Raised)
        button_frame.setStyleSheet("background-color: rgba(255, 255, 255, 100); border-radius: 10px; border: 2px solid rgba(0, 0, 0, 0.5);")

        # Add a layout for the buttons inside the frame
        button_layout = QHBoxLayout(button_frame)
        button_layout.addWidget(self.buttonBLUE)
        button_layout.addWidget(self.buttonRED)
        button_layout.addWidget(self.buttonGREEN)
        button_layout.addWidget(self.buttonUNDO)

        # Add the frame to the main layout
        layout.addWidget(button_frame, 0, 1, 1, 1, Qt.AlignTop)

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

        self.hands_color = (255, 0, 0)
        
        # Starting the timer to update the video frame
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(10)  

    
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

    
    def show_info(self):
        info_text = (
            "This is the AIR WRITING application.\n"
            "To use the app, follow these instructions:\n"
            "1. Select a camera to start drawing using hand gestures.\n"
            "2. If you connect your index and thumb, you can draw.\n"
            "3. If you connect your index and thumb above any of the options, it is activated automatically.\n"
            "4. If you close your hand, you delete the draw."
        )
        QMessageBox.information(self, "Info", info_text)


    def clear_canvas(self):
        self.drawing_canvas.trails = []  # Clear the list of trails
        self.drawing_canvas.current_trail = []  # Also clear the current trail
        self.drawing_canvas.update()  # Update the display


    def undo_last_stroke(self):
        if self.undo_enabled:
            if self.drawing_canvas.trails:
                self.drawing_canvas.trails.pop()  # Remove the last stroke from the list of trails
            # Set a temporary style to make the undo button less transparent
            self.buttonUNDO.setStyleSheet("color: white; background-color: rgba(180, 180, 180, 255); height: 80px;")
            # Start a timer to restore the original style after a short delay
            QTimer.singleShot(150, lambda: self.buttonUNDO.setStyleSheet("color: white; background-color: rgba(180, 180, 180, 160); height: 80px;"))
            self.drawing_canvas.update()  # Update the display to remove the deleted stroke
            self.undo_enabled = False
            # Temporarily disable the button for 300ms
            QTimer.singleShot(300, self.enable_undo_button)


    def enable_undo_button(self):
        self.undo_enabled = True


    def select_color(self, color):
        self.current_color = color
        if color == (Qt.blue):
            self.hands_color = (255, 0, 0)
            # Set a temporary style to make the blue button less transparent
            self.buttonBLUE.setStyleSheet("color: white; background-color: rgba(0, 0, 255, 255); height: 80px;")
            # Start a timer to restore the original style after a short delay
            QTimer.singleShot(150, lambda: self.buttonBLUE.setStyleSheet("color: white; background-color: rgba(0, 0, 255, 160); height: 80px;"))
        elif color == (Qt.red):
            self.hands_color = (0, 0, 255)
            # Set a temporary style to make the red button less transparent
            self.buttonRED.setStyleSheet("color: white; background-color: rgba(255, 0, 0, 255); height: 80px;")
            # Start a timer to restore the original style after a short delay
            QTimer.singleShot(150, lambda: self.buttonRED.setStyleSheet("color: white; background-color: rgba(255, 0, 0, 160); height: 80px;"))
        elif color == (Qt.green):
            self.hands_color = (0, 255, 0)
            # Set a temporary style to make the green button less transparent
            self.buttonGREEN.setStyleSheet("color: white; background-color: rgba(0, 255, 0, 255); height: 80px;")
            # Start a timer to restore the original style after a short delay
            QTimer.singleShot(150, lambda: self.buttonGREEN.setStyleSheet("color: white; background-color: rgba(0, 255, 0, 160); height: 80px;"))


    def map_distance_to_thickness(self, distance):
        # Map the hand distance to the stroke thickness
        
        # Ensure that normalized_distance is between 0 and 1
        normalized_distance = max(0, min(1, distance))

        # Linearly map the normalized distance to a stroke thickness
        thickness_range = self.max_stroke_thickness - self.min_stroke_thickness
        thickness = self.min_stroke_thickness + normalized_distance * thickness_range

        return thickness


    def update_frame(self):
        stroke_thickness = 2  # Default value for stroke thickness
        if self.video_capture is not None:
            # Read a frame from the webcam
            ret, frame = self.video_capture.read()
            if ret:
                # Flip the frame horizontally (mirror effect)
                frame = cv2.flip(frame, 1)
                
                # Process the frame with MediaPipe Hands
                result = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                
                # Calculate hand distance
                hand_distance = None
                    
                # Draw landmarks on the frame if hands are detected
                if result.multi_hand_landmarks:
                    for hand_landmark in result.multi_hand_landmarks:

                        # Compute the distance between the four knuckles
                        knuckle_distances = []
                        for i in range(0, 20, 4):  # Iterate over knuckle points
                            knuckle1 = hand_landmark.landmark[i]
                            knuckle2 = hand_landmark.landmark[i+1]
                            distance = math.sqrt((knuckle1.x - knuckle2.x) ** 2 + (knuckle1.y - knuckle2.y) ** 2) * frame.shape[1] / 2
                            knuckle_distances.append(distance)
                        
                        # Average the distances between the knuckles
                        avg_distance = sum(knuckle_distances) / len(knuckle_distances)
                        
                        # Convert average knuckle distance to distance from camera (approximation)
                        hand_distance = (avg_distance - self.min_hand_distance) / (self.max_hand_distance - self.min_hand_distance)

                        if hand_distance is not None:
                            # Convert hand distance to stroke thickness
                            stroke_thickness = self.map_distance_to_thickness(hand_distance)

                        # Compute the distance between the tip of the thumb and index
                        thumb_tip = hand_landmark.landmark[4]
                        index_tip = hand_landmark.landmark[8]
                        distance = math.sqrt((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2) * frame.shape[1] / 2

                        # Set the maximum writing distance based on the hand distance from the screen
                        max_writing_distance = (hand_distance) * self.distance_costant
                        
                        # Draw detection with blue color if distance is greater than the maximum writing value
                        if distance < max_writing_distance:
                            self.mp_drawing_utils.draw_landmarks(frame, hand_landmark, self.mp_hands.HAND_CONNECTIONS, landmark_drawing_spec=self.mp_drawing_utils.DrawingSpec(color= self.hands_color, thickness=int(stroke_thickness), circle_radius=4))
                        else:
                            self.mp_drawing_utils.draw_landmarks(frame, hand_landmark, self.mp_hands.HAND_CONNECTIONS, landmark_drawing_spec=self.mp_drawing_utils.DrawingSpec(color=(255, 255, 255), thickness=int(stroke_thickness), circle_radius=4)) 
                        
                        # Compute the average position between the tip of the thumb and index
                        cx = int((thumb_tip.x + index_tip.x) * frame.shape[1] / 2)
                        cy = int((thumb_tip.y + index_tip.y) * frame.shape[0] / 2)
                        
                        # Convert coordinates to be on the right side of the application
                        canvas_height = self.drawing_canvas.height()
                        canvas_width = self.drawing_canvas.width()
                        cx_canvas = int(cx * canvas_width / frame.shape[1])
                        cy_canvas = int(cy * canvas_height / frame.shape[0])

                        if cy_canvas > 120:
                            # Add the point to the drawing canvas with the calculated thickness and color
                            if distance < max_writing_distance:
                                if not self.new_line:
                                    self.drawing_canvas.add_point(QPoint(cx_canvas, cy_canvas), stroke_thickness, self.current_color)
                                else:
                                    self.drawing_canvas.start_new_line(QPoint(cx_canvas, cy_canvas), stroke_thickness, self.current_color)
                                    self.new_line = False  # Set the flag to False to continue the existing stroke
                            else:
                                if not self.new_line:
                                    self.drawing_canvas.close_line()
                                self.new_line = True  # Set the flag to True to start a new stroke
                        elif cy_canvas < 100:
                            if not self.new_line:
                                self.drawing_canvas.close_line()
                            self.new_line = True  # Set the flag to True to start a new stroke

                            if distance < max_writing_distance: 
                                if 20 < cx_canvas < 170:
                                    self.select_color(Qt.blue)
                                elif 190 < cx_canvas < 340:
                                    self.select_color(Qt.red)
                                elif 360 < cx_canvas < 510:
                                    self.select_color(Qt.green)
                                elif 530 < cx_canvas < 680:
                                    self.undo_last_stroke()


                        # Update the pointer with the average position and color
                        self.pointer_position_changed.emit(QPoint(cx_canvas, cy_canvas))
                        self.pointer_color_and_thickness_changed.emit(QColor(self.current_color), int(stroke_thickness))

            
                        # Compute the distance between the knuckles and the point between the middle and proximal phalanx of each finger
                        knuckle_to_finger_point_distances = []
                        for i in range(5, 18, 4):  # Knuckle points and points between middle and proximal phalanx of each finger
                            knuckle = hand_landmark.landmark[i]
                            middle_to_proximal = hand_landmark.landmark[i+2]
                            distance = math.sqrt((knuckle.x - middle_to_proximal.x) ** 2 + (knuckle.y - middle_to_proximal.y) ** 2) * frame.shape[1] / 2
                            knuckle_to_finger_point_distances.append(distance)
                        
                        # Compute the average distance between the knuckle distances and the point between the middle and proximal phalanx of each finger
                        avg_distance = sum(knuckle_to_finger_point_distances) / len(knuckle_to_finger_point_distances)
                        
                        # If the average distance is below a certain threshold, consider the hand as a closed fist
                        if avg_distance < self.punch_treshold:
                            self.clear_canvas()  # Call the clear_canvas() function

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
    
    # Call show_info after showing the main window
    window.show_info()
    
    sys.exit(app.exec_())
    