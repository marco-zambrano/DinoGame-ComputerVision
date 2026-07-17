from collections import deque
from dataclasses import dataclass
from pathlib import Path
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
        self.using_solutions = hasattr(mp, "solutions")
        if self.using_solutions:
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.pose = self.mp_pose.Pose(
                model_complexity=1,
                min_detection_confidence=0.55,
                min_tracking_confidence=0.55,
                smooth_landmarks=True,
            )
            self.connections = self.mp_pose.POSE_CONNECTIONS
        else:
            from mediapipe.tasks.python.core import base_options
            from mediapipe.tasks.python.vision import pose_landmarker
            from mediapipe.tasks.python.vision.core import vision_task_running_mode

            model_path = Path(config.POSE_MODEL_PATH)
            if not model_path.exists():
                raise FileNotFoundError(
                    f"No existe {config.POSE_MODEL_PATH}. Descargalo desde {config.POSE_MODEL_URL}"
                )
            options = pose_landmarker.PoseLandmarkerOptions(
                base_options=base_options.BaseOptions(model_asset_path=str(model_path)),
                running_mode=vision_task_running_mode.VisionTaskRunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=0.55,
                min_pose_presence_confidence=0.55,
                min_tracking_confidence=0.55,
            )
            self.pose = pose_landmarker.PoseLandmarker.create_from_options(options)
            self.connections = [(c.start, c.end) for c in pose_landmarker.PoseLandmarksConnections.POSE_LANDMARKS]
        self.baseline = None
        self.calibration_start = None
        self.calibration_samples = []
        self.hip_history = deque(maxlen=config.JUMP_LOOKBACK_FRAMES)
        self.torso_history = deque(maxlen=config.POSE_SMOOTHING_FRAMES)
        self.shoulder_history = deque(maxlen=config.POSE_SMOOTHING_FRAMES)
        self.knee_history = deque(maxlen=config.POSE_SMOOTHING_FRAMES)
        self.last_jump_ms = -99999
        self.armed_at_ms = None
        self.last_results = None

    def close(self):
        self.pose.close()

    def reset_calibration(self):
        self.baseline = None
        self.calibration_start = None
        self.calibration_samples = []
        self.hip_history.clear()
        self.torso_history.clear()
        self.shoulder_history.clear()
        self.knee_history.clear()
        self.armed_at_ms = None

    def process(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        if self.using_solutions:
            rgb.flags.writeable = False
            results = self.pose.process(rgb)
        else:
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            results = self.pose.detect(image)
        self.last_results = results

        metrics = self._metrics(self._landmarks_from_results(results))
        if self.baseline is None:
            return self._calibrate(metrics)

        if metrics is None:
            self.hip_history.clear()
            self.torso_history.clear()
            self.shoulder_history.clear()
            self.knee_history.clear()
            self.armed_at_ms = None
            return PoseState(label="SIN POSE", calibrated=True)

        now_ms = int(time.time() * 1000)
        if self.armed_at_ms is None:
            self.armed_at_ms = now_ms
        self.hip_history.append(metrics["hip_y"])
        self.torso_history.append(metrics["torso"])
        self.shoulder_history.append(metrics["shoulder_y"])
        self.knee_history.append(metrics["knee_y"])

        avg_torso = float(np.mean(self.torso_history))
        avg_shoulder = float(np.mean(self.shoulder_history))
        avg_knee = float(np.mean(self.knee_history))

        torso_reduction = 1.0 - (avg_torso / self.baseline["torso"])
        shoulder_drop = (avg_shoulder - self.baseline["shoulder_y"]) / self.baseline["height"]
        hip_drop = (metrics["hip_y"] - self.baseline["hip_y"]) / self.baseline["height"]
        knee_motion = abs(avg_knee - self.baseline["knee_y"]) / self.baseline["height"]
        ducking = (
            torso_reduction >= config.DUCK_TORSO_REDUCTION_RATIO
            or hip_drop >= config.DUCK_HIP_DROP_RATIO
            or (
                shoulder_drop >= config.DUCK_SHOULDER_DROP_RATIO
                and knee_motion <= config.DUCK_KNEE_STABILITY_RATIO
            )
        )

        jump_event = False
        armed = now_ms - self.armed_at_ms >= config.JUMP_ARMING_MS
        if len(self.hip_history) == self.hip_history.maxlen and armed and not ducking:
            hip_delta = self.hip_history[-1] - self.hip_history[0]
            rise_ratio = -hip_delta / self.baseline["height"]
            velocity_ratio = -(self.hip_history[-1] - self.hip_history[-2]) / self.baseline["height"]
            above_baseline = (self.baseline["hip_y"] - self.hip_history[-1]) / self.baseline["height"]
            cooled_down = now_ms - self.last_jump_ms >= config.JUMP_COOLDOWN_MS
            if (
                cooled_down
                and rise_ratio >= config.JUMP_MIN_RISE_RATIO
                and velocity_ratio >= config.JUMP_MIN_UPWARD_VELOCITY_RATIO
                and above_baseline >= config.JUMP_MIN_ABOVE_BASELINE_RATIO
            ):
                jump_event = True
                self.last_jump_ms = now_ms

        label = "SALTANDO" if jump_event else "AGACHADO" if ducking else "DE PIE"
        return PoseState(jump_event=jump_event, ducking=ducking, label=label, calibrated=True)

    def draw_overlay(self, frame_bgr, state):
        image = frame_bgr.copy()
        landmarks = self._landmarks_from_results(self.last_results)
        if self.using_solutions and self.last_results and self.last_results.pose_landmarks:
            specs = self.mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=3)
            conn = self.mp_drawing.DrawingSpec(color=(255, 80, 0), thickness=2)
            self.mp_drawing.draw_landmarks(
                image,
                self.last_results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=specs,
                connection_drawing_spec=conn,
            )
        elif landmarks:
            h, w = image.shape[:2]
            for start, end in self.connections:
                a = landmarks[start]
                b = landmarks[end]
                if self._visible(a) and self._visible(b):
                    cv2.line(image, (int(a.x * w), int(a.y * h)), (int(b.x * w), int(b.y * h)), (255, 80, 0), 2)
            for lm in landmarks:
                if self._visible(lm):
                    cv2.circle(image, (int(lm.x * w), int(lm.y * h)), 4, (0, 255, 255), -1)
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
        enough_samples = len(self.calibration_samples) >= config.CALIBRATION_MIN_SAMPLES
        if elapsed >= config.CALIBRATION_SECONDS and enough_samples:
            self.baseline = {
                "shoulder_y": float(np.mean([m["shoulder_y"] for m in self.calibration_samples])),
                "hip_y": float(np.mean([m["hip_y"] for m in self.calibration_samples])),
                "knee_y": float(np.mean([m["knee_y"] for m in self.calibration_samples])),
                "torso": float(np.mean([m["torso"] for m in self.calibration_samples])),
                "height": float(np.mean([m["height"] for m in self.calibration_samples])),
            }
            self.hip_history.clear()
            self.torso_history.clear()
            self.shoulder_history.clear()
            self.knee_history.clear()
            self.armed_at_ms = int(time.time() * 1000)
            return PoseState(label="DE PIE", calibrated=True)

        if not self.calibration_samples:
            return PoseState(label="BUSCANDO POSE", calibrated=False)
        if not enough_samples:
            return PoseState(label="QUEDATE QUIETO", calibrated=False)
        return PoseState(label=f"CALIBRANDO {int(np.ceil(remaining))}", calibrated=False)

    def _metrics(self, landmarks):
        if not landmarks:
            return None

        lm = landmarks.landmark if hasattr(landmarks, "landmark") else landmarks
        needed = [11, 12, 23, 24, 25, 26, 27, 28]
        if any(not self._visible(lm[i]) for i in needed):
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

    def _landmarks_from_results(self, results):
        if not results:
            return None
        if self.using_solutions:
            return results.pose_landmarks
        if results.pose_landmarks:
            return results.pose_landmarks[0]
        return None

    def _visible(self, landmark):
        visibility = getattr(landmark, "visibility", None)
        presence = getattr(landmark, "presence", None)
        if visibility is not None and visibility < config.MIN_VISIBILITY:
            return False
        if presence is not None and presence < config.MIN_VISIBILITY:
            return False
        return True
