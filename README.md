<div align="center">
  <img src="https://img.shields.io/badge/Status-Capstone_Ready-success?style=for-the-badge" alt="Status" />
  
  <h1>👁️ FocusVision</h1>
  <p><b>Advanced AI Productivity & Ergonomics Tracking System</b></p>
  
  <p>
    <img src="https://img.shields.io/badge/Python-3.8+-blue.svg?style=flat-square&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/Flask-Web_Framework-lightgrey.svg?style=flat-square&logo=flask" alt="Flask" />
    <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-yellow.svg?style=flat-square" alt="YOLOv8" />
    <img src="https://img.shields.io/badge/MediaPipe-Google-red.svg?style=flat-square&logo=google" alt="MediaPipe" />
    <img src="https://img.shields.io/badge/OpenCV-Computer_Vision-green.svg?style=flat-square&logo=opencv" alt="OpenCV" />
  </p>
</div>

<br/>

> **Note to Evaluator:** Please refer to the `Sample Demo Video` attached with this submission for a quick 2-minute walkthrough of the system's capabilities.

## 📖 About The Project

**FocusVision** is a dual-model computer vision architecture designed to solve real-world productivity and ergonomic challenges, particularly in remote work environments. By running two advanced neural networks concurrently, the system monitors user behavior, tracks focus states, detects hardware distractions (mobile phones), and delivers real-time biofeedback via a modern web interface.

---

## ✨ System Features

### 🧠 Dual-AI Processing Engine
- **MediaPipe Face Mesh:** Calculates complex 3D facial geometry (Eye Aspect Ratio, Iris positioning, Head Yaw/Pitch/Roll) to determine gaze direction and micro-sleep (drowsiness).
- **YOLOv8 Object Detection:** A fine-tuned nano model actively scans the frame for mobile devices to flag critical distractions.

### 📊 Real-Time Glassmorphism Dashboard
- **Live Data Streams:** Watch your attention score calculate in real-time via the `/metrics` API.
- **Chart.js Integration:** Dynamic, color-coded graphs that react instantly to your focus state (e.g., Red drops for phone usage, Purple for drowsiness).

### 🔊 Interactive Biometric Alerts
- **Voice TTS System:** The browser-native SpeechSynthesis API verbally warns you when focus drops below safe thresholds.
- **Visual Overlays:** Screen blurs and red tinting alert you of ergonomic hazards (sitting too close to the monitor).

### 📈 Historical Analytics
- **Session Logging:** Every session is saved locally as a CSV file.
- **Insights Tab:** Review past performance with Doughnut pie charts mapping your total attention distribution (Attentive vs. Distracted vs. Phone vs. Drowsy).

---

## 🛠️ Project Architecture

```text
📦 FocusVision Directory
 ┣ 📂 logs                # Auto-generated CSV session data
 ┣ 📂 static              # Frontend JS and CSS (Glassmorphism UI)
 ┣ 📂 templates           # Flask HTML templates
 ┣ 📜 server.py           # Main Flask Backend / REST API
 ┣ 📜 main.py             # Core OpenCV Video Pipeline
 ┣ 📜 face_mesh.py        # MediaPipe 3D Geometry logic
 ┣ 📜 phone_detector.py   # YOLOv8 inference logic
 ┣ 📜 scorer.py           # Mathematical attention scoring algorithm
 ┣ 📜 requirements.txt    # Python dependencies
 ┗ 📜 yolov8n.pt          # Pre-trained Ultralytics weights
```

---

## ⚙️ Quick Start Guide

### Prerequisites
Make sure you have `Python 3.8+` installed on your machine.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Eshaagoyal/focus-vision.git
   cd focus-vision
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. **Start the AI Server:**
   ```bash
   python server.py
   ```
2. **Open the Dashboard:** Navigate to `http://127.0.0.1:5000` in your web browser.
3. **Begin Tracking:** Click **"▶ Start Session"** and allow webcam access.

---

<div align="center">
  <i>Developed with ❤️ for Capstone Project Evaluation</i>
</div>
