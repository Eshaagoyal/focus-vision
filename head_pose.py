import numpy as np
import cv2

# 3D coordinates of a standard human face (universal reference)
# These never change — same for every person
# Order must match LANDMARK_IDS exactly
MODEL_POINTS = np.array([
    (0.0,    0.0,    0.0),    # Nose tip
    (0.0,   -330.0, -65.0),   # Chin
    (-225.0, 170.0, -135.0),  # Left eye outer corner
    (225.0,  170.0, -135.0),  # Right eye outer corner
    (-150.0,-150.0, -125.0),  # Left mouth corner
    (150.0, -150.0, -125.0)   # Right mouth corner
], dtype=np.float64)

# Corresponding MediaPipe landmark indices for above 6 points
LANDMARK_IDS = [1, 152, 263, 33, 287, 57]


def get_head_angles(face_landmarks, frame_w, frame_h):
    """
    Takes face landmarks + frame size.
    Returns (pitch, yaw) angles in degrees.
    pitch = up/down tilt
    yaw   = left/right turn
    """

    # Step 1 — Extract 2D pixel positions of our 6 landmarks
    image_points = []
    for idx in LANDMARK_IDS:
        lm = face_landmarks.landmark[idx]
        x = lm.x * frame_w
        y = lm.y * frame_h
        image_points.append((x, y))
    image_points = np.array(image_points, dtype=np.float64)

    # Step 2 — Build camera matrix (approximation using frame size)
    focal_length = frame_w
    cx = frame_w / 2
    cy = frame_h / 2
    camera_matrix = np.array([
        [focal_length, 0,            cx],
        [0,            focal_length, cy],
        [0,            0,            1 ]
    ], dtype=np.float64)

    # No lens distortion assumed
    dist_coeffs = np.zeros((4, 1))

    # Step 3 — solvePnP gives us rotation vector
    success, rotation_vec, translation_vec = cv2.solvePnP(
        MODEL_POINTS,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        return 0.0, 0.0

    # Step 4 — Convert rotation vector to euler angles
    rotation_mat, _ = cv2.Rodrigues(rotation_vec)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rotation_mat)

    raw_pitch = angles[0]  # Positive = looking up, Negative = looking down
    raw_yaw   = angles[1]  # Positive = looking right, Negative = looking left

    # Smooth the angles
    if not hasattr(get_head_angles, 'history_pitch'):
        get_head_angles.history_pitch = []
        get_head_angles.history_yaw = []
        
    get_head_angles.history_pitch.append(raw_pitch)
    get_head_angles.history_yaw.append(raw_yaw)
    
    if len(get_head_angles.history_pitch) > 5:
        get_head_angles.history_pitch.pop(0)
        get_head_angles.history_yaw.pop(0)
        
    pitch = sum(get_head_angles.history_pitch) / len(get_head_angles.history_pitch)
    yaw = sum(get_head_angles.history_yaw) / len(get_head_angles.history_yaw)

    return pitch, yaw


def get_head_direction(pitch, yaw):
    """
    Converts raw angles into a human readable direction label.
    Thresholds tuned for natural sitting position.
    """
    if yaw < -15:
        return "Looking LEFT"
    elif yaw > 15:
        return "Looking RIGHT"
    elif pitch < -10:
        return "Looking DOWN"
    elif pitch > 20:
        return "Looking UP"
    else:
        return "FORWARD"