# What changed

## Latest round: timed apples, obstacles, apple types, themes, screen shake, resizable board

All configured from the start screen before you press an arrow key to begin:
- **B** — cycle board size (Small 300 / Medium 400 / Large 500)
- **W** — toggle wrap mode
- **O** — toggle obstacles mode
- **T** — cycle theme (Classic / Neon / Retro)

**Timed apples** — every apple now has a lifespan; if it's not eaten in time it
vanishes and reappears elsewhere (no penalty, no points). It flashes for its
last 1.5 seconds as a warning.

**Multiple apple types**, chosen randomly each spawn:
- Red (**normal**) — +10 points, grow by 1, most common.
- Gold (**golden**) — +30 points, grow by 1, rare, expires fastest.
- Purple (**shrink**) — +5 points, removes one segment — useful to slim down
  in a tight spot, but be deliberate about grabbing it.

**Obstacles mode** — scatters random blocks on the board (count scales with
board size). Hitting one ends the run just like a wall, regardless of wrap
mode. A short safe lane in front of the snake's start is always kept clear.

**Themes** — Classic (black/white), Neon (dark navy + green/cyan), and Retro
(Game Boy–style green). Swaps grid, background, snake, and obstacle colors.

**Screen shake** — a brief shake plays on the final frame right before the
"Game Over" screen appears.

**Resizable board** — pick Small/Medium/Large before starting; the snake
always spawns centered regardless of size.

### Bug fix that came along with this round
Sound effect variables (`eat_sound`, `toggle_sound`, etc.) would raise a
`NameError` if no audio device was available, even though the code was meant
to silently skip sound in that case. They now default to `None` and are
skipped safely.

## Earlier rounds
- Apple no longer spawns inside the snake's body (or, now, inside obstacles).
- Removed a leftover debug `print()` that was spamming the console.
- Swapped `pygame.font.SysFont("arial", ...)` for pygame's bundled default
  font, since `SysFont` depends on fonts installed on the OS.
- Speed is capped so the game doesn't become physically unplayable.
- Persistent high score, saved to `highscore.txt` next to the game.
- Start screen instead of dropping straight into gameplay.
- Grid background during play.
- Movement decoupled from rendering: the game always renders at a smooth 60
  FPS, with a time accumulator deciding when a grid-step happens. The snake
  now glides between cells instead of snapping.
- Only one direction change accepted per grid-step, so rapid double key-taps
  can no longer let the snake reverse into its own neck.
- Sound effects (eat / game over / setting toggles) generated entirely in
  code — no audio files needed.
- Wrap-around mode as an alternate ruleset.

## Ideas for next steps
- Local leaderboard (top 5 scores with initials) instead of a single high score.
- Difficulty presets (Easy/Normal/Hard) bundling start speed + max speed.
- Two-player mode.
- Replay/ghost mode racing your best run.

