# Repository Guidelines

## Project Structure & Module Organization

This repository contains a single-window Python game, **Skeleton Runner / CYBER-RUN**.

- `main.py`: application entry point, Pygame loop, camera setup, intro screen, calibration flow, and integration between pose input and gameplay.
- `pose_detector.py`: MediaPipe Pose / Tasks integration, calibration baseline, jump and duck detection.
- `game.py`: runner game state, drawing, obstacles, collisions, score, and CYBER-RUN visual theme.
- `config.py`: tunable constants for camera, pose thresholds, gameplay, and visual colors.
- `models/`: local MediaPipe model assets, including `pose_landmarker_lite.task`.
- `requirements.txt`: Python dependencies.

There is currently no dedicated `tests/` directory.

## Build, Test, and Development Commands

Create and activate the virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the game:

```powershell
python main.py
```

Check syntax before committing:

```powershell
python -m py_compile main.py game.py pose_detector.py config.py
```

## Coding Style & Naming Conventions

Use standard Python style with 4-space indentation. Keep modules focused: pose logic belongs in `pose_detector.py`, game and rendering logic in `game.py`, and tunable values in `config.py`. Use `UPPER_SNAKE_CASE` for constants, `snake_case` for functions and variables, and descriptive class names such as `PoseDetector` or `Game`.

Prefer clear constants in `config.py` over magic numbers in rendering or detection code.

## Testing Guidelines

No formal test suite is configured yet. At minimum, run `py_compile` after edits. For rendering-only changes, use a dummy Pygame smoke test when possible. For pose changes, verify manually with the camera because thresholds depend on lighting, distance, and participant height.

## Commit & Pull Request Guidelines

Git history uses short, imperative commit messages, for example:

- `Add intro screen before calibration`
- `Redesign runner with cyberpunk visuals`
- `Support MediaPipe Tasks pose detection`

Keep commits scoped to one concern. Pull requests should include a concise summary, manual test steps, screenshots or short video for visual changes, and notes about any changed pose thresholds or calibration behavior.

## Configuration Tips

When moving to a new room or event, adjust detection thresholds in `config.py` only after recalibrating in-app. If the camera index changes, update `CAMERA_INDEX`. Keep `models/pose_landmarker_lite.task` available so the app can run without downloading a model at startup.
