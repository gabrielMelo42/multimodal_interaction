import cv2
import mediapipe as mp

# Inform the user and obtain consent
print("Welcome to the air drawing app. This app uses the camera to detect motion and allows you to draw on the screen.")
consent = input("Do you agree to allow access to the camera? (y/n): ")

if consent.lower() != 'y':
    print("Permission denied. The app cannot access the camera.")
    exit()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing_utils = mp.solutions.drawing_utils

# Access the camera and display the video in real-time
cap = cv2.VideoCapture(2)  # Access the first available camera

while True:
    ret, frame = cap.read()
    if not ret:
        break  # Exit loop if video capture failed

    # Flip the frame horizontally (mirror effect)
    frame = cv2.flip(frame, 1)

    result = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    print(result.multi_hand_landmarks)

    if result.multi_hand_landmarks:
        for hand_landmark in result.multi_hand_landmarks:
            mp_drawing_utils.draw_landmarks(frame, hand_landmark, mp_hands.HAND_CONNECTIONS)
    # Show the captured frame in a window
    cv2.imshow('Camera', frame)

    key = cv2.waitKey(1)
    if key == 27:  # Press 'ESC' to exit
        break

# Release the camera and close the windows
cap.release()
cv2.destroyAllWindows()
