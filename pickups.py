import math, random
from map_data import WORLD_MAP, MAP_H, MAP_W


class HealthPack:
    __slots__ = ("x","y","active")
    def __init__(self, x, y): self.x=x; self.y=y; self.active=True


class AmmoCrate:
    __slots__ = ("x","y","active")
    def __init__(self, x, y): self.x=x; self.y=y; self.active=True


def _make_health_packs(count=5):
    free = [(x+0.5, y+0.5)
            for y in range(1, MAP_H-1)
            for x in range(1, MAP_W-1)
            if WORLD_MAP[y][x] == 0]
    free = [(x,y) for x,y in free if math.hypot(x-2.5, y-2.5) > 3.0]
    random.shuffle(free)
    return [HealthPack(x, y) for x,y in free[:count]]


def _make_ammo_crates(count=4):
    free = [(x+0.5, y+0.5)
            for y in range(1, MAP_H-1)
            for x in range(1, MAP_W-1)
            if WORLD_MAP[y][x] == 0]
    free = [(x,y) for x,y in free if math.hypot(x-2.5, y-2.5) > 3.0]
    random.shuffle(free)
    return [AmmoCrate(x, y) for x,y in free[:count]]
