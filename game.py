import random
from dataclasses import dataclass

import pygame

import config


WHITE = (247, 247, 247)
DARK = (45, 45, 45)
MID = (96, 96, 96)
SKY = (250, 250, 250)
ACCENT = (25, 145, 95)


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


class Dino:
    def __init__(self):
        self.y = config.GROUND_Y - config.DINO_HEIGHT
        self.vy = 0.0
        self.ducking = False
        self.on_ground = True
        self.step_timer = 0.0

    @property
    def rect(self):
        h = config.DINO_DUCK_HEIGHT if self.ducking and self.on_ground else config.DINO_HEIGHT
        w = config.DINO_DUCK_WIDTH if self.ducking and self.on_ground else config.DINO_WIDTH
        return pygame.Rect(config.DINO_X, int(config.GROUND_Y - h if self.on_ground and self.ducking else self.y), w, h)

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
        pygame.draw.rect(surface, DARK, r, border_radius=4)
        if self.ducking and self.on_ground:
            pygame.draw.rect(surface, DARK, (r.right - 12, r.y - 8, 18, 16), border_radius=3)
            pygame.draw.circle(surface, WHITE, (r.right - 5, r.y - 3), 3)
        else:
            pygame.draw.rect(surface, DARK, (r.right - 16, r.y - 18, 24, 24), border_radius=4)
            pygame.draw.circle(surface, WHITE, (r.right + 1, r.y - 10), 3)
        leg_offset = 8 if int(self.step_timer * 12) % 2 == 0 else 24
        pygame.draw.line(surface, DARK, (r.x + 14, r.bottom), (r.x + leg_offset, r.bottom + 16), 5)
        pygame.draw.line(surface, DARK, (r.x + 36, r.bottom), (r.x + 46 - leg_offset // 2, r.bottom + 16), 5)


class Game:
    def __init__(self, font, big_font):
        self.font = font
        self.big_font = big_font
        self.high_score = 0
        self.reset()

    def reset(self):
        self.dino = Dino()
        self.obstacles = []
        self.speed = config.START_SPEED
        self.score = 0
        self.distance_to_next = random.randint(config.OBSTACLE_MIN_GAP, config.OBSTACLE_MAX_GAP)
        self.game_over = False
        self.ground_phase = 0.0
        self.clouds = [[random.randint(0, config.WINDOW_WIDTH), random.randint(70, 240)] for _ in range(5)]

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
        self.ground_phase = (self.ground_phase + self.speed * dt) % 48
        self.dino.update(dt, ducking)

        for cloud in self.clouds:
            cloud[0] -= 28 * dt
            if cloud[0] < -90:
                cloud[0] = config.WINDOW_WIDTH + random.randint(40, 240)
                cloud[1] = random.randint(70, 240)

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
        surface.fill(SKY)
        self._draw_clouds(surface)
        pygame.draw.line(surface, MID, (0, config.GROUND_Y), (config.WINDOW_WIDTH, config.GROUND_Y), 3)
        for x in range(-48, config.WINDOW_WIDTH + 48, 48):
            px = x - int(self.ground_phase)
            pygame.draw.line(surface, (170, 170, 170), (px, config.GROUND_Y + 18), (px + 18, config.GROUND_Y + 18), 2)
        for obstacle in self.obstacles:
            self._draw_obstacle(surface, obstacle)
        self.dino.draw(surface)
        self._draw_score(surface)
        if self.game_over:
            self._draw_game_over(surface)

    def _spawn_obstacle(self):
        kind = random.choices(["cactus", "bird_low", "bird_high"], weights=[0.62, 0.25, 0.13])[0]
        if kind == "cactus":
            w = random.choice([34, 48, 64])
            h = random.choice([58, 72, 86])
            self.obstacles.append(Obstacle(kind, config.WINDOW_WIDTH + 20, config.GROUND_Y - h, w, h))
        elif kind == "bird_low":
            self.obstacles.append(Obstacle(kind, config.WINDOW_WIDTH + 20, config.GROUND_Y - 92, 62, 38))
        else:
            self.obstacles.append(Obstacle(kind, config.WINDOW_WIDTH + 20, config.GROUND_Y - 165, 62, 38))

    def _draw_obstacle(self, surface, obstacle):
        r = obstacle.rect
        if obstacle.kind == "cactus":
            pygame.draw.rect(surface, ACCENT, r, border_radius=6)
            pygame.draw.rect(surface, ACCENT, (r.x - 13, r.y + 18, 16, 36), border_radius=5)
            pygame.draw.rect(surface, ACCENT, (r.right - 3, r.y + 28, 16, 32), border_radius=5)
        else:
            wing = 10 if int(self.score * 2) % 2 == 0 else -10
            pygame.draw.ellipse(surface, DARK, r)
            pygame.draw.polygon(surface, DARK, [(r.x + 20, r.centery), (r.x - 18, r.centery + wing), (r.x + 14, r.centery + 8)])
            pygame.draw.polygon(surface, DARK, [(r.x + 40, r.centery), (r.right + 18, r.centery - wing), (r.x + 46, r.centery + 8)])
            pygame.draw.circle(surface, WHITE, (r.right - 13, r.y + 12), 3)

    def _draw_clouds(self, surface):
        for x, y in self.clouds:
            pygame.draw.circle(surface, (214, 214, 214), (int(x), y), 14, 2)
            pygame.draw.circle(surface, (214, 214, 214), (int(x + 18), y - 9), 18, 2)
            pygame.draw.circle(surface, (214, 214, 214), (int(x + 42), y), 14, 2)
            pygame.draw.line(surface, (214, 214, 214), (x - 12, y + 14), (x + 58, y + 14), 2)

    def _draw_score(self, surface):
        text = self.font.render(f"HI {self.high_score:05d}  {int(self.score):05d}", True, DARK)
        surface.blit(text, (config.WINDOW_WIDTH - text.get_width() - 24, 24))

    def _draw_game_over(self, surface):
        title = self.big_font.render("GAME OVER", True, DARK)
        prompt = self.font.render("Salta o presiona ESPACIO para reiniciar", True, MID)
        surface.blit(title, title.get_rect(center=(config.WINDOW_WIDTH // 2, 280)))
        surface.blit(prompt, prompt.get_rect(center=(config.WINDOW_WIDTH // 2, 330)))
