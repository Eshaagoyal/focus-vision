import cv2
import numpy as np
import time


class Dashboard:
    """
    Draws a professional side panel on the right of the webcam frame.
    Shows score bar, state, session timer, distraction count.
    """

    PANEL_WIDTH = 280
    BG_COLOR    = (30, 30, 30)
    GREEN       = (0, 230, 118)
    ORANGE      = (0, 165, 255)
    RED         = (0, 0, 255)
    WHITE       = (255, 255, 255)
    GRAY        = (150, 150, 150)

    def __init__(self):
        self.start_time = time.time()

    def _score_color(self, score):
        if score >= 70:
            return self.GREEN
        elif score >= 40:
            return self.ORANGE
        else:
            return self.RED

    def _elapsed(self):
        e = int(time.time() - self.start_time)
        return f"{e//60:02d}:{e%60:02d}"

    def draw(self, frame, score, state, head_dir,
             gaze_dir, eye_state, distractions,
             distracted_secs, avg_score, streak_stars=0):
        """
        Attaches a side panel to the right of the frame.
        Returns the combined frame.
        """
        h, w = frame.shape[:2]
        panel = np.full((h, self.PANEL_WIDTH, 3),
                        self.BG_COLOR, dtype=np.uint8)

        color = self._score_color(score)

        # Title
        cv2.putText(panel, "ATTENTION", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    self.WHITE, 2)
        cv2.putText(panel, "TRACKER", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    color, 2)

        # Divider
        cv2.line(panel, (10, 75), (self.PANEL_WIDTH - 10, 75),
                 (70, 70, 70), 1)

        # Score circle
        cx, cy = self.PANEL_WIDTH // 2, 140
        cv2.circle(panel, (cx, cy), 55, (60, 60, 60), -1)
        cv2.circle(panel, (cx, cy), 55, color, 2)
        cv2.putText(panel, str(score),
                    (cx - 28 if score == 100 else cx - 20, cy + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        cv2.putText(panel, "/100", (cx - 18, cy + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    self.GRAY, 1)

        # Score bar
        bar_x, bar_y = 20, 210
        bar_w = self.PANEL_WIDTH - 40
        cv2.rectangle(panel, (bar_x, bar_y),
                      (bar_x + bar_w, bar_y + 12),
                      (60, 60, 60), -1)
        filled = int(bar_w * score / 100)
        if filled > 0:
            cv2.rectangle(panel, (bar_x, bar_y),
                          (bar_x + filled, bar_y + 12),
                          color, -1)

        # State
        cv2.putText(panel, state, (20, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

        # Divider
        cv2.line(panel, (10, 265),
                 (self.PANEL_WIDTH - 10, 265), (70, 70, 70), 1)

        # Stats
        stats = [
            ("Head",         head_dir.replace("Looking ", "")),
            ("Gaze",         gaze_dir.replace("Gaze: ", "")),
            ("Eyes",         eye_state),
            ("Distractions", str(distractions)),
            ("Avg Score",    f"{avg_score}/100"),
            ("Streaks",      "*" * streak_stars if streak_stars > 0 else "None"),
            ("Session",      self._elapsed()),
        ]

        y = 290
        for label, value in stats:
            cv2.putText(panel, f"{label}:", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        self.GRAY, 1)
            val_color = self.WHITE
            if label == "Eyes" and value == "CLOSED":
                val_color = self.RED
            elif label == "Head" and value != "FORWARD":
                val_color = self.ORANGE
            cv2.putText(panel, value,
                        (130, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        val_color, 1)
            y += 28

        # Distraction warning bar
        if distracted_secs > 0:
            cv2.line(panel, (10, y + 5),
                     (self.PANEL_WIDTH - 10, y + 5),
                     (70, 70, 70), 1)
            cv2.putText(panel, f"Distracted: {distracted_secs}s",
                        (20, y + 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        self.ORANGE, 1)
            # Progress bar toward 10s alert
            bar_fill = min(distracted_secs / 10.0, 1.0)
            filled_w = int((self.PANEL_WIDTH - 40) * bar_fill)
            cv2.rectangle(panel, (20, y + 35),
                          (self.PANEL_WIDTH - 20, y + 45),
                          (60, 60, 60), -1)
            if filled_w > 0:
                cv2.rectangle(panel, (20, y + 35),
                              (20 + filled_w, y + 45),
                              self.ORANGE, -1)

        # Combine webcam + panel
        combined = np.hstack([frame, panel])
        return combined