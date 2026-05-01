import cv2
import time
import os
import glob
import csv
from flask import Flask, render_template, Response, jsonify, request
from face_mesh import create_face_mesh, draw_mesh
from head_pose import get_head_angles, get_head_direction
from gaze import get_iris_ratio, get_gaze_direction, get_eye_state, get_face_distance_ratio
from scorer import AttentionScorer
from logger import SessionLogger
from alert import AlertSystem
from phone_detector import PhoneDetector

app = Flask(__name__)

# --- Global State ---
face_mesh = create_face_mesh()
scorer = AttentionScorer()
logger = SessionLogger()
alert = AlertSystem(distraction_threshold=5)
phone_detector = PhoneDetector()

camera = cv2.VideoCapture(0)

app_state = "START_SCREEN" # START_SCREEN, ACTIVE, PAUSED
pomodoro_duration = 25 * 60
active_session_time = 0.0
last_update = time.time()

# Shared metrics for the frontend
metrics = {
    "score": 0,
    "state": "NO FACE",
    "head_dir": "UNKNOWN",
    "gaze_dir": "CENTER",
    "eye_state": "OPEN",
    "distractions": 0,
    "avg_score": 0,
    "streak_stars": 0,
    "distracted_secs": 0,
    "session_time_str": "00:00"
}

def generate_frames():
    global app_state, active_session_time, last_update, metrics
    
    while True:
        success, frame = camera.read()
        if not success:
            break
            
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        if app_state == "ACTIVE":
            phone_visible = phone_detector.check_for_phone(frame)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                # draw_mesh(frame, face_landmarks) # Hidden per user request

                pitch, yaw = get_head_angles(face_landmarks, w, h)
                head_dir = get_head_direction(pitch, yaw)

                ratio = get_iris_ratio(face_landmarks, w, h)
                gaze_dir = get_gaze_direction(ratio)
                eye_state, ear = get_eye_state(face_landmarks)
                face_dist_ratio = get_face_distance_ratio(face_landmarks)

                score, state = scorer.update(head_dir, gaze_dir)
                if eye_state == "CLOSED":
                    score = max(0, score - 30)
                    state = "DROWSY"
                elif face_dist_ratio > 0.20:
                    score = max(0, score - 20)
                    state = "TOO CLOSE"
            else:
                score, state = scorer.update_no_face()
                head_dir = "NO FACE"
                gaze_dir = "CENTER"
                eye_state = "OPEN"

            if phone_visible:
                score = 0
                state = "PHONE DETECTED"

            alert_on = alert.update(state)
            if alert_on:
                frame = alert.draw_alert(frame)

            # 1-second interval logic
            now = time.time()
            elapsed = now - last_update
            if elapsed >= 1.0:
                # Cap elapsed to prevent huge jumps if the camera lags
                if elapsed > 2.0: elapsed = 1.0 
                
                active_session_time += elapsed
                last_update = now
                
                if active_session_time >= pomodoro_duration:
                    app_state = "PAUSED"
                    active_session_time = 0.0
                
                scorer.update_streak(elapsed, score)
                logger.log(head_dir, gaze_dir, score, state)

            # Update metrics for frontend
            avg_score, distractions, _, _ = scorer.get_session_summary()
            
            # Calculate Pomodoro countdown
            remaining = max(0, pomodoro_duration - active_session_time)
            r_mins = int(remaining // 60)
            r_secs = int(remaining % 60)
            
            metrics.update({
                "score": score,
                "state": state,
                "head_dir": head_dir.replace("Looking ", ""),
                "gaze_dir": gaze_dir.replace("Gaze: ", ""),
                "eye_state": eye_state,
                "distractions": distractions,
                "avg_score": avg_score,
                "streak_stars": scorer.streak_stars,
                "distracted_secs": alert.get_distracted_seconds(),
                "alert_active": alert_on,
                "session_time_str": f"{r_mins:02d}:{r_secs:02d}"
            })

        else:
            # Blurred frame for START/PAUSED states
            frame = cv2.GaussianBlur(frame, (51, 51), 0)
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            
            text = "ATTENTION TRACKER" if app_state == "START_SCREEN" else "SESSION PAUSED"
            cv2.putText(frame, text, (int(w/2) - 180, int(h/2)), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

            alert.distracted_since = None
            alert.alert_active = False

        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

import json
from collections import Counter

# --- API Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/metrics')
def get_metrics():
    return jsonify({
        "app_state": app_state,
        "metrics": metrics
    })

@app.route('/api/control', methods=['POST'])
def control():
    global app_state, active_session_time, pomodoro_duration, last_update
    data = request.json
    action = data.get('action')
    
    if action == 'start':
        app_state = "ACTIVE"
        last_update = time.time()
    elif action == 'pause':
        app_state = "PAUSED"
    elif action == 'set_timer':
        secs = float(data.get('seconds', 25 * 60))
        pomodoro_duration = secs
        active_session_time = 0.0 # reset current Pomodoro block
    elif action == 'stop':
        # Kill the local server so the user doesn't need the terminal
        os._exit(0)
        
    return jsonify({"status": "success", "app_state": app_state})

@app.route('/api/tags', methods=['GET', 'POST'])
def tags_api():
    tags_file = 'logs/tags.json'
    if request.method == 'POST':
        data = request.json
        session_id = data.get('id')
        tag = data.get('tag')
        
        tags = {}
        if os.path.exists(tags_file):
            with open(tags_file, 'r') as f:
                tags = json.load(f)
        tags[session_id] = tag
        with open(tags_file, 'w') as f:
            json.dump(tags, f)
        return jsonify({"status": "success"})
    else:
        if os.path.exists(tags_file):
            with open(tags_file, 'r') as f:
                return jsonify(json.load(f))
        return jsonify({})

@app.route('/api/insights')
def insights():
    log_files = glob.glob("logs/*.csv")
    summaries = []
    
    global_total_secs = 0
    global_score_sum = 0
    global_score_count = 0
    morning_sessions = 0
    evening_sessions = 0
    
    for file in sorted(log_files):
        scores = []
        state_tally = []
        distractions = 0
        
        with open(file, 'r') as f:
            reader = csv.DictReader(f)
            last_state = "ATTENTIVE"
            for row in reader:
                try:
                    score = int(row['score'])
                    scores.append(score)
                    
                    state = row['state']
                    state_tally.append(state)
                    
                    if last_state == "ATTENTIVE" and state != "ATTENTIVE":
                        distractions += 1
                    last_state = state
                except:
                    pass
        
        if scores:
            session_id = os.path.basename(file)
            avg_score = int(sum(scores) / len(scores))
            date_str = session_id.split('_')[1] # YYYYMMDD
            time_str = session_id.split('_')[2].split('.')[0] # HHMMSS
            
            # Global Stats Calculation
            global_total_secs += len(scores)
            global_score_sum += sum(scores)
            global_score_count += len(scores)
            
            hour = int(time_str[:2])
            if hour < 12:
                morning_sessions += 1
            else:
                evening_sessions += 1
            
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            
            # Primary Distraction
            distraction_states = [s for s in state_tally if s != "ATTENTIVE"]
            primary_distraction = "None"
            if distraction_states:
                primary_distraction = Counter(distraction_states).most_common(1)[0][0]
                
            # State Distribution Pie Chart Data
            state_counts = Counter(state_tally)
            state_distribution = {
                "Attentive": state_counts.get("ATTENTIVE", 0),
                "Distracted": state_counts.get("DISTRACTED", 0) + state_counts.get("NOT FOCUSED", 0),
                "Drowsy": state_counts.get("DROWSY", 0),
                "Phone": state_counts.get("PHONE DETECTED", 0),
                "Posture": state_counts.get("TOO CLOSE", 0)
            }
            
            summaries.append({
                "id": session_id,
                "date": formatted_date,
                "time": f"{time_str[:2]}:{time_str[2:4]}",
                "avg_score": avg_score,
                "distractions": distractions,
                "duration_secs": len(scores),
                "primary_distraction": primary_distraction,
                "state_distribution": state_distribution,
                "history": scores[::5], # downsampled
                "history_states": state_tally[::5]
            })
            
    best_time = "Evening" if evening_sessions > morning_sessions else "Morning"
    if morning_sessions == evening_sessions: best_time = "Balanced"
    
    global_stats = {
        "total_hours": round(global_total_secs / 3600, 1),
        "overall_avg": int(global_score_sum / max(1, global_score_count)),
        "best_time": best_time
    }
            
    return jsonify({
        "global_stats": global_stats,
        "sessions": summaries
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
