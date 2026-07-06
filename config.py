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

# Calibracion
CALIBRATION_SECONDS = 3.0
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
DINO_WIDTH = 52
DINO_HEIGHT = 76
DINO_DUCK_WIDTH = 74
DINO_DUCK_HEIGHT = 44
GRAVITY = 2400.0
JUMP_VELOCITY = -920.0
START_SPEED = 430.0
MAX_SPEED = 920.0
SPEED_GAIN_PER_SECOND = 7.0
OBSTACLE_MIN_GAP = 440
OBSTACLE_MAX_GAP = 760
SCORE_RATE = 11.0
