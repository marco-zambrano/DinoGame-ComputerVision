from collections import deque
from dataclasses import dataclass
import time

import cv2
import mediapipe as mp
import numpy as np

import config


@dataclass
class PoseState:
    jump_event: bool = False
    ducking: bool = False
    label: str = "SIN POSE"
    calibrated: bool = False


class PoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            model_complexity=1,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.55,
            smooth_landmarks=True,
        )
        self.baseline = None
        self.calibration_start = None
        self.calibration_samples = []
        self.hip_history = deque(maxlen=config.JUMP_LOOKBACK_FRAMES)
        self.torso_history = deque(maxlen=config.POSE_SMOOTHING_FRAMES)
        self.shoulder_history = deque(maxlen=config.POSE_SMOOTHING_FRAMES)
        self.knee_history = deque(maxlen=config.POSE_SMOOTHING_FRAMES)
        self.last_jump_ms = -99999
        self.last_results = None

    def close(self):
        self.pose.close()

    def process(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.pose.process(rgb)
        self.last_results = results

        metrics = self._metrics(results.pose_landmarks)
        if self.baseline is None:
            return self._calibrate(metrics)

        if metrics is None:
            return PoseState(label="SIN POSE", calibrated=True)

        now_ms = int(time.time() * 1000)
        self.hip_history.append(metrics["hip_y"])
        self.torso_history.append(metrics["torso"])
        self.shoulder_history.append(metrics["shoulder_y"])
        self.knee_history.append(metrics["knee_y"])

        avg_torso = float(np.mean(self.torso_history))
        avg_shoulder = float(np.mean(self.shoulder_history))
        avg_knee = float(np.mean(self.knee_history))

        torso_reduction = 1.0 - (avg_torso / self.baseline["torso"])
        shoulder_drop = (avg_shoulder - self.baseline["shoulder_y"]) / self.baseline["height"]
        knee_motion = abs(avg_knee - self.baseline["knee_y"]) / self.baseline["height"]
        ducking = (
            torso_reduction >= config.DUCK_TORSO_REDUCTION_RATIO
            or (
                shoulder_drop >= config.DUCK_SHOULDER_DROP_RATIO
                and knee_motion <= config.DUCK_KNEE_STABILITY_RATIO
            )
        )

        jump_event = False
        if len(self.hip_history) >= 2 and not ducking:
            hip_delta = self.hip_history[-1] - self.hip_history[0]
            rise_ratio = -hip_delta / self.baseline["height"]
            velocity_ratio = -(self.hip_history[-1] - self.hip_history[-2]) / self.baseline["height"]
            cooled_down = now_ms - self.last_jump_ms >= config.JUMP_COOLDOWN_MS
            if (
                cooled_down
                and rise_ratio >= config.JUMP_MIN_RISE_RATIO
                and velocity_ratio >= config.JUMP_MIN_UPWARD_VELOCITY_RATIO
            ):
                jump_event = True
                self.last_jump_ms = now_ms

        label = "SALTANDO" if jump_event else "AGACHADO" if ducking else "DE PIE"
        return PoseState(jump_event=jump_event, ducking=ducking, label=label, calibrated=True)

    def draw_overlay(self, frame_bgr, state):
        image = frame_bgr.copy()
        if self.last_results and self.last_results.pose_landmarks:
            specs = self.mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=3)
            conn = self.mp_drawing.DrawingSpec(color=(255, 80, 0), thickness=2)
            self.mp_drawing.draw_landmarks(
                image,
                self.last_results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=specs,
                connection_drawing_spec=conn,
            )
        color = (0, 220, 255) if state.label == "SALTANDO" else (255, 180, 0) if state.label == "AGACHADO" else (0, 255, 90)
        cv2.rectangle(image, (8, 8), (190, 48), (20, 20, 20), -1)
        cv2.putText(image, state.label, (18, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
        return image

    def _calibrate(self, metrics):
        if self.calibration_start is None:
            self.calibration_start = time.time()

        if metrics is not None:
            self.calibration_samples.append(metrics)

        elapsed = time.time() - self.calibration_start
        remaining = max(0.0, config.CALIBRATION_SECONDS - elapsed)
        if elapsed >= config.CALIBRATION_SECONDS and self.calibration_samples:
            self.baseline = {
                "shoulder_y": float(np.mean([m["shoulder_y"] for m in self.calibration_samples])),
                "hip_y": float(np.mean([m["hip_y"] for m in self.calibration_samples])),
                "knee_y": float(np.mean([m["knee_y"] for m in self.calibration_samples])),
                "torso": float(np.mean([m["torso"] for m in self.calibration_samples])),
                "height": float(np.mean([m["height"] for m in self.calibration_samples])),
            }
            return PoseState(label="DE PIE", calibrated=True)

        return PoseState(label=f"CALIBRANDO {int(np.ceil(remaining))}", calibrated=False)

    def _metrics(self, landmarks):
        if not landmarks:
            return None

        lm = landmarks.landmark
        needed = [11, 12, 23, 24, 25, 26, 27, 28]
        if any(lm[i].visibility < config.MIN_VISIBILITY for i in needed):
            return None

        shoulder_y = (lm[11].y + lm[12].y) / 2
        hip_y = (lm[23].y + lm[24].y) / 2
        knee_y = (lm[25].y + lm[26].y) / 2
        ankle_y = (lm[27].y + lm[28].y) / 2
        torso = abs(hip_y - shoulder_y)
        height = max(0.001, ankle_y - shoulder_y)
        return {
            "shoulder_y": shoulder_y,
            "hip_y": hip_y,
            "knee_y": knee_y,
            "torso": torso,
            "height": height,
        }
