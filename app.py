from flask import Flask, render_template, request, jsonify
import cv2
import mediapipe as mp
import numpy as np
from scipy.spatial import distance as dist
import base64
import socket

app = Flask(__name__)

# MediaPipe setup
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Corrected Eye indices from MediaPipe FaceMesh (468 landmarks)
# Left eye landmarks (indices)
LEFT_EYE = [362, 385, 387, 263, 373, 380]
# Right eye landmarks (indices)
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

EAR_THRESHOLD = 0.22  # Adjust this threshold as needed
FRAME_COUNT = 0
IS_DROWSY = False
EAR_VALUE = 0.0


def eye_aspect_ratio(eye):
    # Compute the euclidean distances between the two sets of
    # vertical eye landmarks (x, y)-coordinates
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])

    # Compute the euclidean distance between the horizontal
    # eye landmark (x, y)-coordinates
    C = dist.euclidean(eye[0], eye[3])

    # Compute the eye aspect ratio
    ear = (A + B) / (2.0 * C)

    # Return the eye aspect ratio
    return ear


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process_frame', methods=['POST'])
def process_frame():
    global FRAME_COUNT, IS_DROWSY, EAR_VALUE

    try:
        data_url = request.json['image']
        header, encoded = data_url.split(",", 1)
        img_bytes = np.frombuffer(base64.b64decode(encoded), dtype=np.uint8)
        frame = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        IS_DROWSY = False
        EAR_VALUE = 0.0

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = np.array([(lm.x * w, lm.y * h)
                                      for lm in face_landmarks.landmark])

                left_eye_pts = landmarks[LEFT_EYE]
                right_eye_pts = landmarks[RIGHT_EYE]

                left_ear = eye_aspect_ratio(left_eye_pts)
                right_ear = eye_aspect_ratio(right_eye_pts)
                EAR_VALUE = (left_ear + right_ear) / 2.0

                print(
                    f"Left EAR: {left_ear:.3f}, Right EAR: {right_ear:.3f}, Average EAR: {EAR_VALUE:.3f}")

                if EAR_VALUE < EAR_THRESHOLD:
                    FRAME_COUNT += 1
                    if FRAME_COUNT >= 10:  # If eyes are closed for 10 consecutive frames
                        IS_DROWSY = True
                else:
                    FRAME_COUNT = 0
                    IS_DROWSY = False

        return jsonify({
            'is_drowsy': IS_DROWSY,
            'ear': round(EAR_VALUE, 3)
        })

    except Exception as e:
        print("Error processing frame:", str(e))
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    host_ip4 = socket.gethostbyname(socket.gethostname())
    print(f"🟢 Access app at: http://{host_ip4}:5000")
    app.run(port=5000, debug=True)
