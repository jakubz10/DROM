import math
from map_data import WORLD_MAP

FOV        = math.pi / 3.0
HALF_FOV   = FOV / 2.0
MAX_DIST   = 16.0
MOUSE_SENS = 0.003   # radians per pixel - tune to taste

# DDA raycaster
def cast_ray(px, py, angle):
    ca = math.cos(angle) or 1e-10
    sa = math.sin(angle) or 1e-10
    mx, my = int(px), int(py)
    ddx = abs(1/ca); ddy = abs(1/sa)
    sx = 1 if ca>0 else -1; sy = 1 if sa>0 else -1
    sdx = (mx+1-px)*ddx if ca>0 else (px-mx)*ddx
    sdy = (my+1-py)*ddy if sa>0 else (py-my)*ddy
    side = 0
    for _ in range(80):
        if sdx < sdy: sdx+=ddx; mx+=sx; side=0
        else:         sdy+=ddy; my+=sy; side=1
        if not (0<=mx<len(WORLD_MAP[0]) and 0<=my<len(WORLD_MAP)): return 99.0,0,0
        wt = WORLD_MAP[my][mx]
        if wt:
            d = (sdx-ddx) if side==0 else (sdy-ddy)
            return max(0.01,d), side, wt
    return 99.0,0,0

# Line-of-sight helper
def has_los(ax, ay, bx, by, steps=16):
    """True if a straight line from (ax,ay) to (bx,by) hits no wall."""
    for i in range(1, steps):
        t  = i / steps
        mx = int(ax + (bx-ax)*t)
        my = int(ay + (by-ay)*t)
        if not (0<=mx<len(WORLD_MAP[0]) and 0<=my<len(WORLD_MAP)): return False
        if WORLD_MAP[my][mx]: return False
    return True
