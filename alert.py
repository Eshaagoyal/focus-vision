import cv2
import time
import threading

try:
    import winsound
    SOUND_AVAILABLE = False # Disabled in favor of frontend AI voice
except ImportError:
    SOUND_AVAILABLE = False


class AlertSystem:
    """
    Fires a visual + audio alert when the user is
    continuously distracted for more than threshold seconds.
    """

    def __init__(self, distraction_threshold=10):
        self.threshold        = distraction_threshold
        self.distracted_since = None
        self.alert_active     = False
        self.alert_start_time = None
        self.alert_duration   = 2.0  # seconds alert stays on screen

    def update(self, state):
        """
        Call every frame with current state.
        Returns True if alert should fire this frame.
        """
        now = time.time()

        if state in ("DISTRACTED", "NOT FOCUSED", "NO FACE"):
            if self.distracted_since is None:
                self.distracted_since = now
            elif now - self.distracted_since >= self.threshold:
                self._trigger_alert()
        else:
            # Reset when attentive
            self.distracted_since = None

        # Check if alert is still active
        if self.alert_active:
            if now - self.alert_start_time >= self.alert_duration:
                self.alert_active = False

        return self.alert_active

    def _trigger_alert(self):
        if not self.alert_active:
            self.alert_active     = True
            self.alert_start_time = time.time()
            self.distracted_since = None  # reset timer after alert
            # Play beep in separate thread so it doesn't block webcam
            if SOUND_AVAILABLE:
                threading.Thread(
                    target=lambda: winsound.Beep(1000, 500),
                    daemon=True
                ).start()

    def draw_alert(self, frame):
        """Draws red overlay on frame when alert is active."""
        if self.alert_active:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0),
                         (frame.shape[1], frame.shape[0]),
                         (0, 0, 255), -1)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
            cv2.putText(frame, "⚠ ATTENTION ALERT!",
                       (int(frame.shape[1]/2) - 180, int(frame.shape[0]/2)),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        return frame

    def get_distracted_seconds(self):
        """How long currently distracted in seconds."""
        if self.distracted_since:
            return int(time.time() - self.distracted_since)
        return 0