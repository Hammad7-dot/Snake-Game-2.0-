import pygame
import os
import io
import math
import random
import struct
import wave
from pygame.locals import *
from snake import *
from apple import *


GRID_SIZE = 10
START_SPEED = 10
MAX_SPEED = 25
RENDER_FPS = 60  
SHAKE_DURATION_MS = 260
SHAKE_MAGNITUDE = 6

BOARD_SIZES = [("Small", 300), ("Medium", 400), ("Large", 500)]
DEFAULT_BOARD_INDEX = 1

THEMES = {
    "Classic": {
        "bg": (0, 0, 0), "grid": (25, 25, 25),
        "snake": (255, 255, 255), "head": (200, 200, 200),
        "text": (255, 255, 255), "muted": (150, 150, 150),
        "obstacle": (90, 90, 90),
    },
    "Neon": {
        "bg": (8, 8, 22), "grid": (28, 22, 45),
        "snake": (0, 255, 140), "head": (0, 255, 255),
        "text": (230, 230, 255), "muted": (120, 110, 170),
        "obstacle": (255, 0, 150),
    },
    "Retro": {
        "bg": (15, 56, 15), "grid": (25, 70, 25),
        "snake": (155, 188, 15), "head": (200, 220, 80),
        "text": (224, 248, 208), "muted": (110, 150, 90),
        "obstacle": (60, 100, 60),
    },
}
THEME_NAMES = list(THEMES.keys())

HIGH_SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.txt")
SOUND_SAMPLE_RATE = 22050


pygame.init()
try:
    pygame.mixer.init(frequency=SOUND_SAMPLE_RATE, size=-16, channels=1)
    SOUND_AVAILABLE = True
except pygame.error:
    # No audio device available (e.g. some headless/CI environments).
    # The game still runs fine, just silently.
    SOUND_AVAILABLE = False

pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()

font = pygame.font.Font(None, 28)
small_font = pygame.font.Font(None, 22)



def generate_tone(frequency=440, duration_ms=120, volume=0.35, fade_out=True):
    """Generate a short sine-wave tone in memory and return a pygame Sound."""
    n_samples = int(SOUND_SAMPLE_RATE * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SOUND_SAMPLE_RATE)
        for i in range(n_samples):
            fade = (1.0 - i / n_samples) if fade_out else 1.0
            value = volume * fade * math.sin(2 * math.pi * frequency * i / SOUND_SAMPLE_RATE)
            wf.writeframes(struct.pack("<h", int(value * 32767)))
    buf.seek(0)
    return pygame.mixer.Sound(buf)


def generate_two_tone(freq1, freq2, duration_ms=140, volume=0.35):
    """Generate a two-note tone (used for game over)."""
    n_samples = int(SOUND_SAMPLE_RATE * duration_ms / 1000)
    half = n_samples // 2
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SOUND_SAMPLE_RATE)
        for i in range(n_samples):
            freq = freq1 if i < half else freq2
            fade = 1.0 - i / n_samples
            value = volume * fade * math.sin(2 * math.pi * freq * i / SOUND_SAMPLE_RATE)
            wf.writeframes(struct.pack("<h", int(value * 32767)))
    buf.seek(0)
    return pygame.mixer.Sound(buf)


if SOUND_AVAILABLE:
    eat_sound = generate_tone(frequency=880, duration_ms=90, volume=0.35)
    golden_sound = generate_tone(frequency=1200, duration_ms=110, volume=0.4)
    shrink_sound = generate_tone(frequency=480, duration_ms=140, volume=0.3)
    gameover_sound = generate_two_tone(300, 140, duration_ms=350, volume=0.4)
    toggle_sound = generate_tone(frequency=520, duration_ms=60, volume=0.25)
else:
  
    eat_sound = golden_sound = shrink_sound = gameover_sound = toggle_sound = None

apple_sounds = {"normal": eat_sound, "golden": golden_sound, "shrink": shrink_sound}


def play_sound(sound):
    if SOUND_AVAILABLE and sound is not None:
        sound.play()


def load_high_score():
    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return int(f.read().strip())
        except (ValueError, OSError):
            return 0
    return 0


def save_high_score(value):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(value))
    except OSError:
        pass


high_score = load_high_score()



board_size_index = DEFAULT_BOARD_INDEX
WRAP_MODE = False       
OBSTACLES_MODE = False  
theme_index = 0


def current_theme():
    return THEMES[THEME_NAMES[theme_index]]


def apply_board_size():
    
    global WIDTH, HEIGHT, screen, game_surface
    WIDTH = HEIGHT = BOARD_SIZES[board_size_index][1]
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    game_surface = pygame.Surface((WIDTH, HEIGHT))


apply_board_size()


def generate_obstacles(width, height, snake_body):
    
    total_cells = (width // GRID_SIZE) * (height // GRID_SIZE)
    count = max(6, min(40, total_cells // 18))

    head_x, head_y = snake_body[-1]
    safe_zone = set(snake_body)
    for i in range(1, 6):
        safe_zone.add((head_x + i * GRID_SIZE, head_y))

    obstacles = set()
    attempts = 0
    while len(obstacles) < count and attempts < count * 25:
        attempts += 1
        pos = (random.randrange(0, width, GRID_SIZE), random.randrange(0, height, GRID_SIZE))
        if pos in safe_zone or pos in obstacles:
            continue
        obstacles.add(pos)
    return obstacles



def reset_game():
    global snake, apple, obstacles, SPEED, score, GAME_ON, paused, STARTED
    global move_timer, prev_snake_positions, next_direction, direction_locked
    global shake_end_tick

    snake = Snake(WIDTH, HEIGHT, GRID_SIZE)
    obstacles = generate_obstacles(WIDTH, HEIGHT, snake.snake) if OBSTACLES_MODE else set()
    apple = Apple()
    apple.set_random_position(WIDTH, list(snake.snake) + list(obstacles))

    SPEED = START_SPEED
    score = 0
    GAME_ON = True
    paused = False
    STARTED = True

    move_timer = 0.0
    prev_snake_positions = list(snake.snake)
    next_direction = snake.direction
    direction_locked = False
    shake_end_tick = 0


# Initial (pre-game) state, shown as the start screen until the player begins.
snake = Snake(WIDTH, HEIGHT, GRID_SIZE)
obstacles = set()
apple = Apple()
apple.set_random_position(WIDTH, snake.snake)
SPEED = START_SPEED
score = 0
GAME_ON = True
paused = False
STARTED = False
shake_end_tick = 0
move_timer = 0.0
prev_snake_positions = list(snake.snake)
next_direction = snake.direction
direction_locked = False


# ------------------ DRAW HELPERS ------------------
def get_render_positions(move_interval):
    """
    Returns the snake's segment positions to actually draw this frame,
    smoothly interpolated between where they were before the last grid-step
    and where they are now. Falls back to exact (snapped) positions right
    after growth/shrink (list length changed) or on a wrap teleport, since
    interpolating across those would look like a visual glitch.
    """
    current = snake.snake
    if len(prev_snake_positions) != len(current) or move_interval <= 0:
        return list(current)

    alpha = min(move_timer / move_interval, 1.0)
    rendered = []
    for (px, py), (cx, cy) in zip(prev_snake_positions, current):
        dx, dy = cx - px, cy - py
        if abs(dx) > GRID_SIZE or abs(dy) > GRID_SIZE:
            # Wrap-around teleport: don't slide across the whole board.
            rendered.append((cx, cy))
        else:
            rendered.append((px + dx * alpha, py + dy * alpha))
    return rendered


def get_shake_offset(now):
    remaining = shake_end_tick - now
    if remaining <= 0:
        return (0, 0)
    frac = remaining / SHAKE_DURATION_MS
    mag = int(SHAKE_MAGNITUDE * frac)
    if mag <= 0:
        return (0, 0)
    return (random.randint(-mag, mag), random.randint(-mag, mag))


def draw_grid(surface, theme):
    for x in range(0, WIDTH, GRID_SIZE):
        pygame.draw.line(surface, theme["grid"], (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, GRID_SIZE):
        pygame.draw.line(surface, theme["grid"], (0, y), (WIDTH, y))


def draw_obstacles(surface, theme):
    for ox, oy in obstacles:
        pygame.draw.rect(surface, theme["obstacle"], (ox, oy, GRID_SIZE, GRID_SIZE))


def draw_snake(surface, positions, theme):
    for x, y in positions[:-1]:
        pygame.draw.rect(surface, theme["snake"], (round(x), round(y), GRID_SIZE, GRID_SIZE))
    hx, hy = positions[-1]
    pygame.draw.rect(surface, theme["head"], (round(hx), round(hy), GRID_SIZE, GRID_SIZE))


def draw_score(surface, theme):
    score_text = font.render(f"Score: {score}", True, theme["text"])
    surface.blit(score_text, (10, 10))
    hs_text = small_font.render(f"Best: {high_score}", True, theme["muted"])
    surface.blit(hs_text, (WIDTH - hs_text.get_width() - 10, 14))

    tag_x = 10
    tag_y = HEIGHT - 24
    if WRAP_MODE:
        tag = small_font.render("WRAP", True, theme["snake"])
        surface.blit(tag, (tag_x, tag_y))
        tag_x += tag.get_width() + 10
    if OBSTACLES_MODE:
        tag = small_font.render("OBST", True, theme["obstacle"])
        surface.blit(tag, (tag_x, tag_y))


def pause_screen(surface, theme):
    text = font.render("Paused - Press P to Resume", True, theme["text"])
    surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))


def draw_game_frame(surface, positions, theme):
    surface.fill(theme["bg"])
    draw_grid(surface, theme)
    if OBSTACLES_MODE:
        draw_obstacles(surface, theme)
    if apple.is_visible():
        surface.blit(apple.apple, apple.position)
    draw_snake(surface, positions, theme)
    draw_score(surface, theme)
    if paused:
        pause_screen(surface, theme)


def start_screen():
    theme = current_theme()
    screen.fill(theme["bg"])

    title = font.render("SNAKE", True, theme["snake"])
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 14))
    y = 14 + title.get_height() + 10

    def line(text, color=None):
        nonlocal y
        surf = small_font.render(text, True, color or theme["text"])
        screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))
        y += surf.get_height() + 4

    line("Press an arrow key to start")
    line("")
    line(f"Board: {BOARD_SIZES[board_size_index][0]}  (B)", theme["muted"])
    line(f"Wrap Mode: {'ON' if WRAP_MODE else 'OFF'}  (W)",
         theme["snake"] if WRAP_MODE else theme["muted"])
    line(f"Obstacles: {'ON' if OBSTACLES_MODE else 'OFF'}  (O)",
         theme["obstacle"] if OBSTACLES_MODE else theme["muted"])
    line(f"Theme: {THEME_NAMES[theme_index]}  (T)", theme["muted"])
    line("")
    line("P = Pause    Esc = Quit", theme["muted"])
    line(f"Best: {high_score}", theme["muted"])

    pygame.display.update()


def game_over_screen():
    theme = current_theme()
    screen.fill(theme["bg"])
    over_text = font.render("GAME OVER", True, (220, 60, 60))
    score_text = font.render(f"Final Score: {score}", True, theme["text"])
    hs_text = small_font.render(f"Best: {high_score}", True, theme["muted"])
    restart_text = font.render("Press R to Restart", True, theme["text"])

    screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 70))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 30))
    screen.blit(hs_text, (WIDTH // 2 - hs_text.get_width() // 2, HEIGHT // 2))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 40))
    pygame.display.update()


# ------------------ GAME LOOP ------------------
running = True
while running:
    dt = clock.tick(RENDER_FPS) / 1000.0  # seconds since last frame

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False

            if not STARTED:
                if event.key == K_w:
                    WRAP_MODE = not WRAP_MODE
                    play_sound(toggle_sound)
                elif event.key == K_o:
                    OBSTACLES_MODE = not OBSTACLES_MODE
                    play_sound(toggle_sound)
                elif event.key == K_t:
                    theme_index = (theme_index + 1) % len(THEME_NAMES)
                    play_sound(toggle_sound)
                elif event.key == K_b:
                    board_size_index = (board_size_index + 1) % len(BOARD_SIZES)
                    apply_board_size()
                    play_sound(toggle_sound)
                elif event.key in (K_UP, K_DOWN, K_LEFT, K_RIGHT):
                    reset_game()  # (re)builds everything using the chosen settings
                continue

            if event.key == K_p and GAME_ON:
                paused = not paused

            if event.key == K_r and not GAME_ON:
                reset_game()

            if GAME_ON and not paused and not direction_locked:
                new_dir = None
                if event.key == K_UP and next_direction != DOWN:
                    new_dir = UP
                elif event.key == K_LEFT and next_direction != RIGHT:
                    new_dir = LEFT
                elif event.key == K_DOWN and next_direction != UP:
                    new_dir = DOWN
                elif event.key == K_RIGHT and next_direction != LEFT:
                    new_dir = RIGHT

                if new_dir is not None:
                    next_direction = new_dir
                    direction_locked = True

    if not STARTED:
        start_screen()
        continue

    move_interval = 1.0 / SPEED

    if GAME_ON and not paused:
        move_timer += dt

        # Usually runs at most once per frame since RENDER_FPS is well above
        # SPEED, but the while loop catches up gracefully if a frame lags.
        while move_timer >= move_interval:
            move_timer -= move_interval
            prev_snake_positions = list(snake.snake)
            snake.direction = next_direction
            snake.crawl()

            if WRAP_MODE:
                snake.wrap(WIDTH)
                died = snake.self_collision()
            else:
                died = snake.wall_collision(WIDTH) or snake.self_collision()

            if OBSTACLES_MODE and snake.snake[-1] in obstacles:
                died = True

            if died:
                GAME_ON = False
                play_sound(gameover_sound)
                shake_end_tick = pygame.time.get_ticks() + SHAKE_DURATION_MS
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)

            elif snake.snake_eat_apple(apple.position):
                eaten_kind = apple.kind
                eaten_growth = apple.growth
                eaten_points = apple.points

                if eaten_growth > 0:
                    snake.snake_bigger()
                elif eaten_growth < 0:
                    snake.shrink()

                score += eaten_points
                SPEED = min(SPEED + 0.5, MAX_SPEED)
                move_interval = 1.0 / SPEED
                play_sound(apple_sounds.get(eaten_kind))

                blocked = list(snake.snake) + (list(obstacles) if OBSTACLES_MODE else [])
                apple.set_random_position(WIDTH, blocked)

            direction_locked = False

            if not GAME_ON:
                break

        # Timed apples: if it's been sitting too long, it vanishes and
        # reappears elsewhere (no points either way).
        if GAME_ON and apple.is_expired():
            blocked = list(snake.snake) + (list(obstacles) if OBSTACLES_MODE else [])
            apple.set_random_position(WIDTH, blocked)

    # ------------------ DRAW ------------------
    now = pygame.time.get_ticks()

    if GAME_ON or now < shake_end_tick:
        theme = current_theme()
        render_positions = get_render_positions(move_interval)
        draw_game_frame(game_surface, render_positions, theme)

        offset = get_shake_offset(now)
        screen.fill(theme["bg"])
        screen.blit(game_surface, offset)
        pygame.display.update()
    else:
        game_over_screen()

pygame.quit()
