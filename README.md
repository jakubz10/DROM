```
       _______   _______    ______   __       __
      /       \ /       \  /      \ /  \     /  |
      $$$$$$$  |$$$$$$$  |/$$$$$$  |$$  \   /$$ |
      $$ |  $$ |$$ |__$$ |$$ |  $$ |$$$  \ /$$$ |
      $$ |  $$ |$$    $$< $$ |  $$ |$$$$  /$$$$ |
      $$ |  $$ |$$$$$$$  |$$ |  $$ |$$ $$ $$/$$ |
      $$ |__$$ |$$ |  $$ |$$ \__$$ |$$ |$$$/ $$ |
      $$    $$/ $$ |  $$ |$$    $$/ $$ | $/  $$ |
      $$$$$$$/  $$/   $$/  $$$$$$/  $$/      $$/
```

# DROM - Terminal FPS

A Doom-style first-person shooter rendered entirely as colored Unicode characters in the Windows console. No game engine, no display library, no image files — every pixel is a computed colored character written at 20 FPS.

---

**Requirements:** Windows 10/11, no third-party packages.

---

## How to Play - Full Tutorial

### Your First Game

```
  +=====================================================+
  |                                                     |
  |   1. Launch the game                                |
  |   2. Press SPACE on the main menu                   |
  |   3. Kill all Droms to clear the level              |
  |   4. Survive all 5 levels to win!                   |
  |                                                     |
  +=====================================================+
```

When you start, you're placed inside a castle map armed with a gun. Hostile creatures called **Droms** patrol the corridors. Your goal: eliminate every Drom on the level to advance.

### Movement

```
              .---.
              | W |          W = Move forward
          .---+---+---.      S = Move backward
          | A | S | D |      A = Strafe left
          '---+---+---'      D = Strafe right
              '---'

          .-------.-------.
          | < / Q | > / E |  Arrow keys or Q/E = Turn camera
          '-------'-------'

          .-------.-------.
          |  UP   | DOWN  |  UP/DOWN arrows = Instant 180 flip
          '-------'-------'
```

- **Movement speed**: 3.8 tiles/second
- **Strafe**: 85% of forward speed
- **Turning**: 2.5 radians/second
- **180 flip**: Instantly face the opposite direction (great for quick reaction)

### Combat

```
         ___
        /   \         SPACE = Shoot
        | + |  <---   Crosshair shows where you're aiming
        \___/

    .------------.
    | AMMO: |16| |  <-- Magazine max
    | RESV: |32| |  <-- Reserve ammo max
    '------------'

    [ R ] = Reload     (1.2 seconds)
```

**Shooting tips:**
- Each shot fires a ray in the direction you're facing
- Enemies within a small cone (~0.09 rad) of the ray center get hit
- Walls block shots — you can't shoot through them
- Reload BEFORE your magazine empties to stay safe

### Reading the HUD

```
  +-------------------------------------------------------------------+
  | N    NE    E    SE    S    SW    W    NW    N   | <-- Compass     |
  |              v     V                            | <-- Enemy blips |
  |                                                 |                 |
  |                                                 |                 |
  |               [3D GAME VIEW]                    |                 |
  |                                                 |                 |
  |                                                 |                 |
  |===================================================| <-- Separator |
  | HP [████████████░░░] 73%  | AMMO 12 | KILLS 3/8 | <-- Status      |
  |    [▄▄▄▄▄▄▄▄▄▄▄   ]      | RESV +16| LVL 1     |                  |
  |       !!! DROM IS CLOSE !!!   >>> RELOAD NOW <<< | <-- Warnings   |
  +-------------------------------------------------------------------+
```

### The Minimap

```
  .---------.
  | # # # # |    # = Wall (colored by type)
  | # . + # |    . = Floor
  | # $ O># |    O = You (green)
  | # . @ # |    > = Your facing direction
  | # # # # |    @ = Enemy
  '---------'    + = Health pack
                 $ = Ammo crate
```

Located in the top-left of the viewport. Shows the full map layout, enemy positions, and pickup locations at a glance.

---

## Enemies - The Droms

### Regular Drom

```
          *           
          |
      .-------.
      | #   # |      
      '-------'
         ||
    .-----------.
    |[   %%%%  ]|
    |[   ----  ]|
    |[   %%%%  ]|
    '-----------'
    <===========*====> 
       ||    ||
       ##    ##    
       ==    ==  
```

- **HP**: 3 hits to kill
- **Damage**: 22 HP/second when in melee range
- **Speed**: 1.2 tiles/sec (chasing)
- **Antenna**: Pulses bright red as damage accumulates — watch for it!

### Boss Drom

```
            *             
            |
        .---------.
        | ##   ## |          
        '---------'
           ||
      .--------------.
      |[    %%%%%   ]|      
      |[    -----   ]|          
      |[    %%%%%   ]|
      '--------------'
      <=====*=*=*====> 
         ||      ||
         ##      ##
         ==      ==
```

- **HP**: 16 hits to kill
- **Damage**: 44 HP/second (2x normal!)
- **Special ability**: Smashes through walls to reach you
- **Eyes**: Track your position — they're always watching

### Drom AI States

```
  PATROL ----[spots you]----> ALERT ----[0.25s]----> CHASE
    ^                                                  |
    |                          .------[close enough]---'
    |                          v
  SEARCH <--[lost you]---- STRAFE (attacking!)
```

| State | Behavior | Color |
|-------|----------|-------|
| Patrol | Walking between waypoints | Blue-white, blue accents |
| Alert | Spotted you, turning to face | Warming up... |
| Chase | Running toward you | Warm white, orange accents |
| Strafe | Circling + attacking | Red-tinted, red accents |
| Search | Lost sight, investigating | Returning to blue |

```
  Type 1: SANDSTONE         Type 2: DARK SLATE
  .-----------.             .-----------.
  | [==] [==] |             | .--. .--. |
  | [==] [==] |             | |##| |##| |     Riveted metal
  | [==] [==] |             | '--' '--' |     panels
  '-----------'             '-----------'
  Warm tan tiles            Deep blue-grey

  Type 3: MOSSY IRON        Type 4: TORCHLIT STONE
  .-----------.             .-----------.
  | /\/\/\/\  |             | /\ /\ /\ |
  | \/\/\/\/  |             | \/ \/ \/ |     Hexagonal
  | /\/\/\/\  |             | /\ /\ /\ |     honeycomb
  '-----------'             '-----------'
  Muted green               Amber-orange

## Technical Details

- **Pure Python** — standard library + Win32 ctypes only
- **Windows-only** — uses `kernel32` and `user32` APIs directly
- **Single-call rendering** — entire frame written in one `WriteConsoleW` call
- **24-bit RGB color** — full color via ANSI escape sequences
- **Adaptive scaling** — menus, moon, and HUD scale to any terminal size
- **Fisheye-corrected** — proper perspective projection via cosine correction
- **30 FPS target** — frame-time regulated game loop


```
  +-----------------------------------------------+
  |                                               |
  |       Good luck, and watch your ammo.         |
  |                                               |
  |              The Droms are waiting.           |
  |                                               |
  +-----------------------------------------------+
```
