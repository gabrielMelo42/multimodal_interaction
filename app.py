import sys
import cv2
import mediapipe as mp
import math
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QFont, QImage, QPixmap, QPainter, QPen, QColor, QBrush
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QPushButton, QGridLayout, QDialog, QComboBox

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
        self.trails = []  # Lista di tratti, ognuno rappresentato da una lista di punti
        self.current_trail = []  # Tratto corrente, iniziato ma non ancora completato
        self.pointer_position = QPoint(0, 0)
        self.pointer_color = Qt.blue
        self.trail_thickness = 5  # Spessore iniziale del tratto
        
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
        painter.fillRect(self.rect(), Qt.white)  # Set the white background
        
        # Disegna i tratti con spessori variabili
        for trail in self.trails:
            for i in range(1, len(trail)):
                pen = QPen(trail[i].color)  # Utilizza il colore del tratto corrente
                pen.setWidth(int(trail[i].thickness))  # Imposta lo spessore del tratto
                painter.setPen(pen)
                # Estrai i punti e passali al metodo drawLine
                p1 = trail[i - 1].point
                p2 = trail[i].point
                painter.drawLine(p1, p2)

        # Disegna il tratto corrente
        for i in range(1, len(self.current_trail)):
            pen = QPen(self.current_trail[i].color)  # Utilizza il colore del tratto corrente
            pen.setWidth(int(self.current_trail[i].thickness))  # Imposta lo spessore del tratto
            painter.setPen(pen)
            # Estrai i punti e passali al metodo drawLine
            p1 = self.current_trail[i - 1].point
            p2 = self.current_trail[i].point
            painter.drawLine(p1, p2)

        # Disegna il puntatore
        pointer_size = math.sqrt(self.trail_thickness)  # Dimensione del puntatore
        pen = QPen(self.pointer_color)  # Imposta il colore del contorno del puntatore
        if self.trail_thickness > 2:
            self.trail_thickness -= 2
        pen.setWidth(self.trail_thickness)  # Imposta la larghezza del contorno
        brush = QBrush(self.pointer_color)  # Imposta il colore di riempimento del puntatore
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
        # Aggiungi il punto al tratto corrente con lo spessore e colore specificati
        self.current_trail.append(PointWithThickness(point, thickness, color))
        self.update()

    def start_new_line(self, point, thickness, color):
        # Crea un nuovo tratto con il punto fornito, lo spessore e il colore specificati
        self.current_trail = [PointWithThickness(point, thickness, color)]
        self.update()

    def close_line(self):
        if len(self.current_trail) >= 2:
            self.trails.append(self.current_trail)
        self.current_trail = []  # Svuota il tratto corrente

    def update_pointer_position(self, position):
        self.pointer_position = position
        self.update()

    def update_pointer_color_and_thickness(self, color, thickness):
        self.pointer_color = color
        self.trail_thickness = thickness  # Utilizza lo spessore del tratto come larghezza del contorno
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

        
        # Drawing canvas
        self.drawing_canvas = DrawingCanvas(main_window=self)
        layout.addWidget(self.drawing_canvas, 0, 1, 1, 1)

        self.max_writing_distance = 30  # Set the maximum distance value for writing
        self.new_line = False

        self.punch_treshold = 20

        self.max_hand_distance = 160  # Massima distanza della mano dalla fotocamera
        self.min_hand_distance = 20  # Minima distanza della mano dalla fotocamera
        self.max_stroke_thickness = 15  # Massimo spessore del tratto
        self.min_stroke_thickness = 1  # Minimo spessore del tratto
        
        # Button to exit the application
        self.exit_button = QPushButton("EXIT")
        self.exit_button.setFont(font)
        self.exit_button.setStyleSheet("QPushButton { text-transform: uppercase; }")
        self.exit_button.clicked.connect(self.close)
        layout.addWidget(self.exit_button, 1, 0, 1, 2)
        
        # Set column stretch to evenly distribute the width
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        # Aggiungi i pulsanti
        self.buttonBLUE = QPushButton("BLUE")
        self.buttonBLUE.setStyleSheet("color: white; background-color: rgba(0, 0, 255, 150); height: 80px;") 
        self.buttonBLUE.setFont(QFont("Arial", 16, QFont.Bold))  # Imposta il font e il grassetto
        self.buttonRED = QPushButton("RED")
        self.buttonRED.setStyleSheet("color: white; background-color: rgba(255, 0, 0, 150); height: 80px;")
        self.buttonRED.setFont(QFont("Arial", 16, QFont.Bold))  # Imposta il font e il grassetto
        self.buttonGREEN = QPushButton("GREEN")
        self.buttonGREEN.setStyleSheet("color: white; background-color: rgba(0, 255, 0, 150); height: 80px;")
        self.buttonGREEN.setFont(QFont("Arial", 16, QFont.Bold))  # Imposta il font e il grassetto
        self.buttonUNDO = QPushButton("UNDO")
        self.buttonUNDO.setStyleSheet("color: white; background-color: rgba(211, 211, 211, 150); height: 80px;")
        self.buttonUNDO.setFont(QFont("Arial", 16, QFont.Bold))  # Imposta il font e il grassetto

        # Aggiungi un widget vuoto per posizionare i pulsanti sopra il canvas
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)

        # Aggiungi i pulsanti al layout orizzontale
        button_layout.addWidget(self.buttonBLUE)
        button_layout.addWidget(self.buttonRED)
        button_layout.addWidget(self.buttonGREEN)
        button_layout.addWidget(self.buttonUNDO)

        self.current_color = Qt.blue

        # Connessioni dei pulsanti per selezionare il colore del tratto
        self.buttonBLUE.clicked.connect(lambda: self.select_color(Qt.blue))
        self.buttonRED.clicked.connect(lambda: self.select_color(Qt.red))
        self.buttonGREEN.clicked.connect(lambda: self.select_color(Qt.green))

        self.buttonUNDO.clicked.connect(self.undo_last_stroke)

        # Imposta la posizione del widget dei pulsanti sopra il canvas
        layout.addWidget(button_widget, 0, 1, 1, 1, Qt.AlignTop)

        
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


    def undo_last_stroke(self):
        if self.drawing_canvas.trails:
            self.drawing_canvas.trails.pop()  # Rimuove l'ultimo tratto dalla lista dei tratti
            self.drawing_canvas.update()  # Aggiorna la visualizzazione per rimuovere il tratto cancellato


    def select_color(self, color):
        self.current_color = color
        if color == (Qt.blue):
            self.hands_color = (255, 0, 0)
        elif color == (Qt.red):
            self.hands_color = (0, 0, 255)
        elif color == (Qt.green):
            self.hands_color = (0, 255, 0)
    

    def map_distance_to_thickness(self, distance):
        # Mappare la distanza della mano alla dimensione dello spessore del tratto
        
        # Assicurati che normalized_distance sia compreso tra 0 e 1
        normalized_distance = max(0, min(1, distance))

        # Mappa linearmente la distanza normalizzata a uno spessore del tratto
        thickness_range = self.max_stroke_thickness - self.min_stroke_thickness
        thickness = self.min_stroke_thickness + normalized_distance * thickness_range

        return thickness



    def update_frame(self):
        stroke_thickness = 2  # Valore predefinito per lo spessore del tratto
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
                        
                        # Draw detection with blue color if distance is greater than the maximum writing value
                        if distance < self.max_writing_distance:
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


                        # Aggiungi il punto al canvas di disegno con lo spessore e colore calcolati
                        if distance < self.max_writing_distance:
                            if not self.new_line:
                                self.drawing_canvas.add_point(QPoint(cx_canvas, cy_canvas), stroke_thickness, self.current_color)
                            else:
                                self.drawing_canvas.start_new_line(QPoint(cx_canvas, cy_canvas), stroke_thickness, self.current_color)
                                self.new_line = False  # Imposta il flag su False per continuare il tratto esistente
                        else:
                            if not self.new_line:
                                self.drawing_canvas.close_line()
                            self.new_line = True  # Imposta il flag su True per iniziare un nuovo tratto


                        # Aggiorna il puntatore con la posizione media e colore
                        self.pointer_position_changed.emit(QPoint(cx_canvas, cy_canvas))
                        self.pointer_color_and_thickness_changed.emit(QColor(self.current_color), int(stroke_thickness))

            
                        # Calcola la distanza tra le nocche e il punto tra la falange intermedia e prossimale di ogni dito
                        knuckle_to_finger_point_distances = []
                        for i in range(5, 18, 4):  # Punti delle nocche e dei punti tra la falange intermedia e prossimale di ogni dito
                            knuckle = hand_landmark.landmark[i]
                            middle_to_proximal = hand_landmark.landmark[i+2]
                            distance = math.sqrt((knuckle.x - middle_to_proximal.x) ** 2 + (knuckle.y - middle_to_proximal.y) ** 2) * frame.shape[1] / 2
                            knuckle_to_finger_point_distances.append(distance)
                        
                        # Calcola la distanza media tra le distanze delle nocche e il punto tra la falange intermedia e prossimale di ogni dito
                        avg_distance = sum(knuckle_to_finger_point_distances) / len(knuckle_to_finger_point_distances)
                        
                        # Se la distanza media è inferiore a una certa soglia, considera la mano chiusa a pugno
                        if avg_distance < self.punch_treshold:
                            self.clear_canvas()  # Chiama la funzione clear_canvas()

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