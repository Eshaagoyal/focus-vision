# Attention & Ergonomics Tracker

A comprehensive computer vision and productivity application designed to help users maintain focus and healthy screen habits during remote work and study sessions.

## 🎯 Project Overview
This project solves real-world productivity and ergonomic challenges by monitoring user behavior via a webcam. It uses a novel combination of AI models to track focus, detect distractions, and alert the user in real-time.

### Key Features
*   **Dual AI Architecture**: Runs **MediaPipe Face Mesh** (for 3D head pose estimation, eye state tracking, and screen distance measuring) concurrently with **YOLOv8** (for detecting mobile phone usage).
*   **Real-Time Dashboard**: A Flask-based web application with a modern Glassmorphism UI that visualizes attention scores dynamically.
*   **Audio Alerts**: Integrated Text-To-Speech (TTS) engine that warns the user when their attention drops below a certain threshold or if poor posture is detected.
*   **Advanced Analytics Engine**: Automatically logs session data to CSV files and generates historical insights, including colored trend lines, pie charts, and distraction root-cause analysis using Chart.js.

## ⚙️ Installation Instructions

1. Ensure you have Python 3.8+ installed on your system.
2. Clone or extract this repository to your local machine.
3. Open a terminal and navigate to the project directory.
4. (Optional but recommended) Create a virtual environment:
   ```bash
   python -m venv venv
   # On Windows: venv\Scripts\activate
   # On Mac/Linux: source venv/bin/activate
   ```
5. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 How to Run the Inference Script

1. In your terminal, run the following command:
   ```bash
   python server.py
   ```
2. The terminal will indicate that the Flask server is running.
3. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```
4. Click **"▶ Start Session"** on the dashboard to begin the live computer vision tracking. The application will request webcam access.

## 📊 How it works
*   **Attentive**: Looking directly at the screen at a safe distance.
*   **Distracted / Not Focused**: Looking away from the screen (head turned left, right, up, or down).
*   **Drowsy**: Eyes closed for an extended period.
*   **Phone Detected**: YOLOv8 detects a mobile phone in the frame.
*   **Posture**: Face is detected too close to the screen (ergonomic warning).

All session data is saved automatically to the `/logs` directory and can be analyzed in the **Insights** tab of the web dashboard.
