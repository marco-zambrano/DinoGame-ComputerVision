# Skeleton Runner / CYBER-RUN

Single-window Python game controlled by body pose via webcam.

## Entrypoints & Structure

- `main.py` — Pygame loop, camera init, 3-state machine: `INTRO` → `CALIBRATING` → `PLAYING`
- `pose_detector.py` — MediaPipe pose, calibration baseline, jump/duck detection
- `game.py` — Runner state, rendering, obstacles, collisions, score, cyberpunk visuals
- `config.py` — All tunable constants: camera, pose thresholds, physics, colors
- `models/pose_landmarker_lite.task` — MediaPipe model (required, not auto-downloaded)
- `assets/dino/*.png` — Optional sprites; if missing, fallback to procedural pixel-art (no error)

## MediaPipe Quirk (key gotcha)

Python 3.13+ **lacks** `mp.solutions`. On 3.13 the code falls through to the MediaPipe Tasks API (`pose_landmarker.PoseLandmarker`) which requires `models/pose_landmarker_lite.task` on disk. On older Python the `solutions` path is used instead. Both paths work — the code detects at import time via `hasattr(mp, "solutions")`.

If the model file is missing the app raises `FileNotFoundError` pointing to the download URL in `config.POSE_MODEL_URL`.

## Commands

```powershell
.\.venv\Scripts\Activate.ps1         # activate venv
python -m pip install -r requirements.txt
python main.py                        # run game (requires webcam)
python -m py_compile main.py game.py pose_detector.py config.py  # syntax check
```

No test framework, CI, or codegen is configured.

## Conventions

- `UPPER_SNAKE_CASE` for constants (in `config.py`), `snake_case` for functions/vars, descriptive class names
- 4-space indentation, standard Python style
- All tuning values in `config.py` — no magic numbers in game/detection logic
- `config.py` has extensive inline tuning comments (jump sensitivity, duck thresholds, smoothing); edit there first before touching detection logic

## Testing

- Syntax check with `py_compile` (above)
- Pose changes must be verified manually with a camera — thresholds depend on lighting, distance, person height
- Rendering-only changes: run the game and visually check

## Config Tips

- After moving to a new room/event: recalibrate in-app, then tweak thresholds in `config.py`
- Camera index → `config.CAMERA_INDEX`
- Model file at `models/pose_landmarker_lite.task` — keep it present to avoid download failures
- Score goal: `GOAL_SCORE = 250` to win (victory screen)
