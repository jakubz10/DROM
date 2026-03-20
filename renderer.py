import math, time
from console import _fg, _bg, _goto, HOME
from map_data import WORLD_MAP, MAP_H, MAP_W, WALL_RGB
from raycaster import cast_ray, FOV, HALF_FOV, MAX_DIST, WALL_CH, FLOOR_CH
from text import TEXT

# ── Module-level constants (built once, reused every frame) ──────────────────

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

_SPLASH_CTRL = [
    "+------------------------------------------------------+",
    "|  W / S              Move Forward / Backward          |",
    "|  A / D              Strafe Left / Right              |",
    "|  Q / E              Turn Left / Right                |",
    "|  LEFT / RIGHT       Turn Left / Right (arrows)       |",
    "|  UP / DOWN          180 degree flip                  |",
    "|  SPACE              Shoot                            |",
    "|  ESC / BACKSPACE    Quit                             |",
    "+------------------------------------------------------+",
]

GUN_TEMPLATE = [
    # (col, row, char, r, g, b)   row 0=top, row 21=bottom
    # Muzzle tip (top)
    (0,0,'|',105,107,115),(1,0,'=',108,110,118),(2,0,']',105,107,115),
    (0,1,'[',112,114,122),(1,1,'=',115,117,125),(2,1,'=',115,117,125),(3,1,']',112,114,122),
    (1,2,'[',122,124,132),(2,2,'=',125,127,135),(3,2,'=',125,127,135),(4,2,'=',125,127,135),(5,2,']',122,124,132),
    (2,3,'[',132,134,142),(3,3,'=',135,137,145),(4,3,'=',135,137,145),(5,3,'=',135,137,145),(6,3,'=',135,137,145),(7,3,']',132,134,142),
    # Barrel
    (3,4,'-',142,144,152),(4,4,'=',145,147,155),(5,4,'=',145,147,155),(6,4,'=',145,147,155),(7,4,'=',145,147,155),(8,4,'=',145,147,155),(9,4,'-',142,144,152),
    (4,5,'[',150,152,160),(5,5,'=',152,154,162),(6,5,'=',152,154,162),(7,5,'=',152,154,162),(8,5,'=',152,154,162),(9,5,'=',152,154,162),(10,5,']',150,152,160),
    (5,6,'-',158,160,168),(6,6,'=',160,162,170),(7,6,'=',160,162,170),(8,6,'=',160,162,170),(9,6,'=',160,162,170),(10,6,'=',160,162,170),(11,6,'-',158,160,168),
    (6,7,'[',165,167,175),(7,7,'=',168,170,178),(8,7,'=',168,170,178),(9,7,'=',168,170,178),(10,7,'=',168,170,178),(11,7,'=',168,170,178),(12,7,']',165,167,175),
    # Barrel junction
    (7,8,'-',172,174,182),(8,8,'=',175,177,185),(9,8,'=',175,177,185),(10,8,'=',175,177,185),(11,8,'=',175,177,185),(12,8,'=',175,177,185),(13,8,'=',175,177,185),(14,8,'-',172,174,182),
    (8,9,'[',180,182,190),(9,9,'=',185,187,195),(10,9,'=',185,187,195),(11,9,'=',185,187,195),(12,9,'=',185,187,195),(13,9,'=',185,187,195),(14,9,'=',185,187,195),(15,9,']',180,182,190),
    # Slide top
    (12,10,'[',220,222,230),(13,10,'-',220,222,230),(14,10,'-',220,222,230),(15,10,'-',220,222,230),(16,10,'-',220,222,230),(17,10,'-',220,222,230),(18,10,'-',220,222,230),(19,10,'-',220,222,230),(20,10,'-',220,222,230),(21,10,'-',220,222,230),(22,10,'-',220,222,230),(23,10,'-',220,222,230),(24,10,'-',220,222,230),(25,10,'-',220,222,230),(26,10,']',220,222,230),
    (12,11,'[',205,207,215),(13,11,'#',215,217,225),(14,11,'#',215,217,225),(15,11,'#',215,217,225),(16,11,'#',215,217,225),(17,11,'#',215,217,225),(18,11,'#',215,217,225),(19,11,'#',215,217,225),(20,11,'#',215,217,225),(21,11,'#',215,217,225),(22,11,'#',215,217,225),(23,11,'#',215,217,225),(24,11,'#',215,217,225),(25,11,'#',215,217,225),(26,11,']',205,207,215),
    # Receiver
    (13,12,'[',200,200,210),(14,12,'=',210,210,218),(15,12,'=',210,210,218),(16,12,'=',210,210,218),(17,12,'=',210,210,218),(18,12,'=',210,210,218),(19,12,'=',210,210,218),(20,12,'=',210,210,218),(21,12,'=',210,210,218),(22,12,'=',210,210,218),(23,12,'=',210,210,218),(24,12,'=',210,210,218),(25,12,'=',210,210,218),(26,12,']',200,200,210),
    (13,13,'[',185,185,195),(14,13,'#',195,195,205),(15,13,'#',195,195,205),(16,13,'#',195,195,205),(17,13,'#',195,195,205),(18,13,'#',195,195,205),(19,13,'#',195,195,205),(20,13,'#',195,195,205),(21,13,'#',195,195,205),(22,13,'#',195,195,205),(23,13,'#',195,195,205),(24,13,'#',195,195,205),(25,13,'#',195,195,205),(26,13,']',185,185,195),
    # Trigger guard
    (13,14,'|',150,150,160),(26,14,'|',150,150,160),
    (14,15,'(',155,155,165),(15,15,'-',140,140,150),(16,15,'-',140,140,150),(23,15,'-',140,140,150),(24,15,'-',140,140,150),(25,15,')',155,155,165),
    # Grip
    (17,16,'[',105,72,43),(18,16,'#',116,78,46),(19,16,'#',116,78,46),(20,16,'#',116,78,46),(21,16,'#',116,78,46),(22,16,']',105,72,43),
    (17,17,'[',95,65,38),(18,17,'#',108,72,42),(19,17,'#',108,72,42),(20,17,'#',108,72,42),(21,17,'#',108,72,42),(22,17,']',95,65,38),
    (17,18,'[',85,58,33),(18,18,'#',95,63,36),(19,18,'#',95,63,36),(20,18,'#',95,63,36),(21,18,'#',95,63,36),(22,18,']',85,58,33),
    (17,19,'[',75,52,28),(18,19,'#',83,56,30),(19,19,'#',83,56,30),(20,19,'#',83,56,30),(21,19,'#',83,56,30),(22,19,']',75,52,28),
    (17,20,'[',68,46,25),(18,20,'#',75,50,27),(19,20,'#',75,50,27),(20,20,'#',75,50,27),(21,20,'#',75,50,27),(22,20,']',68,46,25),
    # Magazine
    (18,21,'(',63,43,22),(19,21,'#',70,47,24),(20,21,'#',70,47,24),(21,21,')',63,43,22),
]
TMPL_ROWS = 22
TMPL_COLS = 27

_tmpl_map = {(co, ro): (ch, r, g, b) for co, ro, ch, r, g, b in GUN_TEMPLATE}

# ── Functions ────────────────────────────────────────────────────────────────

def _build_compass(cols, angle, enemies, px, py):
    """
    Fortnite-style compass bar occupying 2 rows (rows 0-1).
    Row 0: direction labels (N/NE/E/SE/S/SW/W/NW) scrolling with camera angle.
    Row 1: enemy blips - a bright red/yellow triangle marker above each enemy's
           compass position, with distance-based intensity.
    The compass spans 360 degrees mapped to `cols` characters.
    """
    TWO_PI = 2 * math.pi

    # Row 0: scrolling direction strip
    # Cardinal/intercardinal labels placed every 45 deg (= cols/8 chars apart)
    DIRS = ['N','NE','E','SE','S','SW','W','NW']   # every 45 deg, East=0 rad

    # angle=0 means facing East. We want N at top when facing North (angle=-pi/2).
    # Map each column to a world angle.

    # Build the strip as a list of (char, r, g, b)
    strip0 = [(' ', 20, 20, 20)] * cols   # background

    # Place direction labels
    for di, label in enumerate(DIRS):
        dir_angle = di * math.pi / 4   # 0=E,pi/4=NE,pi/2=N ...
        # angular offset from player view center
        diff = (dir_angle - angle + math.pi) % TWO_PI - math.pi
        col  = int(cols/2 + diff / TWO_PI * cols)
        if 0 <= col < cols:
            is_cardinal = (di % 2 == 0)   # N/E/S/W
            lc = (255,255,255) if is_cardinal else (140,140,140)
            for ci2, lch in enumerate(label):
                c2 = col + ci2 - len(label)//2
                if 0 <= c2 < cols:
                    strip0[c2] = (lch, lc[0], lc[1], lc[2])

    # Row 1: enemy blip strip
    strip1 = [(' ', 10, 10, 10)] * cols

    behind_enemies = []   # collect enemies behind player for warning arrows

    for e in enemies:
        if not e.alive: continue
        dx = e.x - px; dy = e.y - py
        dist = math.hypot(dx, dy)
        if dist < 0.1: continue

        enemy_angle = math.atan2(dy, dx)
        diff = (enemy_angle - angle + math.pi) % TWO_PI - math.pi
        # diff is now in [-pi, pi]: negative=left, positive=right

        # Brightness fades with distance, minimum 0.4 so far enemies still show
        brightness = max(0.4, 1.0 - dist / 18.0)

        # Colour by state
        if e.state in ('strafe', 'alert'):
            base_col = (255, 220, 0)    # yellow = danger
        elif e.state == 'chase':
            base_col = (255, 100, 0)    # orange = chasing
        else:
            base_col = (220, 30, 30)    # red = patrolling

        r2 = int(base_col[0] * brightness)
        g2 = int(base_col[1] * brightness)
        b2 = int(base_col[2] * brightness)

        # Map angular diff to a column.
        # Enemies within +-180 deg all fit: clamp to edges if beyond +-170 deg
        if abs(diff) <= math.pi * 0.94:
            col = int(cols/2 + diff / TWO_PI * cols)
            col = max(1, min(cols-2, col))
            # 5-wide blip: edges dim, centre bright, so it's easy to spot
            for offset, intensity in ((-2,0.3),(-1,0.6),(0,1.0),(1,0.6),(2,0.3)):
                c2 = col + offset
                if 0 <= c2 < cols:
                    strip1[c2] = (
                        'V' if offset == 0 else ('|' if abs(offset)==1 else '.'),
                        min(255, int(r2 * intensity)),
                        min(255, int(g2 * intensity)),
                        min(255, int(b2 * intensity)),
                    )
        else:
            # Enemy is behind player - pin to the nearest edge with an arrow
            behind_enemies.append((diff, r2, g2, b2))

    # Pin behind-enemies to left/right edges
    for diff, r2, g2, b2 in behind_enemies:
        # diff > 0 means slightly right-of-behind -> pin right edge
        # diff < 0 means slightly left-of-behind  -> pin left edge
        if diff > 0:
            for c2 in range(cols-5, cols):
                strip1[c2] = ('>' , r2, g2, b2)
        else:
            for c2 in range(0, 5):
                strip1[c2] = ('<', r2, g2, b2)

    # Distance labels on direction strip for each visible enemy
    for e in enemies:
        if not e.alive: continue
        dx = e.x - px; dy = e.y - py
        dist = math.hypot(dx, dy)
        if dist < 0.1: continue
        enemy_angle = math.atan2(dy, dx)
        diff = (enemy_angle - angle + math.pi) % TWO_PI - math.pi
        if abs(diff) > math.pi * 0.94: continue
        col = int(cols/2 + diff / TWO_PI * cols)
        col = max(2, min(cols-3, col))
        label = f"{int(dist)}"
        brightness = max(0.5, 1.0 - dist / 18.0)
        if e.state in ('strafe','alert'):
            lr,lg,lb = int(255*brightness), int(220*brightness), 0
        elif e.state == 'chase':
            lr,lg,lb = int(255*brightness), int(100*brightness), 0
        else:
            lr,lg,lb = int(200*brightness), int(30*brightness), int(30*brightness)
        for ci2, lch in enumerate(label):
            c2 = col - len(label)//2 + ci2
            if 0 <= c2 < cols:
                strip0[c2] = (lch, lr, lg, lb)
    mid = cols // 2
    strip0[mid] = ('|', 0, 200, 255)   # cyan center tick
    # Small FOV bracket markers
    fov_half_cols = int(HALF_FOV / TWO_PI * cols)
    for c2 in (mid - fov_half_cols, mid + fov_half_cols):
        if 0 <= c2 < cols:
            strip0[c2] = ('[' if c2 < mid else ']', 0, 120, 180)

    # Assemble into ANSI strings
    lines = []
    for row_idx, strip in enumerate((strip0, strip1)):
        out = [_goto(0, row_idx)]
        lf = lb = None
        for ch, r2, g2, b2 in strip:
            f = (r2, g2, b2); bg = (0, 0, 0)
            if f != lf: out.append(_fg(*f)); lf = f
            if bg != lb: out.append(_bg(*bg)); lb = bg
            out.append(ch)
        lines.append(''.join(out))
    return ''.join(lines)


def build_frame(cols, rows, px, py, angle, enemies,
                hp, kills, sflash, dalpha, msg, msg_t, fps,
                close_warn=0.0, level=1, total_enemies=8,
                health_packs=None, ammo_crates=None,
                ammo=16, reserve=32, reload_anim=0.0,
                ammo_warn='', hit_flash=0):

    # Compass takes rows 0-1; view starts at row 2
    COMPASS_ROWS = 2
    vr   = rows - 4 - COMPASS_ROWS   # view rows (4 HUD rows now)
    voff = COMPASS_ROWS              # vertical offset for 3-D view
    half = vr // 2
    _t   = time.time()               # cached once - used for all animations this frame
    out  = [HOME]

    # Compass bar (rows 0-1)
    out.append(_build_compass(cols, angle, enemies, px, py))

    # Precompute walls
    z_buf      = [99.0]*cols
    wall_cell  = [None]*cols
    _col_scale = FOV / cols
    _ray_base  = angle - HALF_FOV
    # Precompute sky_x per column (used in star rendering)
    _TWO_PI   = 2*math.pi
    sky_x_col = [int((_ray_base + c * _col_scale) % _TWO_PI / _TWO_PI * 3000) for c in range(cols)]

    curr_ra = _ray_base
    for col in range(cols):
        d, side, wt = cast_ray(px, py, curr_ra)
        curr_ra += _col_scale
        z_buf[col] = d
        if not wt: continue
        is_outer = (wt == 5)
        # Outer walls appear 2.2x taller than inner walls
        wh_raw = min(vr*2, int(vr/d))
        wh     = min(vr*2, int(wh_raw * 2.2)) if is_outer else wh_raw
        top = max(0, half-wh//2)
        bot = min(vr, half+wh//2)
        t   = max(0.0, 1.0-d/MAX_DIST)*(0.55 if side else 1.0)
        base= WALL_RGB.get(wt,(180,50,50))
        fr_w= int(base[0]*t); fg_w=int(base[1]*t); fb_w=int(base[2]*t)

        # Per-type texture character sets (no gradient - fixed pattern chars)
        # Type 5 outer: classic brick  |  1: cross/hash  |  2: vertical stripe
        # 3: horizontal stripe  |  4: diamond dot
        brick_str  = 0.38 if is_outer else 0.22
        brick_h    = max(3, wh // 6)
        brick_w    = max(4, cols // 18)
        batt_h     = max(1, brick_h // 2)

        ci = int(min(1.0, d/MAX_DIST)*(len(WALL_CH)-1))
        base_ch = WALL_CH[ci]

        wall_cell[col] = (base_ch, fr_w,fg_w,fb_w, fr_w//3,fg_w//3,fb_w//3, top,bot,
                          brick_h, brick_w, wh, brick_str, batt_h, is_outer, wt)

    # Precompute sprites
    spr = [[None]*cols for _ in range(vr)]
    alive = sorted((e for e in enemies if e.alive),
                   key=lambda e:(e.x-px)**2+(e.y-py)**2, reverse=True)
    for e in alive:
        dx,dy = e.x-px, e.y-py
        d = math.hypot(dx,dy)
        if d<0.2: continue
        ea = math.atan2(dy,dx)-angle
        ea = (ea+math.pi)%(2*math.pi)-math.pi
        if abs(ea)>HALF_FOV+0.25: continue
        sx2  = int((0.5+ea/FOV)*cols)
        sh   = min(vr*2, int(vr/max(0.1,d)))
        sw   = max(1, sh)          # full width = height (was 3//4, now 1:1 ratio)
        ts   = max(0, half-sh//2); bs=min(vr, half+sh//2)
        x0   = sx2-sw//2
        shd  = max(0.0, 1.0-d/10.0)

        # First pass: build a local filled mask so we can detect edges
        # mask[dy][dx] = True if that texel is a robot part (not transparent)
        mask_h = bs - ts
        mask_w = sw
        mask = [[False]*mask_w for _ in range(mask_h)]

        for dsx in range(sw):
            tx = dsx/max(1,sw-1)
            for dsy in range(mask_h):
                ty = dsy/max(1,mask_h-1)
                bx = tx-0.5
                if (0.12<tx<0.88 and 0.08<ty<0.30): mask[dsy][dsx]=True  # head
                elif (0.38<tx<0.62 and 0.30<ty<0.36): mask[dsy][dsx]=True  # neck
                elif (0.10<tx<0.90 and 0.36<ty<0.78): mask[dsy][dsx]=True  # body
                elif (0.00<tx<0.12 and 0.40<ty<0.68): mask[dsy][dsx]=True  # arm_l
                elif (0.88<tx<1.00 and 0.40<ty<0.68): mask[dsy][dsx]=True  # arm_r
                elif (0.18<tx<0.42 and 0.78<ty<1.00): mask[dsy][dsx]=True  # leg_l
                elif (0.58<tx<0.82 and 0.78<ty<1.00): mask[dsy][dsx]=True  # leg_r
                elif (0.44<tx<0.56 and ty<0.08): mask[dsy][dsx]=True        # antenna

        for dsx in range(sw):
            sc = x0+dsx
            if not (0<=sc<cols): continue
            if z_buf[sc]<d: continue
            tx = dsx/max(1,sw-1)
            for dsy in range(bs-ts):
                ty=dsy/max(1,bs-ts-1); row=ts+dsy
                if not (0<=row<vr): continue

                # Robot sprite layout (tx/ty both 0..1)
                # Antenna:  thin spike above head
                # Head:     wide flat box  ty 0.08-0.30
                # Visor:    glowing strip  ty 0.13-0.22, tx 0.20-0.80
                # Neck:     narrow column  ty 0.30-0.36
                # Body:     wide torso     ty 0.36-0.78
                # Panel:    H-lines on body
                # Arms:     side stubs     ty 0.40-0.68, tx<0.12 or tx>0.88
                # Legs:     two columns    ty 0.78-1.00

                ch=None; rc=gc=bc=0; rbg=gbg=bbg=0

                # Background behind robot - pure black for contrast
                # (we only emit pixels where robot has a part)

                is_antenna  = (0.44<tx<0.56 and ty<0.08)
                is_antenna_tip = (0.47<tx<0.53 and ty<0.03)
                head_box    = (0.12<tx<0.88 and 0.08<ty<0.30)
                visor       = (0.20<tx<0.80 and 0.13<ty<0.23)
                visor_eye_l = (0.26<tx<0.38 and 0.14<ty<0.22)
                visor_eye_r = (0.62<tx<0.74 and 0.14<ty<0.22)
                neck        = (0.38<tx<0.62 and 0.30<ty<0.36)
                body        = (0.10<tx<0.90 and 0.36<ty<0.78)
                arm_l       = (0.00<tx<0.12 and 0.40<ty<0.68)
                arm_r       = (0.88<tx<1.00 and 0.40<ty<0.68)
                panel_h1    = (0.10<tx<0.90 and 0.48<ty<0.50)  # chest seam
                panel_h2    = (0.10<tx<0.90 and 0.63<ty<0.65)  # belly seam
                panel_v     = (0.48<tx<0.52 and 0.36<ty<0.78)  # center spine
                leg_l       = (0.18<tx<0.42 and 0.78<ty<1.00)
                leg_r       = (0.58<tx<0.82 and 0.78<ty<1.00)
                leg_joint_l = (0.18<tx<0.42 and 0.78<ty<0.83)
                leg_joint_r = (0.58<tx<0.82 and 0.78<ty<0.83)

                # brightness scales with closeness
                br_base = max(0.55, shd)

                # Colour palette
                # Base: near-white metal  (slightly warm)
                # Accent: red highlights when aggressive, blue when patrol
                # Pain: full saturated white flash

                if e.pain_t > 0:
                    # Pure white flash on hit
                    metal_r,metal_g,metal_b   = 255,255,255
                    accent_r,accent_g,accent_b = 255,255,255
                    vg_r,vg_g,vg_b             = 255,255,255
                elif e.state == 'strafe':
                    # Attacking - white body, red accents, red visor
                    metal_r  = min(255,int(240*br_base+15))
                    metal_g  = min(255,int(220*br_base+10))
                    metal_b  = min(255,int(220*br_base+10))
                    accent_r,accent_g,accent_b = min(255,int(255*br_base)),int(40*br_base),int(40*br_base)
                    vg_r,vg_g,vg_b             = min(255,int(255*br_base)),int(30*br_base),int(30*br_base)
                elif e.state in ('chase','alert'):
                    # Chasing - white body, orange-red accents, orange visor
                    metal_r  = min(255,int(245*br_base+10))
                    metal_g  = min(255,int(235*br_base+10))
                    metal_b  = min(255,int(230*br_base+10))
                    accent_r,accent_g,accent_b = min(255,int(255*br_base)),int(100*br_base),int(20*br_base)
                    vg_r,vg_g,vg_b             = min(255,int(255*br_base)),int(120*br_base),int(20*br_base)
                else:
                    # Patrolling - white body, blue accents, cyan visor
                    metal_r  = min(255,int(230*br_base+20))
                    metal_g  = min(255,int(235*br_base+20))
                    metal_b  = min(255,int(245*br_base+20))
                    accent_r,accent_g,accent_b = int(80*br_base),int(120*br_base),min(255,int(255*br_base))
                    vg_r,vg_g,vg_b             = int(60*br_base),min(255,int(230*br_base)),min(255,int(255*br_base))

                # Dark background panels - near-black so white pops
                dark_r = max(8, metal_r//10)
                dark_g = max(8, metal_g//10)
                dark_b = max(8, metal_b//10)

                if is_antenna_tip:
                    ch='*'; rc,gc,bc=vg_r,vg_g,vg_b; rbg,gbg,bbg=0,0,0
                elif is_antenna:
                    ch='|'; rc,gc,bc=metal_r,metal_g,metal_b; rbg,gbg,bbg=0,0,0
                elif visor_eye_l or visor_eye_r:
                    ch='#'; rc,gc,bc=vg_r,vg_g,vg_b; rbg,gbg,bbg=dark_r,dark_g,dark_b
                elif visor:
                    ch='-'; rc,gc,bc=vg_r//2,vg_g//2,vg_b//2; rbg,gbg,bbg=dark_r,dark_g,dark_b
                elif head_box:
                    ch='#'; rc,gc,bc=metal_r,metal_g,metal_b; rbg,gbg,bbg=dark_r,dark_g,dark_b
                elif neck:
                    ch='|'; rc,gc,bc=metal_r//2,metal_g//2,metal_b//2; rbg,gbg,bbg=0,0,0
                elif panel_h1 or panel_h2:
                    ch='-'; rc,gc,bc=accent_r,accent_g,accent_b; rbg,gbg,bbg=dark_r,dark_g,dark_b
                elif panel_v:
                    ch='|'; rc,gc,bc=accent_r,accent_g,accent_b; rbg,gbg,bbg=dark_r,dark_g,dark_b
                elif arm_l or arm_r:
                    ch='[' if arm_l else ']'
                    rc,gc,bc=metal_r,metal_g,metal_b; rbg,gbg,bbg=dark_r,dark_g,dark_b
                elif leg_joint_l or leg_joint_r:
                    ch='='; rc,gc,bc=accent_r,accent_g,accent_b; rbg,gbg,bbg=0,0,0
                elif leg_l or leg_r:
                    ch='#'; rc,gc,bc=metal_r,metal_g,metal_b; rbg,gbg,bbg=dark_r,dark_g,dark_b
                elif body:
                    ch='%'; rc,gc,bc=metal_r,metal_g,metal_b; rbg,gbg,bbg=dark_r,dark_g,dark_b

                if ch is not None:
                    spr[row][sc]=(ch, rc,gc,bc, rbg,gbg,bbg)
                else:
                    # Outline pass: if this texel is empty but a neighbour is filled,
                    # draw a contrasting outline. Sample the background behind this
                    # column to pick a colour that pops against it.
                    is_filled = mask[dsy][dsx]
                    if not is_filled:
                        # Check 4-connected neighbours in mask
                        nb = False
                        if dsx>0        and mask[dsy][dsx-1]: nb=True
                        if dsx<mask_w-1 and mask[dsy][dsx+1]: nb=True
                        if dsy>0        and mask[dsy-1][dsx]:  nb=True
                        if dsy<mask_h-1 and mask[dsy+1][dsx]:  nb=True
                        if nb:
                            # Sample what's behind this screen column
                            wc = wall_cell[sc]
                            if wc and wc[7]<=row<wc[8]:
                                bg_lum = wc[1]+wc[2]+wc[3]  # fg brightness of wall
                            elif row < half:
                                bg_lum = 0  # sky is dark
                            else:
                                bg_lum = 30  # floor is near-dark
                            # If background is dark -> white outline
                            # If background is bright -> black outline
                            if bg_lum < 150:
                                spr[row][sc]=('#', 255,255,255, 0,0,0)
                            else:
                                spr[row][sc]=('#', 0,0,0, 255,255,255)

    # Health pack sprites
    if health_packs:
        for hp_pack in health_packs:
            if not hp_pack.active: continue
            dx,dy = hp_pack.x-px, hp_pack.y-py
            d = math.hypot(dx,dy)
            if d<0.2: continue
            ea = math.atan2(dy,dx)-angle
            ea = (ea+math.pi)%(2*math.pi)-math.pi
            if abs(ea)>HALF_FOV+0.3: continue
            sx2  = int((0.5+ea/FOV)*cols)
            # Box is 1/3 of enemy height at same distance
            full_sh = min(vr*2, int(vr/max(0.1,d)))
            sh  = max(1, full_sh//3)
            sw  = sh
            ts2 = max(0, half - sh//2); bs2 = min(vr, half + sh//2)
            x02 = sx2 - sw//2
            shd2 = max(0.4, 1.0-d/14.0)
            # Warm off-white panel / recessed seam / red cross (all distance-shaded)
            pw=int(242*shd2); pg=int(240*shd2); pb=int(235*shd2)   # matte white panel
            iw=int(206*shd2); ig=int(203*shd2); ib=int(198*shd2)   # recessed seam edge
            cr2=int(225*shd2)                                        # red cross
            for dsx in range(sw):
                sc = x02+dsx
                if not (0<=sc<cols): continue
                if z_buf[sc]<d: continue
                tx2 = dsx/max(1,sw-1)
                for dsy in range(bs2-ts2):
                    ty2=dsy/max(1,bs2-ts2-1); row=ts2+dsy
                    if not (0<=row<vr): continue
                    # ── Weathered tactical crate ──────────────────────────
                    # L-shaped corner brackets (arm along each edge from corner)
                    csz=0.22; arm=0.10
                    in_brk=(
                        (tx2<csz and ty2<arm) or (tx2<arm and ty2<csz) or
                        (tx2>1-csz and ty2<arm) or (tx2>1-arm and ty2<csz) or
                        (tx2<csz and ty2>1-arm) or (tx2<arm and ty2>1-csz) or
                        (tx2>1-csz and ty2>1-arm) or (tx2>1-arm and ty2>1-csz)
                    )
                    # Rounded rivets on bracket arms (2 per arm = 8 total)
                    rv=0.05
                    is_rivet=(
                        (abs(tx2-0.15)<rv and abs(ty2-0.05)<rv) or
                        (abs(tx2-0.05)<rv and abs(ty2-0.15)<rv) or
                        (abs(tx2-0.85)<rv and abs(ty2-0.05)<rv) or
                        (abs(tx2-0.95)<rv and abs(ty2-0.15)<rv) or
                        (abs(tx2-0.15)<rv and abs(ty2-0.95)<rv) or
                        (abs(tx2-0.05)<rv and abs(ty2-0.85)<rv) or
                        (abs(tx2-0.85)<rv and abs(ty2-0.95)<rv) or
                        (abs(tx2-0.95)<rv and abs(ty2-0.85)<rv)
                    )
                    ws=(int(tx2*19)*29+int(ty2*19)*53)&0xFF  # deterministic wear seed
                    cross_h=(0.25<ty2<0.75); cross_v=(0.25<tx2<0.75)
                    is_frame=(tx2<0.12 or tx2>0.88 or ty2<0.12 or ty2>0.88) and not in_brk
                    is_seam =(tx2<0.18 or tx2>0.82 or ty2<0.18 or ty2>0.82) and not in_brk and not is_frame
                    if in_brk:
                        # Aged brass / rusted steel with green patina
                        if is_rivet:
                            spr[row][sc]=('o', int(20*shd2),int(16*shd2),int(13*shd2), int(38*shd2),int(28*shd2),int(12*shd2))
                        elif ws<30:   # dark oxidation
                            spr[row][sc]=('#', int(42*shd2),int(32*shd2),int(9*shd2),  int(28*shd2),int(18*shd2),int(5*shd2))
                        elif ws<60:   # greenish patina
                            spr[row][sc]=('%', int(52*shd2),int(72*shd2),int(26*shd2), int(28*shd2),int(38*shd2),int(12*shd2))
                        else:         # base aged brass
                            spr[row][sc]=('#', int(82*shd2),int(58*shd2),int(16*shd2), int(42*shd2),int(28*shd2),int(8*shd2))
                    elif cross_h or cross_v:
                        # Bold red cross — slight wear variation
                        spr[row][sc]=('+', cr2 if ws>=15 else int(195*shd2), int(10*shd2),int(8*shd2), pw,pg,pb)
                    elif is_frame:
                        # Outer white frame (slightly raised appearance)
                        spr[row][sc]=(' ', 0,0,0, pw,pg,pb)
                    elif is_seam:
                        # Recessed inner seam — slightly darker
                        spr[row][sc]=(' ', 0,0,0, iw,ig,ib)
                    elif ws<20:
                        # Surface scratches and scuff marks
                        spr[row][sc]=("'-`."[ws%4], int(165*shd2),int(160*shd2),int(153*shd2), pw,pg,pb)
                    else:
                        # Clean matte white panel
                        spr[row][sc]=(' ', pw,pg,pb, pw,pg,pb)

    # Ammo crate sprites - military green body with gray outline + bullet symbol
    for ac in (ammo_crates or []):
        if not ac.active: continue
        dx,dy = ac.x-px, ac.y-py
        d = math.hypot(dx,dy)
        if d<0.2: continue
        ea = math.atan2(dy,dx)-angle
        ea = (ea+math.pi)%(2*math.pi)-math.pi
        if abs(ea)>HALF_FOV+0.3: continue
        sx2  = int((0.5+ea/FOV)*cols)
        full_sh = min(vr*2, int(vr/max(0.1,d)))
        sh  = max(1, full_sh//3)
        sw  = sh
        ts2 = max(0, half - sh//2); bs2 = min(vr, half + sh//2)
        x02 = sx2 - sw//2
        shd2 = max(0.4, 1.0-d/14.0)
        # Military green body colour
        mg_r = int(50*shd2);  mg_g = int(90*shd2);  mg_b = int(40*shd2)
        # Gray outline colour
        go_r = int(160*shd2); go_g = int(160*shd2); go_b = int(160*shd2)
        # Bullet symbol colour (lighter green-yellow for contrast)
        bl_r = int(180*shd2); bl_g = int(220*shd2); bl_b = int(80*shd2)
        for dsx in range(sw):
            sc = x02+dsx
            if not (0<=sc<cols): continue
            if z_buf[sc]<d: continue
            tx2 = dsx/max(1,sw-1)
            for dsy in range(bs2-ts2):
                ty2=dsy/max(1,bs2-ts2-1); row=ts2+dsy
                if not (0<=row<vr): continue
                border   = (tx2<0.1 or tx2>0.9 or ty2<0.1 or ty2>0.9)
                bullet_v = (0.42<tx2<0.58)
                bullet_h = (0.3<ty2<0.45 or 0.55<ty2<0.7)
                if bullet_v or bullet_h:
                    spr[row][sc]=('|' if bullet_v else '-', bl_r,bl_g,bl_b, mg_r//2,mg_g//2,mg_b//2)
                elif border:
                    spr[row][sc]=('#', go_r,go_g,go_b, 0,0,0)
                else:
                    spr[row][sc]=('%', mg_r,mg_g,mg_b, mg_r//3,mg_g//3,mg_b//3)
    lf=lb=None
    for row in range(vr):
        out.append(_goto(0, row+voff))
        for col in range(cols):
            sp=spr[row][col]
            wc=wall_cell[col]
            if sp:
                ch,fr,fg2,fb,br,bg2,bb=sp
            elif wc and wc[7]<=row<wc[8]:
                base_ch,fr_w,fg_w,fb_w,_br_w,_bg_w,_bb_w,top_w,bot_w,brick_h,brick_w,wh_v,brick_str,batt_h,is_outer,wt_cell = wc
                rel = row - top_w
                wall_h_total = max(1, bot_w - top_w)

                # Battlements on outer wall top edge
                in_batt_zone = is_outer and rel < batt_h
                batt_col = (col // brick_w) % 2 == 0
                if in_batt_zone and batt_col:
                    t2 = row / max(1, half - 1)
                    ch = ' '; fr,fg2,fb = 0,0,0
                    br,bg2,bb = int(2+8*t2), int(5+18*t2), int(15+35*t2)

                # Outer wall: staggered brick pattern
                elif is_outer:
                    mortar_h = (rel % max(1,brick_h) == 0)
                    brick_row_idx = rel // max(1,brick_h)
                    offset = (brick_row_idx % 2) * (brick_w // 2)
                    mortar_v = ((col + offset) % max(1,brick_w) == 0)
                    if mortar_h or mortar_v:
                        fr  = max(0, fr_w - int(fr_w * brick_str))
                        fg2 = max(0, fg_w - int(fg_w * brick_str))
                        fb  = max(0, fb_w - int(fb_w * brick_str))
                        ch  = '·'; br = fr//3; bg2 = fg2//3; bb = fb//3
                    else:
                        ch,fr,fg2,fb,br,bg2,bb = base_ch,fr_w,fg_w,fb_w,_br_w,_bg_w,_bb_w

                # Type 1 (red inner): raised square panel tiles
                elif wt_cell == 1:
                    tile_h = max(4, brick_h)
                    tile_w = max(6, brick_w)
                    tr = rel % tile_h
                    tc = col % tile_w
                    is_border = (tr == 0 or tr == tile_h-1 or tc == 0 or tc == tile_w-1)
                    is_inner  = (tr == 1 or tr == tile_h-2 or tc == 1 or tc == tile_w-2)
                    if is_border:
                        fr  = max(0, fr_w - int(fr_w * 0.45)); fg2 = max(0, fg_w - int(fg_w * 0.45)); fb = max(0, fb_w - int(fb_w * 0.45))
                        ch  = '#'; br = fr//4; bg2 = fg2//4; bb = fb//4
                    elif is_inner:
                        fr  = min(255, fr_w + int(fr_w * 0.15)); fg2 = min(255, fg_w + int(fg_w * 0.10)); fb = min(255, fb_w + int(fb_w * 0.10))
                        ch  = '%'; br = fr//3; bg2 = fg2//3; bb = fb//3
                    else:
                        ch,fr,fg2,fb,br,bg2,bb = base_ch,fr_w,fg_w,fb_w,_br_w,_bg_w,_bb_w

                # Type 2 (blue): metal panels with rivets
                elif wt_cell == 2:
                    panel_w = max(5, brick_w)
                    panel_h = max(4, brick_h)
                    tc = col % panel_w
                    tr = rel % panel_h
                    is_rivet  = (tc == 0 and tr == 0)
                    is_seam_v = (tc == 0)
                    is_seam_h = (tr == 0)
                    if is_rivet:
                        fr = min(255,fr_w+40); fg2 = min(255,fg_w+40); fb = min(255,fb_w+40)
                        ch = 'o'; br = fr//4; bg2 = fg2//4; bb = fb//4
                    elif is_seam_v or is_seam_h:
                        fr = max(0,fr_w-int(fr_w*0.35)); fg2 = max(0,fg_w-int(fg_w*0.35)); fb = max(0,fb_w-int(fb_w*0.35))
                        ch = '|' if is_seam_v else '-'; br = fr//4; bg2 = fg2//4; bb = fb//4
                    else:
                        even = ((col // panel_w) + (rel // panel_h)) % 2 == 0
                        boost = 12 if even else -8
                        fr = max(0,min(255,fr_w+boost)); fg2 = max(0,min(255,fg_w+boost)); fb = max(0,min(255,fb_w+boost))
                        ch = base_ch; br = fr//3; bg2 = fg2//3; bb = fb//3

                # Type 3 (green): herringbone zigzag tiles
                elif wt_cell == 3:
                    sz = max(3, brick_h // 2)
                    diag1 = (col + rel) % (sz * 2)
                    diag2 = (col - rel) % (sz * 2)
                    on_cross  = (diag1 < 1 and diag2 < 1)
                    on_stripe = (diag1 < 1 or diag2 < 1)
                    if on_cross:
                        fr = min(255,fr_w+30); fg2 = min(255,fg_w+30); fb = min(255,fb_w+20)
                        ch = '+'; br = fr//3; bg2 = fg2//3; bb = fb//3
                    elif on_stripe:
                        fr = max(0,fr_w-int(fr_w*0.30)); fg2 = max(0,fg_w-int(fg_w*0.25)); fb = max(0,fb_w-int(fb_w*0.25))
                        ch = '/'; br = fr//4; bg2 = fg2//4; bb = fb//4
                    else:
                        ch,fr,fg2,fb,br,bg2,bb = base_ch,fr_w,fg_w,fb_w,_br_w,_bg_w,_bb_w

                # Type 4 (gold): honeycomb hex tiles
                elif wt_cell == 4:
                    hex_w = max(4, brick_w // 2)
                    hex_h = max(3, brick_h // 2)
                    row_band = rel // hex_h
                    col_off  = (hex_w // 2) if (row_band % 2) else 0
                    tc = (col + col_off) % hex_w
                    tr = rel % hex_h
                    is_h_edge = (tr == 0)
                    is_v_edge = (tc == 0)
                    is_corner = is_h_edge and is_v_edge
                    if is_corner:
                        fr = min(255,fr_w+45); fg2 = min(255,fg_w+35); fb = max(0,fb_w-10)
                        ch = '*'; br = fr//3; bg2 = fg2//3; bb = fb//3
                    elif is_h_edge or is_v_edge:
                        fr = max(0,fr_w-int(fr_w*0.28)); fg2 = max(0,fg_w-int(fg_w*0.28)); fb = max(0,fb_w-int(fb_w*0.28))
                        ch = '-' if is_h_edge else '|'; br = fr//3; bg2 = fg2//3; bb = fb//3
                    else:
                        cell_id = (col + col_off) // hex_w + row_band * 7
                        boost   = 18 if (cell_id % 3 == 0) else (-10 if (cell_id % 3 == 1) else 0)
                        fr = max(0,min(255,fr_w+boost)); fg2 = max(0,min(255,fg_w+int(boost*0.8))); fb = max(0,min(255,fb_w+int(boost*0.4)))
                        ch = base_ch; br = fr//3; bg2 = fg2//3; bb = fb//3

                else:
                    ch,fr,fg2,fb,br,bg2,bb = base_ch,fr_w,fg_w,fb_w,_br_w,_bg_w,_bb_w
            else:
                if row < half:
                    # Realistic world-anchored sky
                    t2    = row / max(1, half - 1)
                    br2   = int(2  + 8*t2)
                    bg2_v = int(5  + 18*t2)
                    bb2   = int(15 + 35*t2)

                    sky_x = sky_x_col[col]
                    sky_y = row

                    seed = (sky_x * 3749 + sky_y * 6113) & 0xFFFF

                    is_star = seed < 80 and t2 < 0.80
                    if is_star:
                        bri = 150 + (seed * 17) % 105
                        twinkle = int(math.sin(_t*1.5 + sky_x*0.1 + sky_y*0.2)*20)
                        bri = max(100, min(255, bri + twinkle))
                        if seed < 10:   ch = '+'
                        elif seed < 25: ch = '*'
                        elif seed < 45: ch = '·'
                        else:           ch = '.'

                        # Slight color variations
                        if seed % 3 == 0:   fr, fg2, fb = bri, bri, min(255, bri + 40)
                        elif seed % 3 == 1: fr, fg2, fb = min(255, bri + 30), min(255, bri + 20), bri
                        else:               fr, fg2, fb = bri, bri, bri

                        br, bg2, bb = br2, bg2_v, bb2
                    else:
                        ch = ' '; fr,fg2,fb = 0,0,0
                        br,bg2,bb = br2, bg2_v, bb2
                    # Sky/wall seam: strong dark band at top of walls
                    sky_seam = half - 1 - row
                    if sky_seam == 0:
                        br  = int(br  * 0.25)
                        bg2 = int(bg2 * 0.25)
                        bb  = int(bb  * 0.25)
                    elif sky_seam == 1:
                        br  = int(br  * 0.55)
                        bg2 = int(bg2 * 0.55)
                        bb  = int(bb  * 0.55)
                else:
                    t2   = (row - half) / max(1, vr - half)
                    base_v = int(12 + 20*t2)
                    fr   = int(base_v * 0.90); fg2 = int(base_v * 0.82); fb = int(base_v * 0.70)
                    br   = max(0, fr - 4);   bg2 = max(0, fg2 - 3);  bb = max(0, fb - 3)
                    seed = (col * 1657 + row * 7331) & 0xFF
                    if   seed < 30:  ch = ','
                    elif seed < 60:  ch = '`'
                    elif seed < 90:  ch = '.'
                    else:            ch = ' '
                    # Floor/wall seam: strong dark band at base of walls
                    seam = row - half
                    if seam == 0:
                        fr  = int(fr  * 0.30)
                        fg2 = int(fg2 * 0.30)
                        fb  = int(fb  * 0.30)
                        br  = int(br  * 0.30)
                        bg2 = int(bg2 * 0.30)
                        bb  = int(bb  * 0.30)
                    elif seam == 1:
                        fr  = int(fr  * 0.55)
                        fg2 = int(fg2 * 0.55)
                        fb  = int(fb  * 0.55)
                        br  = int(br  * 0.55)
                        bg2 = int(bg2 * 0.55)
                        bb  = int(bb  * 0.55)
            if dalpha>0:
                vx=(col-cols//2)/(cols//2); vy=(row-half)/half
                vig=(vx*vx+vy*vy)**0.5
                if vig>0.55:
                    iv=int(min(1.0,(vig-0.55)/0.45)*dalpha*200)
                    fr=min(255,fr+iv); br=min(255,br+iv//3)
            f=(fr,fg2,fb); b=(br,bg2,bb)
            if f!=lf: out.append(_fg(*f)); lf=f
            if b!=lb: out.append(_bg(*b)); lb=b
            out.append(ch)

    # Gun in hand - scales to ~1/3 of the view height
    # Template defined at native 22 rows tall, 28 cols wide.
    # At runtime it is scaled to gun_h rows / gun_w cols using nearest-neighbour.

    # Gun scaling: target ~1/3 view height, but gracefully smaller on tiny terminals
    # Minimum readable size = 5 rows; aspect ratio preserved from template
    target_h = vr // 3
    gun_h    = max(5, min(target_h, vr - 4))   # at least 5, at most vr-4
    gun_w    = max(4, int(TMPL_COLS * gun_h / TMPL_ROWS))
    gun_w    = min(gun_w, cols * 2 // 5)        # never wider than 40% of terminal

    bob  = int(math.sin(_t*7) * max(1, gun_h//12))
    kick = -(gun_h//5) if sflash > 4 else 0

    # Reload animation: gun swings down (drops off screen) then rises back
    RELOAD_TIME = 1.2
    if reload_anim > 0:
        # t goes 1.0 -> 0.0 as reload completes
        t_rl = reload_anim / RELOAD_TIME
        # First half: drop down; second half: come back up
        if t_rl > 0.5:
            drop = int((1.0 - t_rl) * 2 * gun_h * 1.4)   # going down
        else:
            drop = int(t_rl * 2 * gun_h * 1.4)             # coming back up
        kick = drop   # positive = lower on screen
        # Also tilt: rotate gun slightly (shift x-origin) during mid-reload
        tilt = int(math.sin((1.0 - t_rl) * math.pi) * gun_w * 0.25)
    else:
        tilt = 0

    # Bottom-right anchor: gun base sits at bottom of view
    gx      = cols - gun_w - 1 + tilt
    gy_base = voff + vr - 1 + bob + kick

    for out_r in range(gun_h):
        # Map output row -> template row (out_r=0 is bottom, gun_h-1 is top)
        tmpl_r = int((gun_h - 1 - out_r) / max(1, gun_h - 1) * (TMPL_ROWS - 1))
        screen_row = gy_base - out_r
        if not (voff <= screen_row < voff + vr):
            continue
        for out_c in range(gun_w):
            tmpl_c = int(out_c / max(1, gun_w - 1) * (TMPL_COLS - 1))
            pixel = _tmpl_map.get((tmpl_c, tmpl_r))
            if pixel is None:
                continue
            ch2, r2, g2, b2 = pixel
            screen_col = gx + out_c
            if not (0 <= screen_col < cols):
                continue
            out.append(_goto(screen_col, screen_row))
            out.append(_fg(r2, g2, b2)); out.append(_bg(12, 10, 7)); out.append(ch2)

    # Reload progress bar
    if reload_anim > 0:
        bar_w  = gun_w
        filled = int(bar_w * (1.0 - reload_anim / RELOAD_TIME))
        bar_y  = gy_base - gun_h - 1
        if voff <= bar_y < voff + vr:
            out.append(_goto(gx, bar_y))
            out.append(_fg(255,220,0)); out.append(_bg(40,30,0))
            out.append('[' + '#'*filled + '-'*(bar_w-filled-2) + ']')
            label = ' RELOADING '
            lx = gx + bar_w//2 - len(label)//2
            if 0 <= lx < cols:
                out.append(_goto(lx, bar_y))
                out.append(_fg(255,255,100)); out.append(_bg(40,30,0))
                out.append(label)

    # Muzzle EXPLOSION at gun tip (not center screen)
    if sflash > 3:
        exp_x = gx                      # left edge = barrel tip
        exp_y = gy_base - gun_h + 1     # top of gun = muzzle
        exp_r = max(2, gun_h // 7)
        for dr in range(-exp_r, exp_r + 1):
            for dc in range(-exp_r - 1, exp_r + 2):
                dist_e = (dc*0.5)**2 + dr**2
                if dist_e <= exp_r**2:
                    gc2 = exp_x + dc; gr2 = exp_y + dr
                    if 0 <= gc2 < cols and voff <= gr2 < voff + vr:
                        # Radial colour: white center -> yellow -> orange edge
                        norm = dist_e / max(1, exp_r**2)
                        if norm < 0.15:
                            er,eg,eb = 255,255,220
                        elif norm < 0.5:
                            er,eg,eb = 255,200,50
                        else:
                            er,eg,eb = 220,80,10
                        ch_e = '*' if norm < 0.2 else ('+' if norm < 0.55 else '.')
                        out.append(_goto(gc2, gr2))
                        out.append(_fg(er,eg,eb)); out.append(_bg(er//4,eg//8,0))
                        out.append(ch_e)

    # Crosshair - white normally, red when hit_flash active
    cx2 = cols//2
    cy2 = half + voff
    if hit_flash > 0:
        cc = (255, 30, 30)    # red on hit
    elif sflash > 0:
        cc = (255, 200, 60)   # yellow on shoot
    else:
        cc = (220, 220, 220)  # white normally
    cfg = _fg(*cc); cbg = _bg(0,0,0)
    for dc in (-4,-3,-2, 2,3,4):
        out.append(_goto(cx2+dc, cy2)); out.append(cfg); out.append(cbg); out.append('-')
    for dr in (-2,-1, 1,2):
        out.append(_goto(cx2, cy2+dr)); out.append(cfg); out.append(cbg); out.append('|')
    out.append(_goto(cx2, cy2))
    out.append(_fg(255,50,50) if hit_flash > 0 else (_fg(255,255,255) if sflash else _fg(200,200,200)))
    out.append(cbg); out.append('+')

    # Enemy HP labels above their heads
    for e in enemies:
        if not e.alive: continue
        dx,dy = e.x-px, e.y-py
        d = math.hypot(dx,dy)
        if d < 0.2 or d > 14: continue
        ea = math.atan2(dy,dx)-angle
        ea = (ea+math.pi)%(2*math.pi)-math.pi
        if abs(ea) > HALF_FOV + 0.1: continue
        sx2 = int((0.5+ea/FOV)*cols)
        sh  = min(vr*2, int(vr/max(0.1,d)))
        top_s = max(0, half - sh//2)
        label = f"[HP : {e.hp}]"
        lx = sx2 - len(label)//2
        label_row = max(voff, top_s + voff - 1)
        if voff <= label_row < voff + vr and 0 <= lx < cols - len(label):
            # Colour by HP: green full -> yellow half -> red low
            hp_frac = e.hp / 3.0
            if hp_frac > 0.66:   lc = (80, 255, 80)
            elif hp_frac > 0.33: lc = (255, 200, 0)
            else:                lc = (255, 60, 60)
            out.append(_goto(lx, label_row))
            out.append(_fg(*lc)); out.append(_bg(0,0,0))
            out.append(label)

    # Kill message moved to warn row at bottom - nothing drawn at top for msg

    # Minimap
    mm_top = voff + 1
    for my in range(MAP_H):
        out.append(_goto(1, mm_top+my))
        for mx in range(MAP_W):
            v=WORLD_MAP[my][mx]
            if v:
                wc2=WALL_RGB.get(v,(80,30,30))
                out.append(_fg(wc2[0]//2,wc2[1]//2,wc2[2]//2))
                out.append(_bg(0,0,0)); out.append('#')
            else:
                out.append(_fg(20,5,5)); out.append(_bg(0,0,0)); out.append('.')
    for e in enemies:
        if e.alive:
            out.append(_goto(1+int(e.x), mm_top+int(e.y)))
            ec=(255,255,0) if e.state=='strafe' else (255,120,0) if e.state in ('chase','alert','search') else (160,0,0)
            out.append(_fg(*ec)); out.append(_bg(0,0,0)); out.append('@')
    if health_packs:
        for hp_pack in health_packs:
            if hp_pack.active:
                out.append(_goto(1+int(hp_pack.x), mm_top+int(hp_pack.y)))
                out.append(_fg(255,60,60)); out.append(_bg(0,0,0)); out.append('+')
    for ac in (ammo_crates or []):
        if ac.active:
            out.append(_goto(1+int(ac.x), mm_top+int(ac.y)))
            out.append(_fg(80,140,60)); out.append(_bg(0,0,0)); out.append('$')
    out.append(_goto(1+int(px), mm_top+int(py)))
    out.append(_fg(0,255,100)); out.append(_bg(0,0,0)); out.append('O')
    lx2=1+int(px+math.cos(angle)*1.6); ly2=mm_top+int(py+math.sin(angle)*1.6)
    if 0<=lx2<cols and voff<=ly2<voff+vr:
        out.append(_goto(lx2,ly2)); out.append(_fg(0,180,70))
        out.append(_bg(0,0,0)); out.append('>')

    # HUD separator
    hud_sep = voff + vr
    out.append(_goto(0, hud_sep)); out.append(_fg(80,90,140)); out.append(_bg(10,10,20))
    out.append('='*cols)

    hpc      = max(0, min(100, int(hp)))
    ammo_col = (255,220,60)  if ammo > 4 else (255,100,30)
    hcol     = (80,255,100)  if hpc>60 else (255,210,0) if hpc>30 else (255,60,60)
    BG       = (15, 15, 25)
    DIV      = (80, 80, 110)
    LBL      = (160,180,220)

    def _put_str(text, col, row, fg_rgb, bg_rgb=None):
        _bg2 = bg_rgb if bg_rgb is not None else BG
        for i, ch2 in enumerate(text):
            c = col + i
            if 0 <= c < cols:
                out.append(_goto(c, row))
                out.append(_fg(*fg_rgb)); out.append(_bg(*_bg2)); out.append(ch2)

    def _put_ch(ch2, col, row, fg_rgb, bg_rgb=None):
        _bg2 = bg_rgb if bg_rgb is not None else BG
        if 0 <= col < cols:
            out.append(_goto(col, row)); out.append(_fg(*fg_rgb)); out.append(_bg(*_bg2)); out.append(ch2)

    # Row hud_sep+1  &  hud_sep+2 : two-line HP bar + other stats
    row1 = hud_sep + 1
    row2 = hud_sep + 2

    # Fill both rows with dark bg first
    out.append(_goto(0, row1)); out.append(_fg(*BG)); out.append(_bg(*BG)); out.append(' '*cols)
    out.append(_goto(0, row2)); out.append(_fg(*BG)); out.append(_bg(*BG)); out.append(' '*cols)

    # HP label spanning both rows (left column)
    _put_str(f" {TEXT['hud_hp']} ", 0, row1, LBL)
    _put_str(f"{'':>{len(TEXT['hud_hp'])+2}}", 0, row2, LBL)   # blank same width

    cur = len(TEXT['hud_hp']) + 3

    # Two-line HP bar
    bar_w  = max(10, cols // 4)
    filled = int(bar_w * hpc / 100)
    empty  = bar_w - filled

    # Top bar row: filled blocks (bright)
    bar_top  = '\u2588'*filled + '\u2591'*empty
    # Bottom bar row: filled half-blocks (slightly dimmer) + number right-aligned
    bar_bot  = '\u2584'*filled + ' '*empty

    pct_str = f" {hpc:3d}%"

    _put_ch('[', cur, row1, DIV); cur += 1
    for i, ch2 in enumerate(bar_top):
        fc = hcol if i < filled else (50,20,10)
        _put_ch(ch2, cur+i, row1, fc)
    _put_ch(']', cur+bar_w, row1, DIV)

    _put_ch('[', cur, row2, DIV)
    for i, ch2 in enumerate(bar_bot):
        fc = tuple(max(0,v-40) for v in hcol) if i < filled else (30,12,6)
        _put_ch(ch2, cur+i, row2, fc)
    _put_ch(']', cur+bar_w, row2, DIV)
    _put_str(pct_str, cur+bar_w+1, row1, hcol)
    _put_str(f"{'':>{len(pct_str)}}", cur+bar_w+1, row2, BG)

    cur += bar_w + 1 + len(pct_str) + 1

    # Divider
    _put_ch('|', cur, row1, DIV); _put_ch('|', cur, row2, DIV); cur += 1

    # AMMO - both rows
    ammo_lbl = " AMMO "
    ammo_val1 = f" {ammo:2d} "
    ammo_val2 = f"+{reserve:2d} "
    _put_str(ammo_lbl, cur, row1, LBL); _put_str(ammo_lbl, cur, row2, LBL)
    cur += len(ammo_lbl)
    _put_str(ammo_val1, cur, row1, ammo_col)
    _put_str(ammo_val2, cur, row2, tuple(max(0,v-50) for v in ammo_col))
    cur += len(ammo_val1)

    _put_ch('|', cur, row1, DIV); _put_ch('|', cur, row2, DIV); cur += 1

    # KILLS
    kills_lbl = f" {TEXT['hud_kills']} "
    kills_val = f" {kills}/{total_enemies} "
    _put_str(kills_lbl, cur, row1, LBL)
    _put_str(kills_val, cur, row2, (255,220,80))
    cur += max(len(kills_lbl), len(kills_val))

    _put_ch('|', cur, row1, DIV); _put_ch('|', cur, row2, DIV); cur += 1

    # LEVEL
    lvl_lbl = f" {TEXT['hud_level']} "
    lvl_val = f"  {level}  "
    _put_str(lvl_lbl, cur, row1, LBL)
    _put_str(lvl_val, cur, row2, (180,220,255))
    cur += max(len(lvl_lbl), len(lvl_val))

    # (FPS counter removed)

    # Row hud_sep+3 : warnings CENTERED + message to right
    warn_row = hud_sep + 3

    out.append(_goto(0, warn_row)); out.append(_fg(0,0,0)); out.append(_bg(10,10,20))
    out.append(' ' * cols)

    # Collect active warning blocks
    warn_blocks = []   # list of (text, fr,fg2,fb, br,bg2,bb)

    if close_warn > 0:
        blink_on = int(_t * 6) % 2 == 0
        if blink_on: warn_blocks.append((TEXT["warn_close"], 255,30,0,   60,0,0))
        else:        warn_blocks.append((TEXT["warn_close"], 255,220,0,  80,40,0))

    if ammo_warn == 'reload':
        blink_on = int(_t * 5) % 2 == 0
        if blink_on: warn_blocks.append((TEXT["warn_reload"], 255,220,0, 70,50,0))
        else:        warn_blocks.append((TEXT["warn_reload"], 220,130,0, 40,25,0))
    elif ammo_warn == 'no_ammo':
        blink_on = int(_t * 4) % 2 == 0
        if blink_on: warn_blocks.append((TEXT["warn_no_ammo"], 255,20,20, 80,0,0))
        else:        warn_blocks.append((TEXT["warn_no_ammo"], 160,10,10, 40,0,0))

    # Calculate total width of warnings to center them
    GAP = 2
    warn_strs   = ['  ' + wb[0] + '  ' for wb in warn_blocks]
    total_warn_w = sum(len(s) for s in warn_strs) + GAP * max(0, len(warn_strs)-1)
    wx_start     = max(0, (cols - total_warn_w) // 2)

    wcur = wx_start
    for i, (wb, ws) in enumerate(zip(warn_blocks, warn_strs)):
        text, fr, fg2, fb, br, bg2, bb = wb
        out.append(_goto(wcur, warn_row))
        out.append(_fg(fr,fg2,fb)); out.append(_bg(br,bg2,bb))
        out.append(ws)
        wcur += len(ws)
        if i < len(warn_blocks)-1:
            out.append(_goto(wcur, warn_row)); out.append(_fg(*BG)); out.append(_bg(*BG))
            out.append(' '*GAP); wcur += GAP

    # Message to the right of the last warning (or left-start if none)
    if msg and msg_t > 0:
        msg_x = wcur + 2 if warn_blocks else 2
        mc = (255,200,80) if int(_t*4)%2 else (200,140,30)
        out.append(_goto(msg_x, warn_row))
        out.append(_fg(*mc)); out.append(_bg(30,15,0))
        out.append(msg.strip())

    return ''.join(out)


def build_splash(cols, rows):
    out=[HOME]; cx=cols//2; t=time.time()
    _t = t  # Use consistent naming
    for row in range(rows):
        out.append(_goto(0,row))
        out.append(_fg(18,4,4) if row%2==0 else _fg(0,0,0))
        out.append(_bg(6,0,0)  if row%2==0 else _bg(4,0,0))
        out.append(('~' if row%2==0 else ' ')*cols)
    out.append(_fg(140,22,22)); out.append(_bg(0,0,0))
    out.append(_goto(0,0));      out.append('='*cols)
    out.append(_goto(0,rows-1)); out.append('='*cols)
    for r in range(1,rows-1):
        out.append(_goto(0,r));      out.append('|')
        out.append(_goto(cols-1,r)); out.append('|')
    lt=rows//2-len(LOGO_BIG)//2-5
    pr=int(150+80*math.sin(_t*2.5))
    for li,line in enumerate(LOGO_BIG):
        lx=cx-len(line)//2
        out.append(_goto(lx,lt+li))
        for ci2,ch in enumerate(line):
            w=int(75+65*math.sin(ci2*0.25+_t*3))
            out.append(_fg(min(255,pr),w//10,w//14)); out.append(_bg(0,0,0)); out.append(ch)
    sub="R A Y C A S T E R   E N G I N E"
    sy=lt+len(LOGO_BIG)+1
    out.append(_goto(cx-len(TEXT["splash_sub"])//2,sy)); out.append(_fg(105,32,12)); out.append(_bg(0,0,0)); out.append(TEXT["splash_sub"])
    cy2=sy+3
    for li,line in enumerate(_SPLASH_CTRL):
        lx=cx-len(line)//2; out.append(_goto(lx,cy2+li))
        for ch in line:
            out.append(_fg(85,22,6) if ch in '+-|' else _fg(145,65,30))
            out.append(_bg(0,0,0)); out.append(ch)
    prompt=TEXT["splash_prompt"]
    blink=int(_t*2)%2==0
    out.append(_goto(cx-len(prompt)//2,cy2+len(_SPLASH_CTRL)+2))
    out.append(_fg(215,50,12) if blink else _fg(80,14,3))
    out.append(_bg(0,0,0)); out.append(prompt)
    return ''.join(out)


def build_end(cols, rows, title, subtitle, prompt_text, kills_n, win):
    out=[HOME]; cx,cy=cols//2,rows//2
    _t = time.time()
    tc=(0,220,90) if win else (210,25,15)
    sc=(0,130,55) if win else (120,15,8)
    for row in range(rows):
        out.append(_goto(0,row))
        out.append(_fg(0,0,0))
        out.append(_bg(0,6,2) if win else _bg(7,0,0))
        out.append(' '*cols)
    out.append(_goto(cx-len(title)//2,cy-4))
    out.append(_fg(*tc)); out.append(_bg(0,0,0)); out.append(title)
    out.append(_goto(cx-len(subtitle)//2,cy-2))
    out.append(_fg(*sc)); out.append(_bg(0,0,0)); out.append(subtitle)
    stat=f"{TEXT['hud_kills']}: {kills_n}"
    out.append(_goto(cx-len(stat)//2,cy))
    out.append(_fg(165,90,22)); out.append(_bg(0,0,0)); out.append(stat)
    blink=int(_t*2)%2==0
    out.append(_goto(cx-len(prompt_text)//2,cy+3))
    out.append(_fg(*tc) if blink else _fg(*sc))
    out.append(_bg(0,0,0)); out.append(prompt_text)
    return ''.join(out)


def build_level_screen(cols, rows, level, kills_n, next_enemy_count=None):
    out=[HOME]; cx,cy=cols//2,rows//2
    _t = time.time()
    tc=(255,180,0); sc=(180,100,0)
    for row in range(rows):
        out.append(_goto(0,row))
        out.append(_fg(0,0,0)); out.append(_bg(8,5,0))
        out.append(' '*cols)
    title    = TEXT["level_title"]
    subtitle = TEXT["level_subtitle"]
    # next_enemy_count is passed in from game.py to avoid circular import
    nec = next_enemy_count if next_enemy_count is not None else (8 + level * 4)
    next_lv  = f"NEXT: LEVEL {level+1}  -  {nec} ENEMIES"
    prompt   = TEXT["level_prompt"]
    out.append(_goto(cx-len(title)//2,    cy-4)); out.append(_fg(*tc)); out.append(_bg(0,0,0)); out.append(title)
    out.append(_goto(cx-len(subtitle)//2, cy-2)); out.append(_fg(*sc)); out.append(_bg(0,0,0)); out.append(subtitle)
    out.append(_goto(cx-len(next_lv)//2,  cy));   out.append(_fg(200,200,200)); out.append(_bg(0,0,0)); out.append(next_lv)
    blink=int(_t*2)%2==0
    out.append(_goto(cx-len(prompt)//2,   cy+3))
    out.append(_fg(*tc) if blink else _fg(*sc))
    out.append(_bg(0,0,0)); out.append(prompt)
    return ''.join(out)
