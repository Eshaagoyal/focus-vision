# Iris landmark indices
LEFT_IRIS  = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

# Eye corner landmarks
LEFT_EYE_CORNERS  = [362, 263]
RIGHT_EYE_CORNERS = [33,  133]

# Eye vertical landmarks for blink detection (EAR)
# Top and bottom points of each eye
LEFT_EYE_TOP_BOTTOM  = [386, 374]
RIGHT_EYE_TOP_BOTTOM = [159, 145]
LEFT_EYE_LEFT_RIGHT  = [263, 362]
RIGHT_EYE_LEFT_RIGHT = [133,  33]


def get_iris_ratio(face_landmarks, frame_w, frame_h):
    """
    Returns iris horizontal ratio (0.0=left, 0.5=center, 1.0=right)
    Averaged across both eyes for stability.
    """
    def iris_position(iris_ids, corner_ids):
        iris_x = sum(
            face_landmarks.landmark[i].x for i in iris_ids
        ) / 4
        left_x  = face_landmarks.landmark[corner_ids[0]].x
        right_x = face_landmarks.landmark[corner_ids[1]].x
        width   = abs(right_x - left_x)
        if width == 0:
            return 0.5
        return (iris_x - min(left_x, right_x)) / width

    left  = iris_position(LEFT_IRIS,  LEFT_EYE_CORNERS)
    right = iris_position(RIGHT_IRIS, RIGHT_EYE_CORNERS)
    
    raw_ratio = (left + right) / 2
    
    # Smooth the ratio
    if not hasattr(get_iris_ratio, 'history'):
        get_iris_ratio.history = []
        
    get_iris_ratio.history.append(raw_ratio)
    if len(get_iris_ratio.history) > 5:
        get_iris_ratio.history.pop(0)
        
    return sum(get_iris_ratio.history) / len(get_iris_ratio.history)


def get_gaze_direction(ratio):
    """Converts iris ratio to gaze label."""
    if ratio < 0.40:
        return "Gaze: LEFT"
    elif ratio > 0.60:
        return "Gaze: RIGHT"
    else:
        return "Gaze: CENTER"


def get_ear(face_landmarks):
    """
    Eye Aspect Ratio — measures how open the eyes are.
    EAR < 0.20 means eyes are closed (blink or drowsy).
    Formula: vertical distance / horizontal distance of eye landmarks.
    """
    def eye_aspect_ratio(top_bottom_ids, left_right_ids):
        top    = face_landmarks.landmark[top_bottom_ids[0]]
        bottom = face_landmarks.landmark[top_bottom_ids[1]]
        left   = face_landmarks.landmark[left_right_ids[0]]
        right  = face_landmarks.landmark[left_right_ids[1]]

        vertical   = abs(top.y - bottom.y)
        horizontal = abs(left.x - right.x)

        if horizontal == 0:
            return 0.3
        return vertical / horizontal

    left_ear  = eye_aspect_ratio(LEFT_EYE_TOP_BOTTOM,  LEFT_EYE_LEFT_RIGHT)
    right_ear = eye_aspect_ratio(RIGHT_EYE_TOP_BOTTOM, RIGHT_EYE_LEFT_RIGHT)
    return (left_ear + right_ear) / 2


def get_eye_state(face_landmarks):
    """
    Returns eye state based on EAR value.
    OPEN = paying attention
    CLOSED = drowsy or blinking
    """
    ear = get_ear(face_landmarks)
    if ear < 0.20:
        return "CLOSED", ear
    else:
        return "OPEN", ear

def get_face_distance_ratio(face_landmarks):
    """
    Measures the distance between the far left and far right eye corners.
    Returns the ratio relative to the frame width (since landmark.x is normalized 0-1).
    A high ratio means the user is leaning very close to the screen.
    """
    left_corner = face_landmarks.landmark[LEFT_EYE_CORNERS[0]]
    right_corner = face_landmarks.landmark[RIGHT_EYE_CORNERS[0]]
    distance_ratio = abs(left_corner.x - right_corner.x)
    return distance_ratio