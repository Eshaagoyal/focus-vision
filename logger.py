import csv
import os
import time
from datetime import datetime

class SessionLogger:
    """
    Logs attention data every second to a CSV file.
    Each session creates a new file with timestamp in name.
    """

    def __init__(self):
        # Create logs folder if it doesn't exist
        os.makedirs("logs", exist_ok=True)

        # Unique filename per session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = f"logs/session_{timestamp}.csv"

        # Create file and write header
        with open(self.filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "elapsed_sec",
                "head_direction",
                "gaze_direction",
                "score",
                "state"
            ])

        self.start_time = time.time()
        print(f"Logging to: {self.filename}")

    def log(self, head_dir, gaze_dir, score, state):
        """Call this every second to log one row."""
        elapsed = int(time.time() - self.start_time)
        timestamp = datetime.now().strftime("%H:%M:%S")

        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                elapsed,
                head_dir,
                gaze_dir,
                score,
                state
            ])

    def get_filename(self):
        return self.filename