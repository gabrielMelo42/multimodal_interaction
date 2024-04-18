import cv2

# Informar al usuario y obtener consentimiento
print("Welcome to the air drawing app. This app uses the camera to detect motion and allow you to draw on the screen.")
consentimiento = input("Do you agree to allow access to the camera? (y/n): ")

if consentimiento.lower() != 'y':
    print("Permission denied. The app cannot access the camera.")
    exit()

# Acceder a la cámara y mostrar el video en tiempo real
cap = cv2.VideoCapture(0)  # Acceder a la primera cámara disponible

while True:
    ret, frame = cap.read()
    if not ret:
        break # Exit loop if video capture failed

    # Mostrar el fotograma capturado en una ventana
    cv2.imshow('Camera', frame)

    key = cv2.waitKey(1)
    if key == 27:  # Presionar 'ESC' para salir
        break

# Liberar la cámara y cerrar las ventanas
cap.release()
cv2.destroyAllWindows()
