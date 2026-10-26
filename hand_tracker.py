import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision


HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
)

PEACE_ON_FRAMES = 2
PEACE_OFF_FRAMES = 3
SMOOTHING = 0.4


@dataclass
class HandState:
    center: tuple[int, int]
    center_norm: tuple[float, float]
    landmarks: list[tuple[int, int]]
    landmarks_norm: list[tuple[float, float]]
    fingers_up: tuple[bool, bool, bool, bool, bool]
    is_peace: bool
    handedness: str


def _angle(a, b, c):
    ba = np.array(a, dtype=np.float32) - np.array(b, dtype=np.float32)
    bc = np.array(c, dtype=np.float32) - np.array(b, dtype=np.float32)
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom == 0:
        return 0.0
    cos_value = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_value)))


def _finger_extended(points, mcp, pip, tip):
    mcp_p = points[mcp]
    pip_p = points[pip]
    tip_p = points[tip]
    wrist = points[0]
    if np.linalg.norm(np.array(tip_p) - np.array(wrist)) <= np.linalg.norm(np.array(pip_p) - np.array(wrist)):
        return False
    return _angle(mcp_p, pip_p, tip_p) > 130.0


def _fingers_up(points):
    index = _finger_extended(points, 5, 6, 8)
    middle = _finger_extended(points, 9, 10, 12)
    ring = _finger_extended(points, 13, 14, 16)
    pinky = _finger_extended(points, 17, 18, 20)
    thumb = _angle(points[2], points[3], points[4]) > 140.0 and np.linalg.norm(
        np.array(points[4]) - np.array(points[17])
    ) > np.linalg.norm(np.array(points[2]) - np.array(points[17])) * 1.05
    return thumb, index, middle, ring, pinky


def _is_peace(points, fingers_up):
    thumb, index, middle, ring, pinky = fingers_up
    if not (index and middle and not ring and not pinky):
        return False
    palm_width = np.linalg.norm(np.array(points[5]) - np.array(points[17]))
    tip_distance = np.linalg.norm(np.array(points[8]) - np.array(points[12]))
    if palm_width == 0:
        return False
    return tip_distance > palm_width * 0.5


class HandTracker:
    def __init__(self, model_path=None, max_hands=1):
        if model_path is None:
            model_path = Path(__file__).with_name("hand_landmarker.task")
        self.model_path = str(model_path)
        base_options = mp_python.BaseOptions(model_asset_path=self.model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self._timestamp_ms = 0
        self._peace = False
        self._peace_on_count = 0
        self._peace_off_count = 0
        self._smooth_center = None
        self._last_state = None

    def _next_timestamp(self):
        now = int(time.perf_counter() * 1000)
        self._timestamp_ms = max(self._timestamp_ms + 1, now)
        return self._timestamp_ms

    def process(self, frame, draw=True):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.detector.detect_for_video(mp_image, self._next_timestamp())

        if not result.hand_landmarks:
            self._update_peace(False)
            self._last_state = None
            return None

        h, w = frame.shape[:2]
        hand = result.hand_landmarks[0]
        landmarks_norm = [(float(lm.x), float(lm.y)) for lm in hand]
        landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in hand]
        points = [np.array(p, dtype=np.float32) for p in landmarks]

        fingers_up = _fingers_up(points)
        is_peace_now = _is_peace(points, fingers_up)
        self._update_peace(is_peace_now)

        palm_x = int(np.mean([landmarks[i][0] for i in (0, 5, 9, 13, 17)]))
        palm_y = int(np.mean([landmarks[i][1] for i in (0, 5, 9, 13, 17)]))
        if self._smooth_center is None:
            self._smooth_center = (float(palm_x), float(palm_y))
        else:
            sx, sy = self._smooth_center
            self._smooth_center = (
                sx + (palm_x - sx) * SMOOTHING,
                sy + (palm_y - sy) * SMOOTHING,
            )
        center = (int(self._smooth_center[0]), int(self._smooth_center[1]))
        center_norm = (center[0] / w, center[1] / h)

        handedness = "Unknown"
        if result.handedness and result.handedness[0]:
            handedness = result.handedness[0][0].category_name

        state = HandState(
            center=center,
            center_norm=center_norm,
            landmarks=landmarks,
            landmarks_norm=landmarks_norm,
            fingers_up=fingers_up,
            is_peace=self._peace,
            handedness=handedness,
        )
        self._last_state = state

        if draw:
            self.draw(frame, state)
        return state

    def _update_peace(self, is_peace_now):
        if is_peace_now:
            self._peace_on_count += 1
            self._peace_off_count = 0
            if self._peace_on_count >= PEACE_ON_FRAMES:
                self._peace = True
        else:
            self._peace_off_count += 1
            self._peace_on_count = 0
            if self._peace_off_count >= PEACE_OFF_FRAMES:
                self._peace = False

    def draw(self, frame, state):
        color = (60, 255, 120) if state.is_peace else (235, 235, 235)
        points = state.landmarks
        for start, end in HAND_CONNECTIONS:
            cv2.line(frame, points[start], points[end], color, 2, cv2.LINE_AA)
        for point in points:
            cv2.circle(frame, point, 3, (255, 0, 200), -1, cv2.LINE_AA)
        x, y = state.center
        cv2.circle(frame, (x, y), 7, (0, 200, 255), -1, cv2.LINE_AA)
        label = "PEACE" if state.is_peace else "HAND"
        cv2.putText(
            frame, label, (max(5, x - 30), max(20, y - 18)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA,
        )

    def close(self):
        self.detector.close()


def draw_hand_on_panel(canvas, state, x, y, w, h):
    if state is None:
        cv2.putText(
            canvas, "Tangan tidak terdeteksi", (x + 8, y + h - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 130), 1, cv2.LINE_AA,
        )
        return
    color = (60, 255, 120) if state.is_peace else (235, 235, 235)
    for start, end in HAND_CONNECTIONS:
        p1 = (x + int(state.landmarks_norm[start][0] * w), y + int(state.landmarks_norm[start][1] * h))
        p2 = (x + int(state.landmarks_norm[end][0] * w), y + int(state.landmarks_norm[end][1] * h))
        cv2.line(canvas, p1, p2, color, 1, cv2.LINE_AA)
    for px, py in state.landmarks_norm:
        cv2.circle(canvas, (x + int(px * w), y + int(py * h)), 2, (255, 0, 200), -1, cv2.LINE_AA)
