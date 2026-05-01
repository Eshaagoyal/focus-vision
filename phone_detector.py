try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

class PhoneDetector:
    def __init__(self):
        self.model = None
        self.frame_counter = 0
        self.phone_detected = False
        
        if YOLO_AVAILABLE:
            # Load nano model for speed
            self.model = YOLO('yolov8n.pt')

    def check_for_phone(self, frame):
        """
        Runs YOLO inference every 10 frames to save CPU.
        Returns True if cell phone is detected.
        """
        if not YOLO_AVAILABLE or self.model is None:
            return False

        self.frame_counter += 1
        # Run every 10 frames
        if self.frame_counter % 10 == 0:
            # classes=[67] restricts detection to cell phones
            results = self.model(frame, classes=[67], verbose=False)
            
            self.phone_detected = False
            for r in results:
                if len(r.boxes) > 0:
                    self.phone_detected = True
                    break
                    
        return self.phone_detected
