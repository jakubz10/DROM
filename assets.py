WALL_CH  = "##%%++--  "
FLOOR_CH = ".,` "
LOGO_BIG = [
    r" _______   _______    ______   __       __ ",
    r"/       \ /       \  /      \ /  \     /  |",
    r"$$$$$$$  |$$$$$$$  |/$$$$$$  |$$  \   /$$ |",
    r"$$ |  $$ |$$ |__$$ |$$ |  $$ |$$$  \ /$$$ |",
    r"$$ |  $$ |$$    $$< $$ |  $$ |$$$$  /$$$$ |",
    r"$$ |  $$ |$$$$$$$  |$$ |  $$ |$$ $$ $$/$$ |",
    r"$$ |__$$ |$$ |  $$ |$$ \__$$ |$$ |$$$/ $$ |",
    r"$$    $$/ $$ |  $$ |$$    $$/ $$ | $/  $$ |",
    r"$$$$$$$/  $$/   $$/  $$$$$$/  $$/      $$/ ",
]
SPLASH_CTRL = [
    "+------------------------------------------------------+",
    "|     W               Movement system                  |",
    "|   A S D                                              |",
    "|  LEFT / RIGHT       Rotate camera (arrows)           |",
    "|  UP / DOWN          180 degree camera flip (arrows)  |",
    "|  Q / E              Rotate camera alternative        |",
    "|  SPACE              Shoot                            |",
    "|  ESC / BACKSPACE    Quit                             |",
    "+------------------------------------------------------+",
]

_GUN_ROWS = [
    # row  x   shape              edge_rgb            face_rgb
    (  0, '|=]',          (105, 107, 115),    (108, 110, 118)  ),  # r0
    (  0, '[==]',          (112, 114, 122),    (115, 117, 125)  ),  # r1
    (  1, '[===]',         (122, 124, 132),    (125, 127, 135)  ),  # r2
    (  2, '[====]',        (132, 134, 142),    (135, 137, 145)  ),  # r3
    (  3, '-=====-',       (142, 144, 152),    (145, 147, 155)  ),  # r4
    (  4, '[=====]',       (150, 152, 160),    (152, 154, 162)  ),  # r5
    (  5, '-=====-',       (158, 160, 168),    (160, 162, 170)  ),  # r6
    (  6, '[=====]',       (165, 167, 175),    (168, 170, 178)  ),  # r7
    (  7, '-======-',      (172, 174, 182),    (175, 177, 185)  ),  # r8
    (  8, '[======]',      (180, 182, 190),    (185, 187, 195)  ),  # r9
    ( 12, '[-------------]', (220, 222, 230), (220, 222, 230) ),  # r10  (15 chars)
    ( 12, '[#############]', (205, 207, 215), (215, 217, 225) ),  # r11  (15 chars)
    ( 13, '[============]',  (200, 200, 210),  (210, 210, 218) ),  # r12  (14 chars)
    ( 13, '[############]',  (185, 185, 195),  (195, 195, 205) ),  # r13  (14 chars)
    ( 13, '|            |',  (150, 150, 160),  (150, 150, 160) ),  # r14
    ( 14, '(--      --)',    (155, 155, 165),  (140, 140, 150) ),  # r15
    ( 17, '[####]',          (105,  72,  43),  (116,  78,  46) ),  # r16
    ( 17, '[####]',          ( 95,  65,  38),  (108,  72,  42) ),  # r17
    ( 17, '[####]',          ( 85,  58,  33),  ( 95,  63,  36) ),  # r18
    ( 17, '[####]',          ( 75,  52,  28),  ( 83,  56,  30) ),  # r19
    ( 17, '[####]',          ( 68,  46,  25),  ( 75,  50,  27) ),  # r20
    ( 18, '(##)',            ( 63,  43,  22),  ( 70,  47,  24) ),  # r21
]

TMPL_ROWS = 22
TMPL_COLS = 27

def _build_gun_template(rows_def):
    """Convert compact row definitions into renderer-ready (col, row, ch, r, g, b) tuples."""
    result = []
    for row_idx, (x, shape, edge_rgb, face_rgb) in enumerate(rows_def):
        pixels = [(i, ch) for i, ch in enumerate(shape) if ch != ' ']
        if not pixels:
            continue
        first_i = pixels[0][0]
        last_i  = pixels[-1][0]
        for i, ch in pixels:
            rgb = edge_rgb if (i == first_i or i == last_i) else face_rgb
            result.append((x + i, row_idx, ch, rgb[0], rgb[1], rgb[2]))
    return result

GUN_TEMPLATE = _build_gun_template(_GUN_ROWS)


GUN_TEMPLATE_UPGRADED = [
    (co, ro, ch,
     max(0,   int(r * 0.52)),
     max(0,   int(g * 0.52)),
     min(255, int(b * 0.68 + 28)))
    for co, ro, ch, r, g, b in GUN_TEMPLATE
]

#Color palettes
#HUD chrome
COL_HUD_BG     = ( 15,  15,  25)   # background fill behind HUD text
COL_HUD_DIV    = ( 80,  80, 110)   # divider bars between HUD sections
COL_HUD_LBL    = (160, 180, 220)   # label text  (HP, AMMO, KILLS …)
COL_HUD_SEP    = ( 80,  90, 140)   # separator line above HUD
COL_HUD_SEP_BG = ( 10,  10,  20)   # separator line background
#Compass blips (enemy marker colour by AI state)
COL_BLIP_STRAFE = (255, 220,   0)  # yellow  — attacking / danger
COL_BLIP_CHASE  = (255, 100,   0)  # orange  — chasing player
COL_BLIP_PATROL = (220,  30,  30)  # red     — patrolling
#Crosshair
COL_XHAIR_NORMAL = (220, 220, 220) # white-ish at rest
COL_XHAIR_SHOOT  = (255, 200,  60) # yellow flash when firing
COL_XHAIR_HIT    = (255,  30,  30) # red when the player takes a hit
#Muzzle flash / death explosion
COL_FLASH_CORE = (255, 255, 220)   # bright white-yellow centre
COL_FLASH_MID  = (255, 180,  20)   # orange mid ring
COL_FLASH_EDGE = (220,  80,  10)   # dark orange outer edge
#Minimap
MM_CHAR_WALL       = '#'
MM_CHAR_FLOOR      = '.'
MM_CHAR_PLAYER     = 'O'
MM_CHAR_PLAYER_DIR = '>'
MM_CHAR_HEALTH     = '+'
MM_CHAR_AMMO       = '$'
MM_CHAR_ENEMY      = '@'
COL_MM_PLAYER       = (  0, 255, 100)  # bright green
COL_MM_PLAYER_DIR   = (  0, 180,  70)  # dim green arrow
COL_MM_HEALTH       = (255,  60,  60)  # red cross
COL_MM_AMMO         = ( 80, 140,  60)  # olive green
COL_MM_ENEMY_STRAFE = (255, 255,   0)  # yellow — attacking
COL_MM_ENEMY_CHASE  = (255, 120,   0)  # orange — chasing
COL_MM_ENEMY_PATROL = (160,   0,   0)  # dark red — patrolling
#End / level transition screens
COL_END_WIN_TITLE  = (  0, 220,  90)   # "YOU WIN" title
COL_END_WIN_SUB    = (  0, 130,  55)   # subtitle on win
COL_END_LOSE_TITLE = (210,  25,  15)   # "YOU DIED" title
COL_END_LOSE_SUB   = (120,  15,   8)   # subtitle on death
COL_END_STAT       = (165,  90,  22)   # kill count stat line
COL_LEVEL_TITLE    = (255, 180,   0)   # "LEVEL CLEAR" title
COL_LEVEL_SUB      = (180, 100,   0)   # subtitle on level clear
