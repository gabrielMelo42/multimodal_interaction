# AIR WRITING

## Description
The AIR WRITING application allows users to draw on the screen using hand gestures captured by a webcam. The application utilizes computer vision techniques to detect hand movements and translate them into strokes on a drawing canvas. Users can select different colors for drawing and erase strokes by making specific hand gestures.

## Features
- **Drawing with Hand Gestures:** Users can draw on the screen by moving their hands in the air.
- **Multiple Color Selection:** Users can choose from different colors (blue, red, green) for drawing strokes.
- **Undo Functionality:** Users can undo the last drawn stroke by making a specific hand gesture.
- **Clear Canvas:** Users can clear the entire drawing canvas by making a specific hand gesture.

## Usage
1. **Select Camera:** Start the application and select a camera from the available options to begin drawing.
2. **Draw with Hand Gestures:** Move your hand in the air to draw strokes on the screen. Connect your index and thumb to start drawing.
3. **Color Selection:** Place your index and thumb above the color options to change the drawing color (blue, red, green).
4. **Undo:** Make a fist gesture to undo the last drawn stroke.
5. **Clear Canvas:** Make a fist gesture and close your hand completely to clear the entire drawing canvas.

## Requirements
- Python 3.x
- OpenCV (`opencv-python`)
- Mediapipe (`mediapipe`)
- PyQt5 (`pyqt5`)

## Installation
1. Install Python 3.x on your system.
2. Clone or download the project files from the repository.
3. Navigate to the project directory in the terminal.
4. Create a virtual environment (optional but recommended).
5. Install the required dependencies by running:

pip install -r requirements.txt


## Running the Application
1. After installing the dependencies, execute the following command:

python app.py

2. Select a camera from the available options to start drawing.
3. Follow the instructions displayed in the application for drawing, color selection, undoing, and clearing the canvas.






