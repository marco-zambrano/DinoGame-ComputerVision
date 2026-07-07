"""Configuracion central de Skeleton Runner.

Ajusta estos valores en sitio si la deteccion cambia con otra camara,
distancia, iluminacion o tipo de participante. La calibracion inicial toma
una linea base por persona, asi que normalmente solo se tocan los umbrales
cuando hay falsos positivos o gestos que no entran.
"""

# Ventana y loop
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 30
GAME_AREA_WIDTH = WINDOW_WIDTH
GAME_AREA_HEIGHT = WINDOW_HEIGHT

# Camara
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_PREVIEW_WIDTH = 320
CAMERA_PREVIEW_HEIGHT = 240
CAMERA_MARGIN = 18

# MediaPipe Tasks (Python 3.13+) no incluye el modelo de pose dentro del
# paquete. Este archivo se descarga una vez y queda local para correr offline.
POSE_MODEL_PATH = "models/pose_landmarker_lite.task"
POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"

# Calibracion
CALIBRATION_SECONDS = 3.0
INTRO_SECONDS = 7.0
MIN_VISIBILITY = 0.55

# Suavizado de pose. Subir a 5-7 si hay jitter; bajar a 2-3 si se siente lento.
POSE_SMOOTHING_FRAMES = 4

# Salto:
# - Si no detecta saltos reales, baja JUMP_MIN_UPWARD_VELOCITY_RATIO o
#   JUMP_MIN_RISE_RATIO.
# - Si dispara saltos al moverse normal, sube esos valores o el cooldown.
JUMP_LOOKBACK_FRAMES = 5
JUMP_MIN_RISE_RATIO = 0.045
JUMP_MIN_UPWARD_VELOCITY_RATIO = 0.018
JUMP_COOLDOWN_MS = 450

# Agacharse:
# - Si no detecta agacharse, baja DUCK_TORSO_REDUCTION_RATIO o
#   DUCK_SHOULDER_DROP_RATIO.
# - Si confunde salto con agacharse, sube DUCK_KNEE_STABILITY_RATIO.
DUCK_TORSO_REDUCTION_RATIO = 0.25
DUCK_SHOULDER_DROP_RATIO = 0.13
DUCK_KNEE_STABILITY_RATIO = 0.08

# Juego
GROUND_Y = 600
DINO_X = 110
DINO_WIDTH = 72
DINO_HEIGHT = 78
DINO_DUCK_WIDTH = 96
DINO_DUCK_HEIGHT = 45
GRAVITY = 2400.0
JUMP_VELOCITY = -920.0
START_SPEED = 430.0
MAX_SPEED = 920.0
SPEED_GAIN_PER_SECOND = 7.0
OBSTACLE_MIN_GAP = 440
OBSTACLE_MAX_GAP = 760
SCORE_RATE = 11.0

# Tema visual CYBER-RUN. Cambia estos tonos para rebrandear el escenario sin
# tocar la logica del juego ni la deteccion de pose.
CYBER_BG_TOP = (30, 78, 78)
CYBER_BG_MID = (54, 73, 92)
CYBER_BG_BOTTOM = (91, 58, 102)
CYBER_DATA_RAIN = (245, 255, 255, 38)
CYBER_CLOUD = (200, 220, 235)
CYBER_CLOUD_HIGHLIGHT = (255, 255, 255)
CYBER_CLOUD_GLOW = (170, 235, 255)
CIRCUIT_PANEL_COLOR = (46, 42, 74)
CIRCUIT_PANEL_ALT = (38, 36, 67)
CIRCUIT_LINE = (77, 255, 255)
CIRCUIT_MAGENTA = (255, 78, 210)
CIRCUIT_GREEN = (57, 255, 136)
NEON_CYAN = (46, 255, 209)
NEON_GREEN = (57, 255, 136)
NEON_DINO = (48, 255, 170)
NEON_DINO_CORE = (182, 255, 220)
HUD_TEXT = (218, 255, 255)
RETRO_WINDOW = (29, 32, 43)
RETRO_WINDOW_BORDER = (78, 255, 255)
CRT_BODY = (95, 112, 130)
CRT_DARK = (28, 35, 48)
CRT_SCREEN = (70, 255, 140)
