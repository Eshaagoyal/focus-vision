from collections import deque
import time

class AttentionScorer:
    """
    Combines head pose and gaze direction into
    a smooth attention score between 0 and 100.
    Uses a rolling average to avoid jumpy values.
    """

    def __init__(self):
        self.score_history = deque(maxlen=60)  # stores last 60 scores (60 seconds)
        self.distraction_count = 0
        self.last_state = "ATTENTIVE"
        self.start_time = time.time()
        
        # Streak System
        self.streak_seconds = 0
        self.streak_stars = 0

    def compute_score(self, head_direction, gaze_direction):
        """
        Rules:
        - Both head forward + gaze center = 100 (fully attentive)
        - Head forward but gaze away = 60 (slightly distracted)
        - Head away but gaze center = 50 (possibly distracted)
        - Both head and gaze away = 10 (clearly distracted)
        - No face detected = 0
        """
        head_ok = (head_direction == "FORWARD")
        gaze_ok = (gaze_direction == "Gaze: CENTER")

        if head_ok and gaze_ok:
            raw_score = 100
        elif head_ok and not gaze_ok:
            raw_score = 60
        elif not head_ok and gaze_ok:
            raw_score = 50
        else:
            raw_score = 10

        return raw_score

    def update(self, head_direction, gaze_direction):
        """
        Call this every frame.
        Returns smoothed score and current state label.
        """
        raw = self.compute_score(head_direction, gaze_direction)
        self.score_history.append(raw)

        # Smooth score = average of last 10 frames
        recent = list(self.score_history)[-10:]
        smooth_score = int(sum(recent) / len(recent))

        # Determine state
        if smooth_score >= 70:
            state = "ATTENTIVE"
        elif smooth_score >= 40:
            state = "DISTRACTED"
        else:
            state = "NOT FOCUSED"

        # Count distraction events (transitions from attentive to distracted)
        if self.last_state == "ATTENTIVE" and state != "ATTENTIVE":
            self.distraction_count += 1
        self.last_state = state
        return smooth_score, state

    def update_streak(self, elapsed_seconds, current_score):
        """Called every second to track gamification streaks."""
        if current_score >= 80:
            self.streak_seconds += elapsed_seconds
            if self.streak_seconds >= 300: # 5 minutes
                self.streak_stars += 1
                self.streak_seconds = 0
        elif current_score < 50:
            # Reset streak progress if distracted
            self.streak_seconds = 0

    def update_no_face(self):
        """Called when no face is detected."""
        self.score_history.append(0)
        recent = list(self.score_history)[-10:]
        smooth_score = int(sum(recent) / len(recent))
        return smooth_score, "NO FACE"

    def get_session_summary(self):
        """Returns overall session stats."""
        elapsed = int(time.time() - self.start_time)
        if self.score_history:
            avg = int(sum(self.score_history) / len(self.score_history))
        else:
            avg = 0
        minutes = elapsed // 60
        seconds = elapsed % 60
        return avg, self.distraction_count, minutes, seconds