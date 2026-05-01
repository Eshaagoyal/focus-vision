import cv2
import numpy as np
from collections import deque

class LiveGraph:
    """
    Graph that updates in the main loop using pure OpenCV.
    Bypasses Matplotlib completely to avoid Windows DLL blocks.
    """

    def __init__(self, maxlen=60):
        self.maxlen = maxlen
        self.scores = deque([0] * maxlen, maxlen=maxlen)
        self.width = 600
        self.height = 300
        # Create window
        cv2.namedWindow("Attention Graph", cv2.WINDOW_AUTOSIZE)

    def push_and_update(self, score):
        """
        Call this every second from main loop.
        Pushes score AND redraws graph immediately.
        """
        self.scores.append(score)
        data = list(self.scores)
        
        # Create dark background
        img = np.full((self.height, self.width, 3), (30, 30, 30), dtype=np.uint8)
        
        current = data[-1]
        avg = int(sum(data) / max(1, len(data)))
        
        if current >= 70:
            color = (118, 230, 0) # Green (BGR)
        elif current >= 40:
            color = (0, 165, 255) # Orange (BGR)
        else:
            color = (54, 67, 244) # Red (BGR)

        # Draw grid lines for thresholds
        # y=0 is top, y=height is bottom (0 score). 70 score -> 30% from top
        y70 = int(self.height - (70 / 100 * self.height))
        y40 = int(self.height - (40 / 100 * self.height))
        cv2.line(img, (0, y70), (self.width, y70), (118, 230, 0), 1) # 70 line
        cv2.line(img, (0, y40), (self.width, y40), (0, 165, 255), 1) # 40 line

        # Plot data points
        pts = []
        for i, val in enumerate(data):
            x = int(i * (self.width / max(1, self.maxlen - 1)))
            y = int(self.height - (val / 100 * self.height))
            y = max(1, min(y, self.height - 1))
            pts.append((x, y))

        # Draw lines between points
        for i in range(len(pts) - 1):
            cv2.line(img, pts[i], pts[i+1], color, 2, cv2.LINE_AA)

        # Draw labels
        cv2.putText(img, f"Now: {current}/100", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(img, f"Avg: {avg}/100", (self.width - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        
        # Display
        cv2.imshow("Attention Graph", img)

    def stop(self):
        try:
            cv2.destroyWindow("Attention Graph")
        except:
            pass