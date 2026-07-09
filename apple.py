import pygame
from pygame.locals import *
import random

APPLE_KINDS = {
    "normal": {"color": (255, 0, 0),   "points": 10, "growth": 1,  "weight": 70, "ttl_ms": 7000},
    "golden": {"color": (255, 215, 0), "points": 30, "growth": 1,  "weight": 12, "ttl_ms": 4000},
    "shrink": {"color": (150, 90, 220), "points": 5, "growth": -1, "weight": 18, "ttl_ms": 6000},
}

BLINK_WARNING_MS = 1500  

class Apple():

    def __init__(self):
        self.surface = pygame.Surface((10, 10))
        self.kind = "normal"
        self.position = (0, 0)
        self.spawn_tick = 0
        self._apply_kind_color()

    def _apply_kind_color(self):
        self.surface.fill(APPLE_KINDS[self.kind]["color"])

    @property
    def apple(self):
        
        return self.surface

    @property
    def points(self):
        return APPLE_KINDS[self.kind]["points"]

    @property
    def growth(self):
        return APPLE_KINDS[self.kind]["growth"]

    @property
    def ttl_ms(self):
        return APPLE_KINDS[self.kind]["ttl_ms"]

    def _pick_kind(self):
        kinds = list(APPLE_KINDS.keys())
        weights = [APPLE_KINDS[k]["weight"] for k in kinds]
        return random.choices(kinds, weights=weights, k=1)[0]

    def set_random_position(self, screen_size, blocked_cells=None):
       
        blocked_cells = blocked_cells or []
        self.kind = self._pick_kind()
        self._apply_kind_color()
        while True:
            pos = (random.randrange(0, screen_size, 10),
                   random.randrange(0, screen_size, 10))
            if pos not in blocked_cells:
                self.position = pos
                break
        self.spawn_tick = pygame.time.get_ticks()

    def is_expired(self):
        return pygame.time.get_ticks() - self.spawn_tick >= self.ttl_ms

    def is_blinking(self):
        
        remaining = self.ttl_ms - (pygame.time.get_ticks() - self.spawn_tick)
        return 0 < remaining <= BLINK_WARNING_MS

    def is_visible(self):
        if not self.is_blinking():
            return True
        # Flash a few times per second during the warning window.
        return (pygame.time.get_ticks() // 150) % 2 == 0
