# CYBER-RUN / Skeleton Runner

Juego de correr infinito controlado por tu cuerpo mediante la cámara web. Saltá y agachate en la vida real para esquivar obstáculos en una estética cyberpunk.

## Requisitos

- Python 3.10 o superior
- Cámara web
- Archivo de modelo MediaPipe (`models/pose_landmarker_lite.task`)

## Instalación

```powershell
# 1. Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Instalar dependencias
python -m pip install -r requirements.txt

# 3. Descargar el modelo de pose (solo si usás Python 3.13+)
#    El juego te va a avisar si falta y darte el link.
#    Generalmente se descarga automáticamente o podés
#    bajarlo de:
#    https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
#    Y guardarlo en models/pose_landmarker_lite.task
```

## Cómo ejecutar

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

## Cómo se juega

### 1. Ingresá tu nombre
Te aparece un cuadro para escribir tu nombre. Se guarda tu mejor puntaje en una base de datos local. Si el nombre ya existe, podés continuar con ese jugador o elegir otro.

### 2. Pantalla de inicio
Te explica los pasos:
1. Parate frente a la cámara
2. Mantenete visible de hombros a pies
3. Saltá para saltar en el juego
4. Agachate para esquivar obstáculos altos
5. Después de unos segundos empieza la calibración

Presioná **ESPACIO** para empezar la calibración antes.

### 3. Calibración
Parate derecho y quieto frente a la cámara. El juego mide la posición de tus hombros, cadera y rodillas para establecer una línea base. Dura 3 segundos.

### 4. A jugar
Corrés automáticamente. Controlás al dinosaurio con tu cuerpo:

| Acción real | Acción en el juego |
|---|---|
| Saltar | El dinosaurio salta |
| Agacharte (doblando el torso) | El dinosaurio se agacha |
| Pararte derecho | Sigue corriendo |

### Controles de teclado (alternativa)

| Tecla | Acción |
|---|---|
| ESPACIO / ↑ | Saltar / Empezar / Reiniciar |
| L | Ver leaderboard (en pantalla de inicio o Game Over) |
| N | Cambiar de jugador |
| ESC / Q | Salir del juego |

### Obstáculos

- **Cactus** (verde neón) — hay que saltarlos
- **Computadora** (gris/verde) — hay que saltarla
- **Dron bajo** — hay que saltarlo
- **Dron alto** — hay que agacharse

### Puntaje y fin del juego

- El puntaje aumenta con el tiempo y la velocidad
- Llegar a **250 puntos** = victoria (META SUPERADA)
- Si chocás un obstáculo es GAME OVER
- Tu mejor puntaje por jugador se guarda automáticamente

## Estructura del proyecto

| Archivo | Qué hace |
|---|---|
| `main.py` | Bucle principal del juego, cámaras, estados (INTRO → CALIBRACIÓN → JUGANDO) |
| `game.py` | Lógica del juego: runner, obstáculos, colisiones, puntaje, dibujado |
| `pose_detector.py` | Detección de pose con MediaPipe, calibración, detección de salto/agacharse |
| `leaderboard.py` | Base de datos SQLite con los mejores puntajes por jugador |
| `config.py` | Todos los valores ajustables: cámara, umbrales de pose, física, colores |
| `assets/dino/*.png` | Sprites opcionales (si no existen, se dibuja el dinosaurio con código) |
| `models/pose_landmarker_lite.task` | Modelo de MediaPipe para detección de pose |

## Configuración

Todos los valores ajustables están en `config.py`:

- **Cámara**: `CAMERA_INDEX` (si tenés más de una cámara)
- **Sensibilidad de salto**: `JUMP_MIN_RISE_RATIO`, `JUMP_MIN_UPWARD_VELOCITY_RATIO`
- **Sensibilidad de agacharse**: `DUCK_TORSO_REDUCTION_RATIO`, `DUCK_SHOULDER_DROP_RATIO`
- **Velocidad del juego**: `START_SPEED`, `MAX_SPEED`, `SPEED_GAIN_PER_SECOND`
- **Meta**: `GOAL_SCORE = 250`

Si el juego no detecta bien tus movimientos, ajustá esos valores antes de tocar el código de detección.

## Solución de problemas

- **"No se pudo abrir la cámara"**: cambiá `CAMERA_INDEX` en `config.py` (probá 0, 1, 2...)
- **No detecta saltos**: bajá `JUMP_MIN_RISE_RATIO` o `JUMP_MIN_UPWARD_VELOCITY_RATIO`
- **Falsos saltos al caminar**: subí `JUMP_COOLDOWN_MS` o los umbrales anteriores
- **No se agacha**: bajá `DUCK_TORSO_REDUCTION_RATIO` o `DUCK_SHOULDER_DROP_RATIO`
- **Error de modelo faltante**: descargá `pose_landmarker_lite.task` desde la URL en `config.POSE_MODEL_URL` y guardalo en `models/`
