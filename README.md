# 🎮 DROM — Terminal FPS

> A retro raycasting first-person shooter that runs entirely inside your Windows terminal.

---

## 🖥️ What is DROM?

**DROM** is a Doom-style FPS built in pure Python, rendered with ANSI escape codes directly in the Windows console. No GPU, no window, no dependencies — just your terminal and a keyboard.

---

## ✨ Features

- 🏰 **Raycasting engine** — classic Wolfenstein-style 3D rendering at 30 FPS
- 👾 **Drom enemies** — patrol, chase, strafe, search and hear you
- 💀 **Boss Drom** — 16 HP, 2× damage, **smashes through walls** to reach you
- 🔫 **Shooting & reloading** — magazine + reserve ammo, manual reload
- ⬆️ **Gun upgrade** — pick up for double-shot spread fire
- 🧱 **Destructible walls** — shoot type 1–4 walls 8 times to break them
- 💣 **Wall explosions** — large burst visual when walls are destroyed
- 🌙 **World-anchored moon** — sits fixed in the sky as you turn
- ⭐ **Bright stars** — always visible twinkling starfield
- 🗡️ **3D spears** — enemies hold shaded spears; boss tips glow gold-red
- 🚶 **Walking animation** — droms bob as they move; boss tracks eyes toward you
- ❤️ **Health packs & ammo crates** — scattered across the map
- 🏰 **Medieval castle walls** — sandstone, dark slate, mossy iron, torchlit amber, battlements
- 🎯 **Multi-level progression** — enemies increase each level; bosses spawn after clearing droms
- 💥 **3-second win delay** — stay in the action after the last boss dies before level ends
- 🔑 **Hidden cheat code** — press `U` on the title screen to jump to level 5

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| `W` | Move forward |
| `S` | Move backward |
| `A` | Strafe left |
| `D` | Strafe right |
| `Q` / `←` | Turn left |
| `E` / `→` | Turn right |
| `↑` / `↓` | 180° flip |
| `SPACE` | Shoot |
| `R` | Reload |
| `ESC` / `BACKSPACE` | Quit |
| `U` *(title screen)* | 🔓 Secret: start at level 5 |

---

## 🧠 Enemy Behaviour

| State | Behaviour |
|-------|-----------|
| 🔵 Patrol | Walks waypoints around the map |
| 🟡 Alert | Spots you — pauses briefly before charging |
| 🔴 Chase | Runs toward your last known position |
| 🟠 Strafe | Circles you at knife range |
| ⚪ Search | Investigates last heard noise |

**Boss Drom extras:**
- 👁️ Eyes track your position
- 🧱 Smashes through walls when you're out of sight or when stuck
- 💢 2× melee damage (44 dmg/s vs normal drom's 22)
- 🔥 Big explosion on death

---

## 🗺️ Map & Levels

- 🏰 Castle layout with 5 wall types (1 = sandstone, 2 = dark slate, 3 = mossy iron, 4 = torchlit, 5 = indestructible battlements)
- 📈 Enemies scale: Level 1 = 8 droms, +4 per level
- 👑 Bosses: 1 on levels 1–2, 2 on level 3+
- 🔑 Bosses spawn **only after** all regular droms are eliminated

---

## 🚀 Running the Game

**Requirements:** Python 3.10+ on Windows (uses Win32 console APIs)

```bash
python game.py
```

> Make sure your terminal window is large enough — the game adapts to terminal size automatically.

---

## 📁 Project Structure

| File | Role |
|------|------|
| `game.py` | Main loop, game state, input handling |
| `renderer.py` | Frame builder — raycasting, sprites, HUD, sky |
| `enemy.py` | Drom & Boss AI state machines |
| `map_data.py` | Map layout, waypoints, wall colours |
| `raycaster.py` | DDA ray casting & line-of-sight |
| `pickups.py` | Health packs, ammo crates, gun upgrade |
| `input.py` | Win32 keyboard polling |
| `console.py` | Terminal setup, ANSI output, Win32 handles |
| `assets.py` | Shared visual/asset constants |
| `text.py` | All player-facing strings |

---

## 🏆 Tips

- 💊 Health packs heal 30–50 HP — don't waste them when full
- 📦 Ammo crates fill mag first, then reserve (max 16 + 32)
- 🔫 Gun upgrade doubles your shots — grab it early
- 🧱 Shoot walls strategically — create new paths or cut off droms
- 👂 Droms can **hear** you nearby even without line of sight
- 🏃 Boss will **break through walls** to reach you — keep moving

---

*Built with ❤️ in pure Python — no dependencies, no engine, no mercy.*
