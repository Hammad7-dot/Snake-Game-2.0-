import pygame
from pygame.locals import *

UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3


class Snake():

    def __init__(self, width=400, height=400, grid_size=10):
        # Start as a horizontal 5-segment line, centered on the board,
        # so this works for any board size (small/medium/large).
        center_row = (height // 2 // grid_size) * grid_size
        start_col = (width // 2 // grid_size) * grid_size - 2 * grid_size
        self.snake = [(start_col + i * grid_size, center_row) for i in range(5)]
        self.direction = RIGHT

    def crawl(self):
        head_x, head_y = self.snake[-1]

        if self.direction == RIGHT:
            new_head = (head_x + 10, head_y)
        elif self.direction == UP:
            new_head = (head_x, head_y - 10)
        elif self.direction == DOWN:
            new_head = (head_x, head_y + 10)
        elif self.direction == LEFT:
            new_head = (head_x - 10, head_y)

        self.snake.append(new_head)
        self.snake.pop(0)

    def self_collision(self):
        return self.snake[-1] in self.snake[0:-1]

    def wall_collision(self, screen_size):
        head_x, head_y = self.snake[-1]
        return head_x >= screen_size or head_x < 0 or head_y >= screen_size or head_y < 0

    def wrap(self, screen_size):
        """Wrap the head to the opposite edge instead of dying on wall contact."""
        head_x, head_y = self.snake[-1]
        self.snake[-1] = (head_x % screen_size, head_y % screen_size)

    def snake_eat_apple(self, apple_pos):
        return self.snake[-1] == apple_pos

    def snake_bigger(self):
        self.snake.insert(0, self.snake[0])

    def shrink(self):
        """Removes one segment from the tail end (used by 'shrink' apples)."""
        if len(self.snake) > 1:
            self.snake.pop(0)
