import sys
import time

import cv2
import pygame

import config
from game import Game
from leaderboard import Leaderboard
from pose_detector import PoseDetector, PoseState


ENTER_NAME = "enter_name"
INTRO = "intro"
CALIBRATING = "calibrating"
PLAYING = "playing"
NAME_CONFIRM = "name_confirm"


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
    shade.fill((8, 12, 24, 185))
    screen.blit(shade, (0, 0))
    title = big_font.render(state.label, True, config.HUD_TEXT)
    screen.blit(title, title.get_rect(center=(config.WINDOW_WIDTH // 2, 300)))
    subtitle = pygame.font.SysFont("consolas", 26).render("Quedate derecho y visible de pies a hombros", True, config.NEON_CYAN)
    screen.blit(subtitle, subtitle.get_rect(center=(config.WINDOW_WIDTH // 2, 355)))


def draw_intro(screen, frame_bgr, game, font, big_font, seconds_left):
    game.draw(screen)
    shade = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
    shade.fill((5, 8, 18, 205))
    screen.blit(shade, (0, 0))

    title = big_font.render("CYBER-RUN", True, config.NEON_CYAN)
    glow = big_font.render("CYBER-RUN", True, config.NEON_GREEN)
    left = pygame.Rect(54, 72, 560, 480)
    right = pygame.Rect(680, 78, 520, 390)

    pygame.draw.rect(screen, (10, 16, 26, 190), left, border_radius=8)
    pygame.draw.rect(screen, config.CIRCUIT_MAGENTA, left, 2, border_radius=8)
    pygame.draw.rect(screen, (10, 16, 26, 170), right, border_radius=8)
    pygame.draw.rect(screen, config.NEON_CYAN, right, 2, border_radius=8)

    screen.blit(glow, glow.get_rect(topleft=(left.x + 35, left.y + 24)))
    screen.blit(title, title.get_rect(topleft=(left.x + 38, left.y + 24)))

    steps = [
        ("1", "Ponte frente a la camara"),
        ("2", "Mantente visible de hombros a pies"),
        ("3", "Salta para saltar en el juego"),
        ("4", "Agachate para esquivar drones altos"),
        ("5", "Despues viene una calibracion corta"),
    ]
    y = left.y + 120
    for number, line in steps:
        pygame.draw.circle(screen, config.CIRCUIT_GREEN, (left.x + 54, y + 14), 16)
        badge = font.render(number, True, (8, 18, 18))
        screen.blit(badge, badge.get_rect(center=(left.x + 54, y + 14)))
        text = font.render(line, True, config.HUD_TEXT)
        screen.blit(text, (left.x + 86, y))
        y += 58

    if frame_bgr is not None:
        preview_w, preview_h = right.w - 36, right.h - 72
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb = cv2.resize(frame_rgb, (preview_w, preview_h))
        preview = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        rect = pygame.Rect(right.x + 18, right.y + 52, preview_w, preview_h)
        label = font.render("VISTA DE CAMARA", True, config.NEON_CYAN)
        screen.blit(label, (right.x + 22, right.y + 16))
        pygame.draw.rect(screen, (12, 16, 28), rect.inflate(8, 8), border_radius=6)
        screen.blit(preview, rect)
    else:
        label = font.render("Esperando camara...", True, config.NEON_CYAN)
        screen.blit(label, label.get_rect(center=right.center))

    countdown = max(0, int(seconds_left) + 1)
    prompt_rect = pygame.Rect(250, config.WINDOW_HEIGHT - 96, 780, 52)
    pygame.draw.rect(screen, (8, 18, 18, 185), prompt_rect, border_radius=8)
    pygame.draw.rect(screen, config.CIRCUIT_GREEN, prompt_rect, 2, border_radius=8)
    prompt = font.render(f"Calibracion en {countdown}s  |  ESPACIO para empezar ahora", True, config.NEON_GREEN)
    screen.blit(prompt, prompt.get_rect(center=prompt_rect.center))


def draw_enter_name(screen, player_name, font, big_font):
    shade = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
    shade.fill((8, 12, 24, 220))
    screen.blit(shade, (0, 0))
    title = big_font.render("INGRESA TU NOMBRE", True, config.HUD_TEXT)
    screen.blit(title, title.get_rect(center=(config.WINDOW_WIDTH // 2, 220)))
    display_name = (player_name + "█") if len(player_name) < 15 else player_name[:15]
    text = big_font.render(display_name, True, config.NEON_CYAN)
    screen.blit(text, text.get_rect(center=(config.WINDOW_WIDTH // 2, 310)))
    hint = font.render("Letras, numeros, espacio  |  ENTER para confirmar", True, config.NEON_GREEN)
    screen.blit(hint, hint.get_rect(center=(config.WINDOW_WIDTH // 2, 380)))
    if not player_name:
        empty = font.render("(vacio = JUGADOR)", True, (140, 140, 140))
        screen.blit(empty, empty.get_rect(center=(config.WINDOW_WIDTH // 2, 345)))


def draw_leaderboard_overlay(screen, leaderboard, font, big_font):
    shade = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
    shade.fill((5, 8, 18, 210))
    screen.blit(shade, (0, 0))
    title = big_font.render("LEADERBOARD", True, config.NEON_CYAN)
    screen.blit(title, title.get_rect(center=(config.WINDOW_WIDTH // 2, 80)))
    entries = leaderboard.get_top()
    if not entries:
        msg = font.render("Todavia no hay scores registrados", True, (140, 140, 140))
        screen.blit(msg, msg.get_rect(center=(config.WINDOW_WIDTH // 2, 300)))
    else:
        header = font.render(f"{'#':>3}  {'NOMBRE':<18}  {'SCORE':>6}", True, config.NEON_GREEN)
        screen.blit(header, header.get_rect(center=(config.WINDOW_WIDTH // 2, 140)))
        pygame.draw.line(screen, config.CIRCUIT_LINE, (config.WINDOW_WIDTH // 2 - 220, 170), (config.WINDOW_WIDTH // 2 + 220, 170), 2)
        y = 200
        for i, (name, score, _) in enumerate(entries):
            color = config.NEON_DINO if i == 0 else config.HUD_TEXT
            line = font.render(f"{i+1:>3}  {name:<18}  {score:>6}", True, color)
            screen.blit(line, line.get_rect(midleft=(config.WINDOW_WIDTH // 2 - 220, y)))
            y += 42
    prompt = font.render("Presiona cualquier tecla para cerrar", True, (120, 120, 140))
    screen.blit(prompt, prompt.get_rect(center=(config.WINDOW_WIDTH // 2, config.WINDOW_HEIGHT - 60)))


def draw_name_confirm(screen, player_name, existing_score, font, big_font):
    shade = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
    shade.fill((8, 12, 24, 220))
    screen.blit(shade, (0, 0))
    title = big_font.render("JUGADOR EXISTENTE", True, config.CIRCUIT_MAGENTA)
    screen.blit(title, title.get_rect(center=(config.WINDOW_WIDTH // 2, 200)))
    msg = font.render(f"'{player_name}' ya existe  |  Mejor score: {existing_score}", True, config.HUD_TEXT)
    screen.blit(msg, msg.get_rect(center=(config.WINDOW_WIDTH // 2, 270)))
    opt1 = font.render("ESPACIO / ENTER  -  Continuar como este jugador", True, config.NEON_GREEN)
    screen.blit(opt1, opt1.get_rect(center=(config.WINDOW_WIDTH // 2, 340)))
    opt2 = font.render("N / BACKSPACE  -  Elegir otro nombre", True, config.NEON_CYAN)
    screen.blit(opt2, opt2.get_rect(center=(config.WINDOW_WIDTH // 2, 390)))


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
    leaderboard = Leaderboard()
    state = PoseState()
    last_frame = None
    player_name = ""
    existing_score = 0
    score_saved = False
    show_leaderboard = False
    app_state = ENTER_NAME
    intro_start = time.time()

    try:
        running = True
        while running:
            dt = clock.tick(config.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if app_state == ENTER_NAME:
                        if event.key == pygame.K_RETURN:
                            if not player_name.strip():
                                player_name = "JUGADOR"
                            best = leaderboard.get_player_best(player_name)
                            if best > 0:
                                existing_score = best
                                app_state = NAME_CONFIRM
                            else:
                                app_state = INTRO
                                intro_start = time.time()
                        elif event.key == pygame.K_BACKSPACE:
                            player_name = player_name[:-1]
                        elif event.key == pygame.K_SPACE and len(player_name) < 15:
                            player_name += " "
                        elif event.unicode and event.unicode.isprintable() and len(player_name) < 15:
                            player_name += event.unicode
                    elif app_state == NAME_CONFIRM:
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            app_state = INTRO
                            intro_start = time.time()
                        elif event.key in (pygame.K_n, pygame.K_BACKSPACE):
                            player_name = ""
                            existing_score = 0
                            app_state = ENTER_NAME
                    elif show_leaderboard:
                        if event.key == pygame.K_n and player_name:
                            show_leaderboard = False
                            player_name = ""
                            existing_score = 0
                            app_state = ENTER_NAME
                        else:
                            show_leaderboard = False
                    elif event.key == pygame.K_l and (app_state == INTRO or (app_state == PLAYING and (game.game_over or game.victory))):
                        show_leaderboard = True
                    elif event.key == pygame.K_n and (app_state == INTRO or (app_state == PLAYING and (game.game_over or game.victory))):
                        player_name = ""
                        existing_score = 0
                        app_state = ENTER_NAME
                    elif event.key in (pygame.K_SPACE, pygame.K_UP):
                        if app_state == INTRO:
                            app_state = CALIBRATING
                        elif app_state == PLAYING and (game.game_over or game.victory):
                            score_saved = False
                            game.reset()
                        elif app_state == PLAYING:
                            game.handle_jump()
                    elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False

            ok, frame = cap.read()
            if ok:
                frame = cv2.flip(frame, 1)
                last_frame = frame
                if app_state != INTRO:
                    state = detector.process(frame)
            else:
                state = PoseState(label="SIN CAMARA", calibrated=True)

            if app_state == INTRO and time.time() - intro_start >= config.INTRO_SECONDS:
                app_state = CALIBRATING

            if app_state == CALIBRATING and state.calibrated:
                app_state = PLAYING

            if app_state == PLAYING and state.jump_event and not show_leaderboard:
                game.handle_jump()
            if app_state == PLAYING and not show_leaderboard:
                game.update(dt, state.ducking)
                if game.game_over or game.victory:
                    if not score_saved:
                        leaderboard.add_score(player_name, int(game.score))
                        score_saved = True
                        show_leaderboard = True

            if app_state == ENTER_NAME:
                draw_enter_name(screen, player_name, font, big_font)
            elif app_state == NAME_CONFIRM:
                draw_name_confirm(screen, player_name, existing_score, font, big_font)
            elif app_state == INTRO:
                seconds_left = config.INTRO_SECONDS - (time.time() - intro_start)
                draw_intro(screen, last_frame, game, font, big_font, seconds_left)
            else:
                game.draw(screen)
                if player_name:
                    label = font.render(f"{player_name}", True, config.NEON_DINO)
                    label_rect = label.get_rect(bottomright=(config.WINDOW_WIDTH - 22, config.WINDOW_HEIGHT - 22))
                    bg = pygame.Surface(label_rect.inflate(16, 8).size, pygame.SRCALPHA)
                    pygame.draw.rect(bg, (8, 16, 28, 180), bg.get_rect(), border_radius=4)
                    screen.blit(bg, label_rect.inflate(16, 8).topleft)
                    screen.blit(label, label_rect)
                if last_frame is not None:
                    draw_camera_preview(screen, last_frame, state, detector, font)
                if app_state == CALIBRATING:
                    draw_calibration(screen, state, big_font)

            if show_leaderboard:
                draw_leaderboard_overlay(screen, leaderboard, font, big_font)

            pygame.display.flip()
    finally:
        detector.close()
        leaderboard.close()
        cap.release()
        pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
