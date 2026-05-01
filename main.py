import cv2
import time
from face_mesh import create_face_mesh, draw_mesh
from head_pose import get_head_angles, get_head_direction
from gaze import get_iris_ratio, get_gaze_direction, get_eye_state, get_face_distance_ratio
from scorer import AttentionScorer
from graph import LiveGraph
from logger import SessionLogger
from alert import AlertSystem
from dashboard import Dashboard
from report import save_report
from phone_detector import PhoneDetector

# Initialize all modules
face_mesh  = create_face_mesh()
scorer     = AttentionScorer()
graph      = LiveGraph()
logger     = SessionLogger()
alert      = AlertSystem(distraction_threshold=10)
dashboard  = Dashboard()
phone_detector = PhoneDetector()
cap        = cv2.VideoCapture(0)

# State variables
app_state   = "START_SCREEN" # START_SCREEN, ACTIVE, PAUSED
active_session_time = 0.0 # seconds spent in ACTIVE state
pomodoro_duration   = 25 * 60 # 25 minutes in seconds

last_update = time.time()
score       = 0
state       = "NO FACE"
head_dir    = "UNKNOWN"
gaze_dir    = "Gaze: CENTER"
eye_state   = "OPEN"
avg_score   = 0

print("Attention Tracker started. Press SPACE to start.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w  = frame.shape[:2]

    # Handle Key Presses
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '):  # SPACEBAR
        if app_state == "START_SCREEN":
            app_state = "ACTIVE"
            last_update = time.time()
        elif app_state == "PAUSED":
            app_state = "ACTIVE"
            last_update = time.time()
    elif key == ord('p'):  # 'P' KEY
        if app_state == "ACTIVE":
            app_state = "PAUSED"
        elif app_state == "PAUSED":
            app_state = "ACTIVE"
            last_update = time.time()

    if app_state == "ACTIVE":
        phone_visible = phone_detector.check_for_phone(frame)

        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            draw_mesh(frame, face_landmarks)

            # Head pose
            pitch, yaw = get_head_angles(face_landmarks, w, h)
            head_dir   = get_head_direction(pitch, yaw)

            # Gaze + eye state + posture
            ratio     = get_iris_ratio(face_landmarks, w, h)
            gaze_dir  = get_gaze_direction(ratio)
            eye_state, ear = get_eye_state(face_landmarks)
            face_dist_ratio = get_face_distance_ratio(face_landmarks)

            # Score — penalise extra if eyes closed
            score, state = scorer.update(head_dir, gaze_dir)
            if eye_state == "CLOSED":
                score = max(0, score - 30)
                state = "DROWSY"
            elif face_dist_ratio > 0.35: # If eyes take up > 35% of frame width
                score = max(0, score - 20)
                state = "TOO CLOSE"
        else:
            score, state = scorer.update_no_face()
            head_dir  = "NO FACE"
            gaze_dir  = "Gaze: CENTER"
            eye_state = "OPEN"

        if phone_visible:
            score = 0
            state = "PHONE DETECTED"

        # Alert system
        alert_on = alert.update(state)
        if alert_on:
            frame = alert.draw_alert(frame)

        # Every 1 second — update graph + log + Pomodoro + Streaks
        now = time.time()
        if now - last_update >= 1.0:
            elapsed = now - last_update
            active_session_time += elapsed
            
            # Trigger Pomodoro Break
            if active_session_time >= pomodoro_duration:
                app_state = "PAUSED"
                active_session_time = 0.0  # Reset for next Pomodoro
            
            scorer.update_streak(elapsed, score)
            graph.push_and_update(score)
            logger.log(head_dir, gaze_dir, score, state)
            last_update = now

    else:
        # START_SCREEN or PAUSED
        import numpy as np
        # Blur the frame heavily to focus on the text
        frame = cv2.GaussianBlur(frame, (51, 51), 0)
        
        # Add a dark translucent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        if app_state == "START_SCREEN":
            cv2.putText(frame, "ATTENTION TRACKER", (int(w/2) - 200, int(h/2) - 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
            cv2.putText(frame, "Press SPACE to Start", (int(w/2) - 170, int(h/2) + 20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        elif app_state == "PAUSED":
            cv2.putText(frame, "SESSION PAUSED", (int(w/2) - 180, int(h/2) - 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 165, 255), 3)
            cv2.putText(frame, "Take a break. Press SPACE to Resume", (int(w/2) - 280, int(h/2) + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        
        # Pause the alert triggers
        alert.distracted_since = None
        alert.alert_active = False

    # Session stats
    avg_score, distractions, mins, secs = scorer.get_session_summary()
    distracted_secs = alert.get_distracted_seconds()

    # Draw dashboard panel
    frame = dashboard.draw(
        frame, score, state, head_dir,
        gaze_dir, eye_state, distractions,
        distracted_secs, avg_score, scorer.streak_stars
    )

    cv2.imshow("Attention Tracker", frame)

# Save report on quit
avg_score, distractions, mins, secs = scorer.get_session_summary()
save_report(avg_score, distractions, mins, secs, logger.get_filename())

graph.stop()
cap.release()
cv2.destroyAllWindows()