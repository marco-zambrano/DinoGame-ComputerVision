import random
from dataclasses import dataclass
from pathlib import Path

import pygame

import config


PIXEL = 3
GROUND_HEIGHT = config.WINDOW_HEIGHT - config.GROUND_Y
PANEL_WIDTH = 128
OUTLINE = (8, 16, 24)
DINO_FILL = (88, 190, 112)
DINO_DARK = (20, 56, 42)
PIXEL_SHADOW = (40, 54, 90)
ASSET_DIR = Path(__file__).resolve().parent / "assets" / "dino"


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


def _scale_pixel(surface, scale):
    return pygame.transform.scale(surface, (surface.get_width() * scale, surface.get_height() * scale))


class Dino:
    def __init__(self):
        self.y = config.GROUND_Y - config.DINO_HEIGHT
        self.vy = 0.0
        self.ducking = False
        self.on_ground = True
        self.step_timer = 0.0
        self.air_timer = 0.0
        self.land_timer = 0.0
        self.run_sprites = self._load_sprite_set("run", 4, config.DINO_HEIGHT + 34)
        self.duck_sprites = self._load_sprite_set("duck", 2, config.DINO_DUCK_HEIGHT + 28)
        self.goal_sprites = self._load_named_sprites(("goal_1.png", "goal_2.png", "goal_3.png"), config.DINO_HEIGHT + 52)
        self.goal_meme_sprite = self._load_sprite("goal_meme.png", config.DINO_HEIGHT + 48)
        self.lose_sprites = self._load_named_sprites(("lose_1.png", "lose_2.png", "lose_3.png"), config.DINO_HEIGHT + 48)
        self.jump_prepare_sprite = self._load_sprite("jump_prepare.png", config.DINO_HEIGHT + 22)
        self.jump_sprite = self._load_sprite("jump.png", config.DINO_HEIGHT + 34)
        self.land_sprite = self._load_sprite("land.png", config.DINO_DUCK_HEIGHT + 42)

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
            self.air_timer = 0.0
            self.land_timer = 0.0

    def update(self, dt, ducking):
        self.ducking = ducking and self.on_ground
        if not self.on_ground:
            self.air_timer += dt
            self.vy += config.GRAVITY * dt
            self.y += self.vy * dt
            floor_y = config.GROUND_Y - config.DINO_HEIGHT
            if self.y >= floor_y:
                self.y = floor_y
                self.vy = 0.0
                self.on_ground = True
                self.land_timer = 0.18
        else:
            self.y = config.GROUND_Y - config.DINO_HEIGHT
            self.land_timer = max(0.0, self.land_timer - dt)
        self.step_timer += dt

    def draw(self, surface, celebrating=False, dying=False):
        r = self.rect
        if celebrating and self.goal_sprites:
            sprite = self.goal_sprites[int(self.step_timer * 4) % len(self.goal_sprites)]
            bob = -2 if int(self.step_timer * 8) % 2 == 0 else 0
        elif celebrating and self.goal_meme_sprite is not None:
            sprite = self.goal_meme_sprite
            bob = 0
        elif dying and self.lose_sprites:
            frame = min(len(self.lose_sprites) - 1, int(self.step_timer * 3))
            sprite = self.lose_sprites[frame]
            bob = 0
        elif self.land_timer > 0.0 and self.land_sprite is not None:
            sprite = self.land_sprite
            bob = 0
        elif self.ducking and self.on_ground:
            sprite = self.duck_sprites[int(self.step_timer * 12) % 2]
            bob = 0
        elif not self.on_ground and self.air_timer < 0.14 and self.jump_prepare_sprite is not None:
            sprite = self.jump_prepare_sprite
            bob = 0
        elif not self.on_ground and self.jump_sprite is not None:
            sprite = self.jump_sprite
            bob = 0
        else:
            sprite = self.run_sprites[int(self.step_timer * 14) % len(self.run_sprites)]
            bob = -1 if self.on_ground and int(self.step_timer * 14) % 2 == 0 else 0
        surface.blit(
            sprite,
            (r.x - 18, r.bottom - sprite.get_height() + config.DINO_VISUAL_GROUND_OFFSET + bob),
        )

    def _load_named_sprites(self, filenames, target_height):
        return tuple(
            sprite
            for filename in filenames
            if (sprite := self._load_sprite(filename, target_height)) is not None
        )

    def _load_sprite_set(self, prefix, count, target_height):
        sprites = tuple(
            sprite
            for i in range(1, count + 1)
            if (sprite := self._load_sprite(f"{prefix}_{i}.png", target_height)) is not None
        )
        if len(sprites) == count:
            return sprites
        if prefix == "run":
            return tuple(self._make_run_sprite(i) for i in range(4))
        return tuple(self._make_duck_sprite(i) for i in range(2))

    def _load_sprite(self, filename, target_height):
        path = ASSET_DIR / filename
        if not path.exists():
            return None
        sprite = pygame.image.load(str(path)).convert_alpha()
        return self._scale_sprite(sprite, target_height)

    def _scale_sprite(self, sprite, target_height):
        scale = target_height / sprite.get_height()
        width = max(1, int(sprite.get_width() * scale))
        height = max(1, int(sprite.get_height() * scale))
        return pygame.transform.scale(sprite, (width, height))

    def _make_surface(self, width, height):
        return pygame.Surface((width * PIXEL, height * PIXEL), pygame.SRCALPHA)

    def _px(self, surface, x, y, w=1, h=1, color=DINO_FILL):
        pygame.draw.rect(surface, color, (x * PIXEL, y * PIXEL, w * PIXEL, h * PIXEL))

    def _make_run_sprite(self, frame):
        mask = self._make_surface(29, 30)
        self._draw_trex(mask, frame, duck=False)
        return self._with_sprite_glow(mask, (23 * PIXEL, 6 * PIXEL), mask.get_height())

    def _make_duck_sprite(self, frame):
        mask = self._make_surface(35, 17)
        self._draw_trex(mask, frame, duck=True)
        return self._with_sprite_glow(mask, (28 * PIXEL, 4 * PIXEL), mask.get_height())

    def _draw_trex(self, mask, frame, duck):
        if duck:
            fill_rects = [
                (1, 9, 7, 2), (5, 8, 7, 2), (9, 7, 12, 5), (13, 11, 9, 2),
                (20, 5, 5, 6), (24, 3, 9, 6), (29, 7, 6, 2), (31, 4, 2, 2),
                (20, 11, 4, 1), (22, 12, 1, 1),
            ]
            legs_a = [(12, 13, 3, 3), (11, 16, 4, 1), (20, 13, 3, 2), (21, 16, 3, 1)]
            legs_b = [(12, 13, 3, 2), (12, 16, 3, 1), (20, 13, 3, 3), (19, 16, 4, 1)]
        else:
            fill_rects = [
                (0, 15, 4, 2), (2, 14, 5, 3), (4, 13, 6, 3), (7, 12, 5, 3),
                (9, 11, 9, 9), (11, 9, 8, 4), (13, 18, 5, 3), (17, 8, 3, 7),
                (18, 4, 8, 8), (21, 9, 7, 3), (21, 12, 5, 1), (25, 6, 2, 2),
                (18, 15, 3, 1), (20, 16, 1, 2),
            ]
            legs = [
                [(11, 20, 3, 5), (10, 25, 4, 2), (17, 20, 3, 3), (18, 23, 2, 2)],
                [(11, 20, 3, 4), (11, 24, 2, 2), (17, 20, 3, 5), (16, 25, 4, 2)],
                [(10, 20, 3, 3), (9, 23, 3, 2), (17, 20, 3, 5), (18, 25, 3, 2)],
                [(11, 20, 3, 5), (12, 25, 3, 2), (18, 20, 3, 3), (19, 23, 3, 2)],
            ]
            fill_rects += legs[frame % 4]

        if duck:
            fill_rects += legs_a if frame == 0 else legs_b

        for x, y, w, h in fill_rects:
            self._px(mask, x - 1, y, w + 2, h, OUTLINE)
            self._px(mask, x, y - 1, w, h + 2, OUTLINE)
        for rect in fill_rects:
            self._px(mask, *rect)

        mouth = (24, 6, 5, 1) if duck else (22, 8, 5, 1)
        self._px(mask, *mouth, color=OUTLINE)
        self._px(mask, 23 if not duck else 28, 6 if not duck else 4, 1, 1, color=(230, 255, 235))
        self._px(mask, 10 if not duck else 15, 19 if not duck else 12, 2, 2, color=DINO_DARK)

    def _with_sprite_glow(self, mask, eye_pos, height):
        pad = 10
        sprite = pygame.Surface((mask.get_width() + pad * 2, height + pad * 2), pygame.SRCALPHA)
        for radius, alpha in ((10, 30), (6, 52), (3, 86)):
            glow = mask.copy()
            glow.fill(_rgba(config.NEON_GREEN, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            for dx, dy in ((-radius, 0), (radius, 0), (0, -radius), (0, radius), (-radius, -radius), (radius, radius)):
                sprite.blit(glow, (pad + dx, pad + dy))
        sprite.blit(mask, (pad, pad))
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
        self.previous_high_score = self.high_score
        self.distance_to_next = random.randint(config.OBSTACLE_MIN_GAP, config.OBSTACLE_MAX_GAP)
        self.game_over = False
        self.record_break = False
        self.victory = False
        self.victory_timer = 0.0
        self.ground_phase = 0.0
        self.clouds = [
            [random.randint(0, config.WINDOW_WIDTH), random.randint(70, 230), random.randrange(len(self.cloud_variants))]
            for _ in range(6)
        ]

    def handle_jump(self):
        if self.game_over or self.victory:
            self.reset()
        else:
            self.dino.jump()

    def update(self, dt, ducking):
        if self.game_over:
            self.dino.step_timer += dt
            return
        if self.victory:
            self.victory_timer += dt
            self.ground_phase = (self.ground_phase + self.speed * 0.25 * dt) % PANEL_WIDTH
            self.dino.update(dt, False)
            return
        self.speed = min(config.MAX_SPEED, self.speed + config.SPEED_GAIN_PER_SECOND * dt)
        self.score += config.SCORE_RATE * dt
        self.high_score = max(self.high_score, int(self.score))
        if self.score >= config.GOAL_SCORE:
            self.score = config.GOAL_SCORE
            self.high_score = max(self.high_score, int(self.score))
            self.victory = True
            self.victory_timer = 0.0
            self.dino.step_timer = 0.0
            self.obstacles.clear()
            return
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
            self.record_break = int(self.score) > self.previous_high_score
            self.dino.step_timer = 0.0

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        self._draw_binary_rain(surface)
        self._draw_clouds(surface)
        self._draw_circuit_floor(surface)
        for obstacle in self.obstacles:
            self._draw_obstacle(surface, obstacle)
        self.dino.draw(surface, celebrating=self.victory or self.record_break, dying=self.game_over and not self.record_break)
        self._draw_title_bar(surface)
        self._draw_score(surface)
        if self.victory:
            self._draw_victory(surface)
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
        patterns = [
            [
                "000000111100000000000",
                "000011222211100000000",
                "001122222222111000000",
                "011222222222222110000",
                "112222122222222211100",
                "222221111222222222110",
                "022111001112222211110",
                "001100000011111100000",
            ],
            [
                "0000000111100000000000",
                "0000011222211000000000",
                "0001122222222111000000",
                "0112222221222221110000",
                "1122222111112222211100",
                "0222111000011122222110",
                "0011000000000111111000",
            ],
            [
                "00000111100000000000",
                "00011222211100000000",
                "01122222222111000000",
                "11222221122222111000",
                "22222110011222221110",
                "01111000000111111000",
            ],
        ][variant]
        palette = {
            "1": (142, 181, 215, 210),
            "2": (*config.CYBER_CLOUD, 230),
        }
        low = pygame.Surface((max(len(row) for row in patterns), len(patterns)), pygame.SRCALPHA)
        for y, row in enumerate(patterns):
            for x, value in enumerate(row):
                if value in palette:
                    low.set_at((x, y), palette[value])
        sprite = pygame.Surface((low.get_width() * 9 + 24, low.get_height() * 9 + 18), pygame.SRCALPHA)
        glow = _scale_pixel(low, 9)
        glow.fill(_rgba(config.CYBER_CLOUD_GLOW, 70), special_flags=pygame.BLEND_RGBA_MULT)
        for dx, dy in ((-8, 0), (8, 0), (0, -6), (0, 6)):
            sprite.blit(glow, (12 + dx, 9 + dy))
        sprite.blit(_scale_pixel(low, 9), (12, 9))
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
            pygame.draw.rect(floor, (16, 15, 36), (px, 0, PANEL_WIDTH - 3, GROUND_HEIGHT), 3)
            pygame.draw.rect(floor, PIXEL_SHADOW, (px + 8, 12, PANEL_WIDTH - 19, 12))
            pygame.draw.rect(floor, (27, 31, 60), (px + 16, 76, PANEL_WIDTH - 34, 18))
            pygame.draw.rect(floor, (22, 24, 49), (px + 28, GROUND_HEIGHT - 28, 28, 18))

            y_mid = 35 + ((x // PANEL_WIDTH) % 3) * 10
            points = [(px + 6, y_mid), (px + 32, y_mid), (px + 32, y_mid + 20), (px + 72, y_mid + 20), (px + 72, y_mid - 10), (px + 119, y_mid - 10)]
            for start, end in zip(points, points[1:]):
                _draw_neon_line(floor, config.CIRCUIT_LINE, start, end, 3)
            for point in points[1:-1]:
                _draw_neon_circle(floor, config.CIRCUIT_LINE, point, 3)

            accent = config.CIRCUIT_MAGENTA if (x // PANEL_WIDTH) % 3 == 0 else config.CIRCUIT_GREEN
            _draw_neon_line(floor, accent, (px + 18, 103), (px + 38, 103), 3)
            for led_x in (px + 78, px + 88, px + 98):
                pygame.draw.rect(floor, accent, (led_x, GROUND_HEIGHT - 23, 5, 5))
        surface.blit(floor, (0, config.GROUND_Y))
        pygame.draw.line(surface, OUTLINE, (0, config.GROUND_Y - 1), (config.WINDOW_WIDTH, config.GROUND_Y - 1), 4)
        _draw_neon_line(surface, config.CIRCUIT_LINE, (0, config.GROUND_Y + 15), (config.WINDOW_WIDTH, config.GROUND_Y + 15), 3)

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
        body = pygame.Rect(offset + r.w // 2 - 9, offset, 18, r.h)
        left = pygame.Rect(offset + 2, offset + r.h // 3, 18, r.h // 2)
        right = pygame.Rect(offset + r.w - 20, offset + r.h // 4, 18, r.h // 2)
        for shape in (body, left, right):
            pygame.draw.rect(fill, OUTLINE, shape.inflate(6, 6))
            pygame.draw.rect(fill, (36, 174, 125, 185), shape)
            pygame.draw.rect(fill, config.NEON_CYAN, shape, 3)
            _draw_neon_rect(fill, shape, config.NEON_CYAN, 2)
        surface.blit(fill, (r.x - offset, r.y - offset))

    def _draw_computer(self, surface, r):
        flicker = 150 + int((self.score * 18) % 70)
        pad = 16
        layer = pygame.Surface((r.w + pad * 2, r.h + pad * 2), pygame.SRCALPHA)
        monitor = pygame.Rect(pad + 3, pad + 2, r.w - 6, 45)
        screen = pygame.Rect(pad + 13, pad + 11, r.w - 26, 25)
        stand = pygame.Rect(pad + 29, pad + 47, 14, 9)
        case = pygame.Rect(pad + 8, pad + 55, r.w - 16, 20)
        keyboard = pygame.Rect(pad + 4, pad + 75, r.w + 22, 11)
        side = pygame.Rect(pad - 5, pad + 11, 12, 55)
        for rect, color in ((side, (76, 73, 126)), (monitor, (188, 194, 214)), (stand, (132, 137, 165)), (case, (160, 166, 190)), (keyboard, (215, 218, 226))):
            pygame.draw.rect(layer, OUTLINE, rect.inflate(6, 6))
            pygame.draw.rect(layer, color, rect)
            pygame.draw.rect(layer, (89, 94, 136), rect, 3)
        pygame.draw.rect(layer, _rgba(config.CRT_SCREEN, flicker), screen)
        pygame.draw.rect(layer, OUTLINE, screen, 3)
        _draw_neon_rect(layer, screen, config.CRT_SCREEN, 2)
        _draw_neon_line(layer, config.CRT_SCREEN, (screen.x + 7, screen.y + 14), (screen.x + 24, screen.y + 14), 2)
        pygame.draw.rect(layer, config.CIRCUIT_GREEN, (case.x + 13, case.y + 10, 5, 5))
        pygame.draw.rect(layer, config.CIRCUIT_GREEN, (case.x + 23, case.y + 10, 5, 5))
        for i in range(7):
            pygame.draw.rect(layer, (125, 129, 158), (keyboard.x + 10 + i * 8, keyboard.y + 3, 5, 4))
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
        camera_left = config.WINDOW_WIDTH - config.CAMERA_PREVIEW_WIDTH - config.CAMERA_MARGIN
        x = camera_left - text.get_width() - 28
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
        center_x = (config.WINDOW_WIDTH - config.CAMERA_PREVIEW_WIDTH - config.CAMERA_MARGIN * 3) // 2
        title_text = "NUEVO RECORD" if self.record_break else "SYSTEM HALTED"
        accent = config.CIRCUIT_GREEN if self.record_break else config.CIRCUIT_MAGENTA
        title = self.big_font.render(title_text, True, config.HUD_TEXT)
        prompt = self.font.render("Salta o presiona ESPACIO para reiniciar", True, config.NEON_CYAN)
        panel = pygame.Surface((620, 150), pygame.SRCALPHA)
        pygame.draw.rect(panel, (12, 14, 24, 190), panel.get_rect(), border_radius=6)
        _draw_neon_rect(panel, panel.get_rect().inflate(-4, -4), accent, 2, 6)
        surface.blit(panel, panel.get_rect(center=(center_x, 315)))
        surface.blit(title, title.get_rect(center=(center_x, 290)))
        surface.blit(prompt, prompt.get_rect(center=(center_x, 340)))

    def _draw_victory(self, surface):
        center_x = (config.WINDOW_WIDTH - config.CAMERA_PREVIEW_WIDTH - config.CAMERA_MARGIN * 3) // 2
        title = self.big_font.render("META SUPERADA", True, config.HUD_TEXT)
        prompt = self.font.render("Salta o presiona ESPACIO para jugar otra vez", True, config.NEON_CYAN)
        panel = pygame.Surface((680, 150), pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 18, 18, 170), panel.get_rect(), border_radius=6)
        _draw_neon_rect(panel, panel.get_rect().inflate(-4, -4), config.CIRCUIT_GREEN, 2, 6)
        surface.blit(panel, panel.get_rect(center=(center_x, 170)))
        surface.blit(title, title.get_rect(center=(center_x, 145)))
        surface.blit(prompt, prompt.get_rect(center=(center_x, 195)))

    def _lerp(self, a, b, t):
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
