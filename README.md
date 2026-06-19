# 🦯 Intelligent Belt for Visually Impaired People

An **AI-powered wearable assistive system** designed to help visually impaired people navigate indoor environments safely. The system uses computer vision, ultrasonic sensors, an IMU sensor, voice guidance, buzzer alerts, and low-light illumination to identify obstacles and guide the user in real time.

---

## 📌 Project Overview

GPS-based navigation is often unreliable inside buildings. This project provides an affordable indoor navigation solution for visually impaired people using a Raspberry Pi-based intelligent belt.

The webcam continuously captures the surrounding environment, while a custom-trained **Edge Impulse object-detection model** identifies important indoor objects and obstacles. The model achieved an accuracy of **93.8%** and can detect four object classes:

* Person
* Table
* Chair
* Door

Ultrasonic sensors measure the distance to nearby obstacles, and the system provides voice instructions such as moving left, moving right, or stopping.

An IMU sensor detects whether the user turns in the wrong direction. An LED light automatically improves webcam visibility in low-light environments.

---

## ✨ Key Features

* Real-time indoor object and obstacle detection
* Edge Impulse-based object-detection model
* Model accuracy of **93.8%**
* Detection of people, tables, chairs, and doors
* Distance measurement using ultrasonic sensors
* Voice-based navigation guidance
* Left, right, and front obstacle identification
* Wrong-turn detection using an IMU sensor
* Buzzer warning for dangerous or incorrect movement
* Automatic LED activation in low-light conditions
* Raspberry Pi-based portable implementation
* Wearable belt design

---

## ⚙️ How the System Works

1. The webcam continuously captures the surrounding environment.
2. The Edge Impulse model processes the camera frames.
3. The model detects people, tables, chairs, and doors.
4. Ultrasonic sensors measure the distance to nearby obstacles.
5. The system identifies whether an obstacle is on the left, right, or front.
6. Voice instructions guide the user towards a safer direction.
7. The IMU sensor checks whether the user follows the suggested direction.
8. If the user turns incorrectly, the buzzer produces a warning sound.
9. The LED turns on when the webcam does not receive enough light.

---

## 🏗️ System Architecture

```text
                         Webcam
                            |
                            v
              Edge Impulse Object Detection
                            |
                            v
Ultrasonic Sensors --> Raspberry Pi 4 <-- IMU Sensor
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
        Voice Guidance    Buzzer       LED Light
```

---

## 🔩 Hardware Requirements

| Component            | Purpose                                |
| -------------------- | -------------------------------------- |
| Raspberry Pi 4       | Main processing unit                   |
| USB Webcam           | Captures the indoor environment        |
| Ultrasonic Sensors   | Measure obstacle distance              |
| IMU Sensor           | Detects user movement and wrong turns  |
| Buzzer               | Provides warning alerts                |
| LED Light            | Improves webcam visibility in darkness |
| Speaker or Earphones | Provides voice instructions            |
| Mini Breadboard      | Used for circuit connections           |
| Jumper Wires         | Connect the hardware components        |
| Power Bank           | Provides portable power                |
| Belt                 | Holds the complete system              |

---

## 💻 Software Requirements

* Raspberry Pi OS
* Python 3
* Edge Impulse
* OpenCV
* NumPy
* RPi.GPIO or GPIO Zero
* Text-to-Speech library
* IMU sensor library

---

## 🛠️ Technologies Used

* **Python** — Main programming language
* **Edge Impulse** — Model training and object detection
* **OpenCV** — Webcam capture and image processing
* **Raspberry Pi 4** — Main edge-computing device
* **Raspberry Pi GPIO** — Sensor and actuator control
* **Ultrasonic Sensors** — Obstacle-distance measurement
* **IMU Sensor** — Movement and direction detection
* **Text-to-Speech** — Audio navigation guidance

---

## 📊 Edge Impulse Model Details

| Model Information | Details                  |
| ----------------- | ------------------------ |
| Platform          | Edge Impulse             |
| Model Type        | Object Detection         |
| Achieved Accuracy | **93.8%**                |
| Number of Classes | 4                        |
| Deployment Device | Raspberry Pi 4           |
| Input Source      | USB Webcam               |
| Processing Type   | Real-time edge inference |

### Model Classes

```text
person
table
chair
door
```

The model was trained using images captured from different:

* Indoor locations
* Camera angles
* Lighting conditions
* Object distances
* Backgrounds
* Object positions

A varied dataset helps the model identify objects more reliably in different indoor environments.

---

## 📁 Project Structure

```text
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
├── edge_impulse_model/
│   └── model.eim
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
```

> Update the model filename and folder structure according to the actual Edge Impulse model exported for the Raspberry Pi.

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/indoor-blind-navigation.git
cd indoor-blind-navigation
```

Replace `your-username` with your GitHub username.

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the required libraries

```bash
pip install -r requirements.txt
```

The main Python libraries can also be installed manually:

```bash
pip install opencv-python numpy pyttsx3 gpiozero
```

Install the required Edge Impulse runtime or SDK according to the deployment package exported from the Edge Impulse platform.

### 4. Add the Edge Impulse Model

Export the trained model from Edge Impulse for Linux or Raspberry Pi deployment.

Place the exported model in the following location:

```text
edge_impulse_model/model.eim
```

Update the model path in the Python program when a different filename or location is used.

### 5. Connect the Hardware

Connect the webcam, ultrasonic sensors, IMU sensor, buzzer, LED, and speaker according to the GPIO configuration used in the source code.

### 6. Run the Project

```bash
python3 main.py
```

---

## 🔊 Example Voice Alerts

```text
Person detected ahead.
Chair detected on the left.
Table detected ahead.
Door detected on the right.
Obstacle detected nearby.
Move slightly to the left.
Please turn right.
Wrong direction detected.
Low light detected. LED activated.
```

---

## 🧠 Detection and Navigation Logic

```text
Capture a frame using the webcam.

Run the Edge Impulse object-detection model.

If a person, table, chair, or door is detected:
    Identify the detected object's position.
    Estimate whether it is on the left, centre, or right.
    Check the ultrasonic sensor distance.
    Provide the appropriate voice guidance.

If an obstacle is within the safety distance:
    Warn the user through voice guidance.
    Activate the buzzer when required.
    Suggest a safer movement direction.

If the user turns opposite to the instructed direction:
    Detect the movement using the IMU sensor.
    Activate the warning buzzer.
    Repeat the correct direction.

If the environment is dark:
    Turn on the LED.
    Improve webcam visibility.
```

---

## 🏢 Applications

* Colleges and universities
* Hospitals
* Shopping malls
* Railway stations
* Airports
* Offices
* Public buildings
* Homes
* Care centres

---

## ⚠️ Current Limitations

* The current model detects only people, tables, chairs, and doors.
* Detection accuracy depends on the quality and diversity of the training dataset.
* Webcam performance may decrease in poor-light conditions.
* Ultrasonic sensors may not correctly detect certain soft or angled surfaces.
* Complex environments may generate multiple alerts simultaneously.
* Object detection may be affected by occlusion or unusual viewing angles.
* The system currently does not provide complete indoor map-based navigation.
* The prototype requires further real-world testing and calibration.

---

## 🔮 Future Enhancements

* Emergency SOS alerts to relatives or caregivers
* Custom PCB for a compact wearable design
* Indoor mapping and route planning
* Smartphone application integration
* Bluetooth earphone support
* Multi-language voice guidance
* Battery-level monitoring
* Location sharing with caregivers
* Additional object-detection classes
* Improved staircase and doorway detection
* Edge AI optimization for faster inference
* Outdoor GPS navigation support

---

## 👥 Contributors

* **Kishore J**
* **Rubhavarshini B**
* **Omana S**
* **Sanmathi S**

---

## 🔒 License

Copyright © 2026 Kishore J. All Rights Reserved.

This project is proprietary and confidential. No part of this project, including its source code, trained models, datasets, documentation, designs, or hardware implementation, may be copied, used, modified, reproduced, distributed, published, sublicensed, or sold without prior written permission from the copyright owner.

Unauthorized use of this project for academic, personal, research, or commercial purposes is strictly prohibited.

---

## ⚠️ Disclaimer

This project is an assistive prototype developed for academic and research purposes. It should not be considered a complete replacement for a white cane, guide dog, caregiver, or certified mobility aid.

The system must be tested carefully in controlled environments before real-world use. The developers are not responsible for injuries, accidents, or damages caused by improper use, inaccurate detection, sensor failure, or hardware failure.

