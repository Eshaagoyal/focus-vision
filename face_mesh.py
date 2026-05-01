import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def create_face_mesh():
    """
    Creates and returns a MediaPipe FaceMesh instance.
    refine_landmarks=True unlocks iris landmarks (468-477)
    which we need for gaze detection later.
    """
    return mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

def draw_mesh(frame, face_landmarks):
    """
    Draws the face mesh tesselation on the frame.
    Only called when a face is detected.
    """
    mp_drawing.draw_landmarks(
        image=frame,
        landmark_list=face_landmarks,
        connections=mp_face_mesh.FACEMESH_TESSELATION,
        landmark_drawing_spec=None,
        connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
    )