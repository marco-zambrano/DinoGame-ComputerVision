import random
from dataclasses import dataclass

import pygame

import config


PIXEL = 3
GROUND_HEIGHT = config.WINDOW_HEIGHT - config.GROUND_Y
PANEL_WIDTH = 128


@dataclass
class Obstacle:
    kind: str
    x: float
    y: int
    w: int
    h: int

    @property
    def rect(self):
        return pygame.Rect(int(self.x), self.y, self.w, self.h)


def _rgba(color, alpha):
    return (*color[:3], alpha)


def _draw_neon_line(surface, color, start, end, width=2):
    for glow_width, alpha in ((width + 8, 28), (width + 5, 46), (width + 2, 78)):
        pygame.draw.line(surface, _rgba(color, alpha), start, end, glow_width)
    pygame.draw.line(surface, color, start, end, width)


def _draw_neon_rect(surface, rect, color, width=2, radius=0):
    for glow_width, alpha in ((width + 8, 24), (width + 5, 42), (width + 2, 76)):
        pygame.draw.rect(surface, _rgba(color, alpha), rect, glow_width, border_radius=radius)
    pygame.draw.rect(surface, color, rect, width, border_radius=radius)


def _draw_neon_circle(surface, color, center, radius):
    for grow, alpha in ((8, 24), (5, 42), (2, 76)):
        pygame.draw.circle(surface, _rgba(color, alpha), center, radius + grow)
    pygame.draw.circle(surface, color, center, radius)


class Dino:
    def __init__(self):
        self.y = config.GROUND_Y - config.DINO_HEIGHT
        self.vy = 0.0
        self.ducking = False
        self.on_ground = True
        self.step_timer = 0.0
        self.run_sprites = (self._make_run_sprite(0), self._make_run_sprite(1))
        self.duck_sprites = (self._make_duck_sprite(0), self._make_duck_sprite(1))

    @property
    def rect(self):
        h = config.DINO_DUCK_HEIGHT if self.ducking and self.on_ground else config.DINO_HEIGHT
        w = config.DINO_DUCK_WIDTH if self.ducking and self.on_ground else config.DINO_WIDTH
        y = config.GROUND_Y - h if self.on_ground and self.ducking else self.y
        return pygame.Rect(config.DINO_X, int(y), w, h)

    def jump(self):
        if self.on_ground:
            self.vy = config.JUMP_VELOCITY
            self.on_ground = False
            self.ducking = False

    def update(self, dt, ducking):
        self.ducking = ducking and self.on_ground
        if not self.on_ground:
            self.vy += config.GRAVITY * dt
            self.y += self.vy * dt
            floor_y = config.GROUND_Y - config.DINO_HEIGHT
            if self.y >= floor_y:
                self.y = floor_y
                self.vy = 0.0
                self.on_ground = True
        else:
            self.y = config.GROUND_Y - config.DINO_HEIGHT
        self.step_timer += dt

    def draw(self, surface):
        r = self.rect
        if self.ducking and self.on_ground:
            sprite = self.duck_sprites[int(self.step_timer * 12) % 2]
        else:
            sprite = self.run_sprites[int(self.step_timer * 12) % 2]
        surface.blit(sprite, (r.x - 10, r.bottom - sprite.get_height() - 8))

    def _make_surface(self, width, height):
        return pygame.Surface((width * PIXEL, height * PIXEL), pygame.SRCALPHA)

    def _px(self, surface, x, y, w=1, h=1, color=config.NEON_DINO):
        pygame.draw.rect(surface, color, (x * PIXEL, y * PIXEL, w * PIXEL, h * PIXEL))

    def _make_run_sprite(self, frame):
        mask = self._make_surface(24, 26)

        self._px(mask, 0, 13, 4, 3)
        self._px(mask, 2, 12, 4, 3)
        self._px(mask, 4, 11, 4, 3)
        self._px(mask, 6, 10, 4, 3)
        self._px(mask, 7, 10, 9, 9)
        self._px(mask, 9, 8, 7, 4)
        self._px(mask, 11, 17, 5, 3)
        self._px(mask, 14, 7, 3, 7)
        self._px(mask, 15, 3, 8, 8)
        self._px(mask, 18, 8, 6, 3)
        self._px(mask, 18, 11, 4, 1)
        self._px(mask, 21, 5, 2, 2)
        self._px(mask, 19, 7, 4, 1, (0, 0, 0, 0))
        self._px(mask, 15, 14, 3, 1)
        self._px(mask, 17, 15, 1, 2)

        if frame == 0:
            self._px(mask, 9, 19, 3, 5)
            self._px(mask, 8, 24, 4, 2)
            self._px(mask, 14, 19, 3, 4)
            self._px(mask, 15, 23, 2, 2)
        else:
            self._px(mask, 9, 19, 3, 4)
            self._px(mask, 9, 23, 2, 2)
            self._px(mask, 14, 19, 3, 5)
            self._px(mask, 13, 24, 4, 2)

        return self._with_sprite_glow(mask, (20 * PIXEL, 5 * PIXEL), 92)

    def _make_duck_sprite(self, frame):
        mask = self._make_surface(32, 15)

        self._px(mask, 0, 8, 5, 2)
        self._px(mask, 3, 7, 6, 2)
        self._px(mask, 7, 6, 12, 5)
        self._px(mask, 10, 10, 8, 2)
        self._px(mask, 17, 5, 4, 5)
        self._px(mask, 20, 3, 9, 6)
        self._px(mask, 24, 7, 8, 2)
        self._px(mask, 27, 4, 2, 2)
        self._px(mask, 25, 6, 5, 1, (0, 0, 0, 0))
        self._px(mask, 18, 10, 3, 1)
        self._px(mask, 20, 11, 1, 1)

        if frame == 0:
            self._px(mask, 10, 12, 3, 3)
            self._px(mask, 9, 14, 4, 1)
            self._px(mask, 17, 12, 3, 2)
            self._px(mask, 18, 14, 3, 1)
        else:
            self._px(mask, 10, 12, 3, 2)
            self._px(mask, 10, 14, 3, 1)
            self._px(mask, 17, 12, 3, 3)
            self._px(mask, 16, 14, 4, 1)

        return self._with_sprite_glow(mask, (26 * PIXEL, 4 * PIXEL), 51)

    def _with_sprite_glow(self, mask, eye_pos, height):
        pad = 10
        sprite = pygame.Surface((mask.get_width() + pad * 2, height + pad * 2), pygame.SRCALPHA)
        for radius, alpha in ((8, 32), (5, 54), (3, 88)):
            glow = mask.copy()
            glow.fill(_rgba(config.NEON_DINO, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            for dx, dy in ((-radius, 0), (radius, 0), (0, -radius), (0, radius), (-radius, -radius), (radius, radius)):
                sprite.blit(glow, (pad + dx, pad + dy))
        core = mask.copy()
        core.fill((*config.NEON_DINO, 220), special_flags=pygame.BLEND_RGBA_MULT)
        sprite.blit(core, (pad, pad))
        highlight = mask.copy()
        highlight.fill((*config.NEON_DINO_CORE, 120), special_flags=pygame.BLEND_RGBA_MULT)
        sprite.blit(highlight, (pad, pad))
        _draw_neon_circle(sprite, (255, 255, 255), (pad + eye_pos[0], pad + eye_pos[1]), 2)
        return sprite


class Game:
    def __init__(self, font, big_font):
        self.font = font
        self.big_font = big_font
        self.high_score = 0
        self.background = self._make_background()
        self.binary_fonts = {size: pygame.font.SysFont("consolas", size, bold=True) for size in (18, 20, 22)}
        self.binary_bits = self._make_binary_bits()
        self.cloud_variants = [self._make_cloud_sprite(i) for i in range(3)]
        self.reset()

    def reset(self):
        self.dino = Dino()
        self.obstacles = []
        self.speed = config.START_SPEED
        self.score = 0
        self.distance_to_next = random.randint(config.OBSTACLE_MIN_GAP, config.OBSTACLE_MAX_GAP)
        self.game_over = False
        self.ground_phase = 0.0
        self.clouds = [
            [random.randint(0, config.WINDOW_WIDTH), random.randint(70, 230), random.randrange(len(self.cloud_variants))]
            for _ in range(6)
        ]

    def handle_jump(self):
        if self.game_over:
            self.reset()
        else:
            self.dino.jump()

    def update(self, dt, ducking):
        if self.game_over:
            return
        self.speed = min(config.MAX_SPEED, self.speed + config.SPEED_GAIN_PER_SECOND * dt)
        self.score += config.SCORE_RATE * dt
        self.high_score = max(self.high_score, int(self.score))
        self.ground_phase = (self.ground_phase + self.speed * dt) % PANEL_WIDTH
        self.dino.update(dt, ducking)

        for bit in self.binary_bits:
            bit[0] -= self.speed * 0.055 * dt
            bit[1] += bit[4] * dt
            if bit[0] < -40 or bit[1] > config.GROUND_Y - 10:
                bit[0] = config.WINDOW_WIDTH + random.randint(0, 220)
                bit[1] = random.randint(40, config.GROUND_Y - 120)
                bit[2] = random.choice(("0", "1"))

        for cloud in self.clouds:
            cloud[0] -= 24 * dt
            if cloud[0] < -180:
                cloud[0] = config.WINDOW_WIDTH + random.randint(40, 260)
                cloud[1] = random.randint(70, 230)
                cloud[2] = random.randrange(len(self.cloud_variants))

        self.distance_to_next -= self.speed * dt
        if self.distance_to_next <= 0:
            self._spawn_obstacle()
            self.distance_to_next = random.randint(config.OBSTACLE_MIN_GAP, config.OBSTACLE_MAX_GAP)

        for obstacle in self.obstacles:
            obstacle.x -= self.speed * dt
        self.obstacles = [o for o in self.obstacles if o.x + o.w > -20]

        dino_hitbox = self.dino.rect.inflate(-10, -8)
        if any(dino_hitbox.colliderect(o.rect.inflate(-6, -6)) for o in self.obstacles):
            self.game_over = True

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        self._draw_binary_rain(surface)
        self._draw_clouds(surface)
        self._draw_circuit_floor(surface)
        for obstacle in self.obstacles:
            self._draw_obstacle(surface, obstacle)
        self.dino.draw(surface)
        self._draw_title_bar(surface)
        self._draw_score(surface)
        if self.game_over:
            self._draw_game_over(surface)

    def _spawn_obstacle(self):
        kind = random.choices(["cactus", "computer", "bird_low", "bird_high"], weights=[0.34, 0.28, 0.25, 0.13])[0]
        if kind == "cactus":
            w = random.choice([38, 52, 66])
            h = random.choice([60, 76, 90])
            self.obstacles.append(Obstacle(kind, config.WINDOW_WIDTH + 20, config.GROUND_Y - h, w, h))
        elif kind == "computer":
            self.obstacles.append(Obstacle(kind, config.WINDOW_WIDTH + 20, config.GROUND_Y - 78, 72, 78))
        elif kind == "bird_low":
            self.obstacles.append(Obstacle(kind, config.WINDOW_WIDTH + 20, config.GROUND_Y - 92, 62, 38))
        else:
            self.obstacles.append(Obstacle(kind, config.WINDOW_WIDTH + 20, config.GROUND_Y - 165, 62, 38))

    def _make_background(self):
        bg = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        horizon = config.GROUND_Y
        for y in range(horizon):
            t = y / max(1, horizon - 1)
            if t < 0.52:
                local = t / 0.52
                color = self._lerp(config.CYBER_BG_TOP, config.CYBER_BG_MID, local)
            else:
                local = (t - 0.52) / 0.48
                color = self._lerp(config.CYBER_BG_MID, config.CYBER_BG_BOTTOM, local)
            pygame.draw.line(bg, color, (0, y), (config.WINDOW_WIDTH, y))
        pygame.draw.rect(bg, config.CIRCUIT_PANEL_COLOR, (0, horizon, config.WINDOW_WIDTH, GROUND_HEIGHT))
        return bg

    def _make_binary_bits(self):
        return [
            [
                random.randint(0, config.WINDOW_WIDTH),
                random.randint(45, config.GROUND_Y - 85),
                random.choice(("0", "1")),
                random.choice((18, 20, 22)),
                random.uniform(4.0, 13.0),
            ]
            for _ in range(70)
        ]

    def _draw_binary_rain(self, surface):
        overlay = pygame.Surface((config.WINDOW_WIDTH, config.GROUND_Y), pygame.SRCALPHA)
        for x, y, bit, size, _speed in self.binary_bits:
            glyph = self.binary_fonts[size].render(bit, True, config.CYBER_DATA_RAIN)
            overlay.blit(glyph, (int(x), int(y)))
        surface.blit(overlay, (0, 0))

    def _make_cloud_sprite(self, variant):
        sprite = pygame.Surface((190, 96), pygame.SRCALPHA)
        shapes = [
            [(48, 48, 25), (78, 38, 33), (113, 44, 29), (139, 54, 22)],
            [(38, 56, 21), (69, 44, 28), (99, 39, 35), (132, 51, 28), (154, 58, 18)],
            [(54, 54, 28), (90, 42, 36), (129, 49, 25), (151, 59, 20)],
        ][variant]
        for grow, alpha in ((16, 26), (10, 42), (5, 62)):
            for cx, cy, radius in shapes:
                pygame.draw.circle(sprite, _rgba(config.CYBER_CLOUD_GLOW, alpha), (cx, cy), radius + grow)
        for cx, cy, radius in shapes:
            pygame.draw.circle(sprite, config.CYBER_CLOUD, (cx, cy), radius)
        for cx, cy, radius in shapes[:2]:
            pygame.draw.circle(sprite, _rgba(config.CYBER_CLOUD_HIGHLIGHT, 190), (cx - 6, cy - 6), max(8, radius // 2))
        return sprite

    def _draw_clouds(self, surface):
        for x, y, variant in self.clouds:
            surface.blit(self.cloud_variants[variant], (int(x), int(y)))

    def _draw_circuit_floor(self, surface):
        floor = pygame.Surface((config.WINDOW_WIDTH, GROUND_HEIGHT), pygame.SRCALPHA)
        for x in range(-PANEL_WIDTH, config.WINDOW_WIDTH + PANEL_WIDTH, PANEL_WIDTH):
            px = x - int(self.ground_phase)
            panel_color = config.CIRCUIT_PANEL_COLOR if (x // PANEL_WIDTH) % 2 == 0 else config.CIRCUIT_PANEL_ALT
            pygame.draw.rect(floor, panel_color, (px, 0, PANEL_WIDTH - 3, GROUND_HEIGHT))
            pygame.draw.rect(floor, (20, 18, 38), (px, 0, PANEL_WIDTH - 3, GROUND_HEIGHT), 2)

            y_mid = 36 + ((x // PANEL_WIDTH) % 3) * 12
            points = [(px + 8, y_mid), (px + 34, y_mid), (px + 34, y_mid + 22), (px + 82, y_mid + 22), (px + 82, y_mid - 8), (px + 118, y_mid - 8)]
            for start, end in zip(points, points[1:]):
                _draw_neon_line(floor, config.CIRCUIT_LINE, start, end, 2)
            for point in points[1:-1]:
                _draw_neon_circle(floor, config.CIRCUIT_LINE, point, 3)

            accent = config.CIRCUIT_MAGENTA if (x // PANEL_WIDTH) % 3 == 0 else config.CIRCUIT_GREEN
            _draw_neon_line(floor, accent, (px + 24, 92), (px + 56, 92), 2)
            _draw_neon_circle(floor, accent, (px + 64, 92), 3)
        surface.blit(floor, (0, config.GROUND_Y))
        _draw_neon_line(surface, config.CIRCUIT_LINE, (0, config.GROUND_Y), (config.WINDOW_WIDTH, config.GROUND_Y), 2)

    def _draw_obstacle(self, surface, obstacle):
        if obstacle.kind == "computer":
            self._draw_computer(surface, obstacle.rect)
        elif obstacle.kind.startswith("bird"):
            self._draw_drone(surface, obstacle.rect)
        else:
            self._draw_cactus(surface, obstacle.rect)

    def _draw_cactus(self, surface, r):
        fill = pygame.Surface((r.w + 34, r.h + 34), pygame.SRCALPHA)
        offset = 17
        body = pygame.Rect(offset + 12, offset, max(14, r.w - 24), r.h)
        left = pygame.Rect(offset, offset + r.h // 3, 18, r.h // 2)
        right = pygame.Rect(offset + r.w - 18, offset + r.h // 4, 18, r.h // 2)
        for shape in (body, left, right):
            pygame.draw.rect(fill, (7, 42, 39, 135), shape, border_radius=8)
            _draw_neon_rect(fill, shape, config.NEON_CYAN, 2, 8)
        surface.blit(fill, (r.x - offset, r.y - offset))

    def _draw_computer(self, surface, r):
        flicker = 150 + int((self.score * 18) % 70)
        pad = 16
        layer = pygame.Surface((r.w + pad * 2, r.h + pad * 2), pygame.SRCALPHA)
        monitor = pygame.Rect(pad + 4, pad, r.w - 8, 44)
        screen = pygame.Rect(pad + 12, pad + 8, r.w - 24, 24)
        stand = pygame.Rect(pad + 29, pad + 44, 14, 10)
        base = pygame.Rect(pad + 16, pad + 54, r.w - 32, 10)
        tower = pygame.Rect(pad + 7, pad + 58, r.w - 14, 20)
        for rect in (monitor, stand, base, tower):
            pygame.draw.rect(layer, config.CRT_BODY, rect, border_radius=3)
            pygame.draw.rect(layer, config.CRT_DARK, rect, 2, border_radius=3)
        pygame.draw.rect(layer, _rgba(config.CRT_SCREEN, flicker), screen, border_radius=2)
        _draw_neon_rect(layer, screen, config.CRT_SCREEN, 2, 2)
        _draw_neon_line(layer, config.CRT_SCREEN, (screen.x + 7, screen.y + 14), (screen.x + 24, screen.y + 14), 2)
        _draw_neon_circle(layer, config.CIRCUIT_MAGENTA, (tower.right - 12, tower.y + 10), 3)
        surface.blit(layer, (r.x - pad, r.y - pad))

    def _draw_drone(self, surface, r):
        wing = 8 if int(self.score * 2) % 2 == 0 else -8
        layer = pygame.Surface((r.w + 54, r.h + 48), pygame.SRCALPHA)
        ox, oy = 27, 24
        body = pygame.Rect(ox + 12, oy + 8, r.w - 24, r.h - 14)
        pygame.draw.ellipse(layer, (12, 22, 34, 150), body)
        _draw_neon_rect(layer, body, config.CIRCUIT_MAGENTA, 2, 14)
        left = [(ox + 18, oy + 18), (ox - 10, oy + 12 + wing), (ox + 10, oy + 26)]
        right = [(ox + r.w - 18, oy + 18), (ox + r.w + 10, oy + 12 - wing), (ox + r.w - 10, oy + 26)]
        for poly in (left, right):
            pygame.draw.polygon(layer, (12, 28, 42, 135), poly)
            pygame.draw.lines(layer, _rgba(config.CIRCUIT_LINE, 80), True, poly, 8)
            pygame.draw.lines(layer, config.CIRCUIT_LINE, True, poly, 2)
        _draw_neon_circle(layer, config.NEON_GREEN, (ox + r.w - 13, oy + 18), 3)
        surface.blit(layer, (r.x - ox, r.y - oy))

    def _draw_score(self, surface):
        score_text = f"HI: {self.high_score:05d} | SCORE: {int(self.score):05d}"
        text = self.font.render(score_text, True, config.HUD_TEXT)
        glow = self.font.render(score_text, True, config.NEON_CYAN)
        x = config.WINDOW_WIDTH - text.get_width() - 24
        y = 24
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            glow.set_alpha(70)
            surface.blit(glow, (x + dx, y + dy))
        surface.blit(text, (x, y))

    def _draw_title_bar(self, surface):
        bar = pygame.Rect(18, 18, 330, 34)
        pygame.draw.rect(surface, config.RETRO_WINDOW, bar, border_radius=3)
        pygame.draw.rect(surface, _rgba(config.RETRO_WINDOW_BORDER, 150), bar, 1, border_radius=3)
        label = self.font.render("CHROME:// CYBER-RUN", True, config.HUD_TEXT)
        surface.blit(label, (bar.x + 12, bar.y + 6))
        colors = (config.CIRCUIT_MAGENTA, config.CIRCUIT_GREEN, config.CIRCUIT_LINE)
        for i, color in enumerate(colors):
            pygame.draw.circle(surface, color, (bar.right - 76 + i * 24, bar.centery), 6)

    def _draw_game_over(self, surface):
        title = self.big_font.render("SYSTEM HALTED", True, config.HUD_TEXT)
        prompt = self.font.render("Salta o presiona ESPACIO para reiniciar", True, config.NEON_CYAN)
        panel = pygame.Surface((620, 150), pygame.SRCALPHA)
        pygame.draw.rect(panel, (12, 14, 24, 190), panel.get_rect(), border_radius=6)
        _draw_neon_rect(panel, panel.get_rect().inflate(-4, -4), config.CIRCUIT_MAGENTA, 2, 6)
        surface.blit(panel, panel.get_rect(center=(config.WINDOW_WIDTH // 2, 315)))
        surface.blit(title, title.get_rect(center=(config.WINDOW_WIDTH // 2, 290)))
        surface.blit(prompt, prompt.get_rect(center=(config.WINDOW_WIDTH // 2, 340)))

    def _lerp(self, a, b, t):
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
