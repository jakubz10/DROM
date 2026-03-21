# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

```bash
python game.py
```

Requires Python 3.10+ on **Windows only** — uses Win32 console APIs (`kernel32`, `user32`) via `ctypes`. No third-party packages needed.

## Architecture

The game is a Doom-style raycasting FPS rendered entirely through ANSI escape codes written directly to the Windows console via `WriteConsoleW`. There is no game engine, no display library, no assets on disk — everything is computed and drawn as coloured Unicode characters each frame.

### Frame loop (`game.py`)

`main()` runs a 30 FPS loop. Each tick:
1. `poll_input()` → raw Win32 key states (returns 7-tuple: `keys, shoot, flip, reload_key, quit_now, cheat_l5, killall`)
2. State machine dispatch: `splash` → `play` → `levelwin` / `dead` / `endgame`
3. Game logic (move, shoot, AI, pickups, wall breaks, win delay)
4. `build_frame(...)` → single giant ANSI string
5. `_wcon(fs)` → write string to console in one call

Game state is a plain `dict` (`g`). `new_game(level)` creates a fresh one. No classes wrap it.

**Campaign structure**: Levels 1–5 are the main campaign. After level 5 the `endgame` state is entered (skipping `levelwin`). The endgame menu (`build_endgame_menu`) offers W=infinite play, SPACE=main menu, ESC=quit. Levels beyond 5 reuse map 5 with increasing enemy count (`8 + (level-1)*4`).

### Rendering pipeline (`renderer.py`)

`build_frame(cols, rows, ...)` builds the entire frame as one string and returns it. It never writes to the console directly. The frame is assembled in layers:

1. **Sky** — gradient with stars (seeded per column) and a world-anchored moon
2. **Walls** — DDA raycasting column by column; wall height and colour from `WALL_RGB`
3. **Floor** — distance-shaded gradient below the horizon
4. **Sprites** — enemies and pickups sorted by distance, projected and UV-mapped
5. **Wall explosions** — rendered directly with `_goto` after the main pixel loop (not via `spr` buffer) so they are never clipped
6. **Compass** — top 2 rows: scrolling N/NE/E/SE… strip + enemy blips
7. **HUD** — bottom rows: HP, ammo, kills, FPS, minimap, gun sprite, crosshair, messages; blinking dot in bottom-left corner

The moon position is precomputed once per frame as a screen column (`_moon_sc`) from the player's world angle before the sky pixel loop runs.

**`build_frame` extra parameters** (beyond cols/rows/game-state basics):
- `gun_upgrade_anim` — float 0–1.5; drives a golden screen flash when a gun upgrade is collected
- `wall_hp` — dict `{(mx,my): shots_remaining}`; used to render wall crack textures
- `win_delay_t` — float 0–3; drives wall-sinking and floor-reddening effects during the 3s level-win pause

**Wall sinking (win delay):** `_dissolve_r` grows from 0 outward as `win_delay_t` falls. Walls within that radius have their `top` raised toward `bot`; fully sunk walls also set `z_buf[col]=99.0` so sprites behind them stay visible.

**Floor ink spill (win delay):** Per-pixel noise seed `((col*1481 + row*3761) & 0xFF)` shifts the red frontier from the player's feet toward the horizon as `_floor_red` increases from 0→1.

**Enemy damage tinting:** Applied only when `e.pain_t <= 0` (skips white pain flash). Scales from `_max_hp` (16 for boss, 3 for regular) — darkens and shifts toward red as HP drops.

**Wall crack texture:** Seed `(col*1481 + rel*3761 + mx_hit*29 + my_hit*67) & 0xFF` gives a deterministic per-pixel value. Three damage tiers (>0, >30%, >60% of `WALL_SHOTS`) use uniform `_dk` multipliers (0.84/0.74/0.62) so cracks stay close to the wall's own colour.

**`wall_cell` tuple layout (18 elements):** `base_ch, fr, fg2, fb, br, bg2, bb, top, bot, col_c, is_outer, side, dist, dalpha, ch, wt_cell, mx_hit, my_hit`

### Raycasting (`raycaster.py`)

`cast_ray(px, py, angle)` → `(distance, side, wall_type)` using DDA. Returns `99.0` on miss.
`has_los(ax, ay, bx, by)` — linear sample for enemy sight checks.
`FOV = π/3` (60°).

### Enemy AI (`enemy.py`)

`Enemy` and `Boss(Enemy)` use `__slots__` throughout. AI is a 5-state machine per entity: `patrol → alert → chase → strafe → search`. State transitions and actions are separate methods (`_do_patrol`, `_do_chase`, etc.).

**Critical `__slots__` note**: `Boss` declares only its *additional* slot `('_wall_break_cd',)` — Python merges parent and child slots automatically. Adding new attributes to either class requires updating the corresponding `__slots__` tuple.

`Boss._break_wall_toward()` mutates `WORLD_MAP[my][mx] = 0` directly and appends to `WALL_BREAKS` (an event queue in `map_data`). `game.py` drains `WALL_BREAKS` each frame to spawn explosion visuals.

### Map data (`map_data.py`)

`WORLD_MAP` is a mutable 2D list (list of lists of ints). All imports share the **same list object** — mutations (wall destruction) are immediately visible everywhere without re-import.

Wall types: `0` = floor, `1–4` = destructible castle walls, `5` = indestructible outer wall.
`load_map(level)` replaces the contents of `WORLD_MAP` **in-place** (`.clear()` + `.extend()`) to preserve references.

`WAYPOINTS` and `WALL_BREAKS` follow the same in-place mutation pattern.

### Assets and constants

| File | Purpose |
|------|---------|
| `assets.py` | Gun sprite template, all colour constants, minimap chars, HUD colours |
| `text.py` | Every player-facing string in one `TEXT` dict |
| `console.py` | Win32 handles, `_wcon()`, `_fg()/_bg()` ANSI colour helpers (cached) |

All colour constants live in `assets.py` and are imported by name into `renderer.py`. When adding new visual elements, add colours there first.

### Pickup system (`pickups.py`)

`HealthPack`, `AmmoCrate`, `GunUpgrade` are simple `__slots__` objects with `x`, `y`, `active`. Pickup logic (proximity check, stat mutation) lives entirely in `game.py`'s play loop, not in the pickup classes.

## Key Constants

| Constant | Location | Value | Meaning |
|---|---|---|---|
| `FOV` | `raycaster.py` | `π/3` | Camera field of view |
| `MAG_SIZE` | `game.py` | `16` | Bullets per magazine |
| `MAX_RESERVE` | `game.py` | `32` | Max reserve ammo |
| `WALL_SHOTS` | `game.py` | `8` | Shots to destroy a type 1-4 wall |
| `RELOAD_TIME` | `game.py` | `1.2s` | Reload animation duration |
| `MOVE_SPEED` | `game.py` | `3.8` | Player tiles/sec |
| `MELEE_DAMAGE` (Enemy) | `enemy.py` | `22.0` | Normal drom damage/sec |
| `MELEE_DAMAGE` (Boss) | `enemy.py` | `44.0` | Boss damage/sec (2×) |
| `_MOON_WORLD_A` | `renderer.py` | `1.1 rad` | Fixed world angle of the moon |
| `_WIN_DELAY_TOTAL` | `renderer.py` | `3.0s` | Duration of wall-sink/floor-red win effect |
| `_SINK_ZONE` | `renderer.py` | `5.0 tiles` | Radius over which wall sinking fades in |
| `gun_upgrade_anim` | `game.py` state | `0–1.5` | Countdown for golden gun-upgrade screen flash |
| `VK_Y` | `input.py` | `0x59` | Dev key: instantly kill all enemies |

## Adding a New Level

1. Add `_MAP_N` to `map_data.py` (same 2D list format, `5`-bordered)
2. Add matching `_WAYPOINTS_N` list of `(x, y)` patrol points
3. Extend `_MAPS` and `_WAYPOINTS_BY_LEVEL` dicts with the new level index
4. `load_map(level)` handles everything else automatically

## Rendering New Sprites

Sprites are rendered in `build_frame` by projecting world `(x, y)` to screen column/height, then iterating a UV grid (`tx` 0→1 left-to-right, `ty` 0→1 top-to-bottom). The sprite pixel loop in `renderer.py` is the place to add per-pixel logic. Walking animation uses `math.sin(time * 7.0 + e.eid * 1.9)` for per-enemy phase offset.
