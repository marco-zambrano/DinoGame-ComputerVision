import sys

import cv2
import pygame

import config
from game import Game
from pose_detector import PoseDetector, PoseState


def camera_to_surface(frame_bgr):
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    frame_rgb = cv2.resize(frame_rgb, (config.CAMERA_PREVIEW_WIDTH, config.CAMERA_PREVIEW_HEIGHT))
    return pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))


def draw_camera_preview(screen, frame_bgr, state, detector, font):
    overlay = detector.draw_overlay(frame_bgr, state)
    preview = camera_to_surface(overlay)
    x = config.WINDOW_WIDTH - config.CAMERA_PREVIEW_WIDTH - config.CAMERA_MARGIN
    y = 64
    pygame.draw.rect(screen, (20, 20, 20), (x - 4, y - 4, config.CAMERA_PREVIEW_WIDTH + 8, config.CAMERA_PREVIEW_HEIGHT + 8), border_radius=6)
    screen.blit(preview, (x, y))
    if not state.calibrated:
        label = font.render("Parate derecho frente a la camara", True, (45, 45, 45))
        screen.blit(label, label.get_rect(center=(config.WINDOW_WIDTH // 2, 400)))


def draw_calibration(screen, state, big_font):
    shade = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
    shade.fill((255, 255, 255, 170))
    screen.blit(shade, (0, 0))
    title = big_font.render(state.label, True, (35, 35, 35))
    screen.blit(title, title.get_rect(center=(config.WINDOW_WIDTH // 2, 300)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    pygame.display.set_caption("Skeleton Runner")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 24)
    big_font = pygame.font.SysFont("consolas", 52, bold=True)

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    if not cap.isOpened():
        print("No se pudo abrir la camara. Revisa CAMERA_INDEX en config.py.")
        pygame.quit()
        return 1

    detector = PoseDetector()
    game = Game(font, big_font)
    state = PoseState()
    last_frame = None

    try:
        running = True
        while running:
            dt = clock.tick(config.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_UP):
                        game.handle_jump()
                    elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False

            ok, frame = cap.read()
            if ok:
                frame = cv2.flip(frame, 1)
                last_frame = frame
                state = detector.process(frame)
            else:
                state = PoseState(label="SIN CAMARA", calibrated=True)

            if state.calibrated and state.jump_event:
                game.handle_jump()
            if state.calibrated:
                game.update(dt, state.ducking)

            game.draw(screen)
            if last_frame is not None:
                draw_camera_preview(screen, last_frame, state, detector, font)
            if not state.calibrated:
                draw_calibration(screen, state, big_font)

            pygame.display.flip()
    finally:
        detector.close()
        cap.release()
        pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
