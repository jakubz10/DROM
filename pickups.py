import math, random
from map_data import WORLD_MAP


class HealthPack:
    __slots__ = ("x","y","active")
    def __init__(self, x, y): self.x=x; self.y=y; self.active=True


class AmmoCrate:
    __slots__ = ("x","y","active")
    def __init__(self, x, y): self.x=x; self.y=y; self.active=True


def _make_health_packs(count=5):
    mh = len(WORLD_MAP); mw = len(WORLD_MAP[0])
    free = [(x+0.5, y+0.5) for y in range(1, mh-1) for x in range(1, mw-1)
            if WORLD_MAP[y][x] == 0]
    free = [(x,y) for x,y in free if math.hypot(x-2.5, y-2.5) > 3.0]
    random.shuffle(free)
    return [HealthPack(x, y) for x,y in free[:count]]


def _make_ammo_crates(count=4):
    mh = len(WORLD_MAP); mw = len(WORLD_MAP[0])
    free = [(x+0.5, y+0.5) for y in range(1, mh-1) for x in range(1, mw-1)
            if WORLD_MAP[y][x] == 0]
    free = [(x,y) for x,y in free if math.hypot(x-2.5, y-2.5) > 3.0]
    random.shuffle(free)
    return [AmmoCrate(x, y) for x,y in free[:count]]


class GunUpgrade:
    __slots__ = ("x","y","active")
    def __init__(self, x, y): self.x=x; self.y=y; self.active=True


def _make_gun_upgrade():
    mh = len(WORLD_MAP); mw = len(WORLD_MAP[0])
    free = [(x+0.5, y+0.5) for y in range(1,mh-1) for x in range(1,mw-1)
            if WORLD_MAP[y][x] == 0]
    free = [(x,y) for x,y in free if math.hypot(x-2.5,y-2.5) > 6.0]
    random.shuffle(free)
    return GunUpgrade(*free[0]) if free else None
