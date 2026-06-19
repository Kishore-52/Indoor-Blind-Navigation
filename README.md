Intelligent Belt for Visually Impaired People

An AI-powered wearable assistive system designed to help visually impaired people navigate indoor environments safely. The system uses computer vision, ultrasonic sensors, an IMU sensor, voice guidance, buzzer alerts, and low-light illumination to identify obstacles and guide the user in real time.

Project Overview

GPS-based navigation is often unreliable inside buildings. This project provides an affordable indoor navigation solution for visually impaired people using a Raspberry Pi-based intelligent belt.

The webcam captures the surroundings, while a custom-trained YOLO model detects indoor objects and obstacles. Ultrasonic sensors measure the distance to nearby obstacles, and the system provides voice instructions such as moving left, moving right, or stopping.

An IMU sensor detects whether the user turns in the wrong direction. An LED light automatically improves camera visibility in low-light environments.

Key Features
Real-time indoor object and obstacle detection
Distance measurement using ultrasonic sensors
Voice-based navigation guidance
Left, right, and front obstacle identification
Wrong-turn detection using an IMU sensor
Buzzer warning for dangerous or incorrect movement
Automatic LED activation in low-light conditions
Custom-trained YOLO object-detection model
Raspberry Pi-based portable implementation
Wearable belt design
How the System Works
The webcam continuously captures the surroundings.
The YOLO model detects indoor objects and obstacles.
Ultrasonic sensors measure the distance to obstacles.
The system identifies whether the obstacle is on the left, right, or front.
Voice instructions guide the user towards a safer direction.
The IMU sensor checks whether the user follows the suggested direction.
If the user turns incorrectly, the buzzer produces a warning sound.
The LED turns on when the camera does not receive enough light.
System Architecture
                         Webcam
                            |
                            v
                   YOLO Object Detection
                            |
                            v
Ultrasonic Sensors --> Raspberry Pi 4 <-- IMU Sensor
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
        Voice Guidance    Buzzer       LED Light
Hardware Requirements
Component	Purpose
Raspberry Pi 4	Main processing unit
USB Webcam	Captures the indoor environment
Ultrasonic Sensors	Measure obstacle distance
IMU Sensor	Detects user movement and wrong turns
Buzzer	Provides warning alerts
LED Light	Improves camera visibility in darkness
Speaker or Earphones	Provides voice instructions
Mini Breadboard	Used for circuit connections
Jumper Wires	Connects the hardware components
Power Bank	Provides portable power
Belt	Holds the complete system
Software Requirements
Raspberry Pi OS
Python 3
OpenCV
Ultralytics YOLO
NumPy
RPi.GPIO or GPIO Zero
Text-to-Speech library
IMU sensor library
Technologies Used
Python — Main programming language
YOLO — Real-time object detection
OpenCV — Camera capture and image processing
Raspberry Pi GPIO — Hardware control
Ultrasonic Sensors — Distance measurement
IMU Sensor — Movement and direction detection
Text-to-Speech — Audio navigation guidance
Project Structure
indoor-blind-navigation/
│
├── main.py
├── object_detection.py
├── ultrasonic_sensor.py
├── imu_direction.py
├── audio_guidance.py
├── buzzer_control.py
├── led_control.py
│
├── models/
│   └── best.pt
│
├── audio/
│   ├── move_left.mp3
│   ├── move_right.mp3
│   ├── obstacle_ahead.mp3
│   └── wrong_direction.mp3
│
├── images/
│   ├── prototype.jpg
│   └── system_architecture.png
│
├── requirements.txt
├── LICENSE
└── README.md
Installation
1. Clone the repository
git clone https://github.com/your-username/indoor-blind-navigation.git
cd indoor-blind-navigation

Replace your-username with your GitHub username.

2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate
3. Install the required libraries
pip install -r requirements.txt

You can also install the main libraries manually:

pip install ultralytics opencv-python numpy pyttsx3 gpiozero
4. Add the trained model

Place the trained YOLO model in the following location:

models/best.pt
5. Connect the hardware

Connect the webcam, ultrasonic sensors, IMU sensor, buzzer, LED, and speaker according to the GPIO configuration used in the source code.

6. Run the project
python3 main.py
Example Voice Alerts
Person detected ahead.
Obstacle detected on the left.
Move slightly to the right.
Chair detected two metres ahead.
Wrong direction detected.
Please turn right.
Low light detected. LED activated.
Object-Detection Classes

The custom-trained model can include indoor object classes such as:

person
chair
table
door
staircase
wall
bed
sofa
pillar
obstacle

The model should be trained using images from different:

Indoor locations
Camera angles
Lighting conditions
Object distances
Backgrounds
Building layouts
Safety Logic
If an obstacle is detected within the safety distance:
    Identify its position
    Provide a voice instruction
    Activate the buzzer when required

If the user turns opposite to the instructed direction:
    Detect the movement using the IMU sensor
    Activate the warning buzzer
    Repeat the correct direction

If the environment is dark:
    Turn on the LED
    Improve the webcam visibility
Applications
Colleges and universities
Hospitals
Shopping malls
Railway stations
Airports
Offices
Public buildings
Homes
Care centres
Current Limitations
Detection accuracy depends on the quality of the trained dataset.
Camera performance may reduce in poor lighting.
Ultrasonic sensors may not correctly detect soft or angled surfaces.
Complex environments may generate multiple alerts simultaneously.
The system currently does not provide complete indoor map-based navigation.
The prototype requires further real-world testing and calibration.
Future Enhancements
Emergency SOS alerts to relatives or caregivers
Custom PCB for a compact wearable design
Indoor mapping and route planning
Smartphone application integration
Bluetooth earphone support
Multi-language voice guidance
Battery-level monitoring
Location sharing with caregivers
Improved staircase and doorway detection
Edge AI optimization for faster performance
Outdoor GPS navigation support
Contributors
Kishore J
Rubhavarshini B
Omana S
Sanmathi P

