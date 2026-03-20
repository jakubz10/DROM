import math, random
from map_data import WORLD_MAP, MAP_H, MAP_W
from raycaster import has_los

ENEMY_SPAWNS = [
    (3.5, 3.5), (20.5, 3.5), (3.5, 20.5), (20.5, 20.5),
    (7.5, 14.5), (6.5, 17.5), (17.5, 6.5), (17.5, 17.5),
]

# Patrol waypoints for bigger map
_WAYPOINTS = [
    (2.5,2.5),(21.5,2.5),(21.5,21.5),(2.5,21.5),
    (11.5,2.5),(21.5,11.5),(11.5,21.5),(2.5,11.5),
    (6.5,6.5),(17.5,6.5),(17.5,17.5),(6.5,17.5),
]


def _lerp_angle(a, b, t):
    """Smoothly interpolate angle a toward b."""
    diff = (b - a + math.pi) % (2*math.pi) - math.pi
    return a + diff * min(1.0, t)


class Enemy:
    __slots__ = ("x","y","alive","eid",
                 "state","angle",
                 "speed","alert_t","strafe_dir",
                 "attack_cd","wp_idx","stuck_t",
                 "hp","pain_t",
                 "search_t","last_px","last_py","hear_range")

    # speeds per state
    SPD_PATROL = 0.5
    SPD_CHASE  = 1.2
    SPD_STRAFE = 0.9

    SIGHT_RANGE   = 16.0
    ATTACK_RANGE  = 1.6    # must get close to knife you - was 7.0
    MELEE_RANGE   = 1.6    # knife reach
    ATTACK_DAMAGE = 0.0    # no ranged damage
    MELEE_DAMAGE  = 22.0   # knife damage per second (applied in melee)

    def __init__(self, x, y, eid):
        self.x = x; self.y = y; self.alive = True; self.eid = eid
        self.state      = 'patrol'
        self.angle      = random.uniform(0, 2*math.pi)
        self.speed      = self.SPD_PATROL
        self.alert_t    = 0.0
        self.strafe_dir = random.choice((-1, 1))
        self.attack_cd  = random.uniform(0.5, 1.5)
        self.wp_idx     = eid % len(_WAYPOINTS)
        self.stuck_t    = 0.0
        self.hp         = 3
        self.pain_t     = 0.0
        self.search_t   = 0.0   # time spent searching last known position
        self.last_px    = x     # last known player position
        self.last_py    = y
        self.hear_range = 6.0   # radius within which footsteps are "heard"

    # called once per frame
    def update(self, dt, px, py, all_enemies):
        if not self.alive: return 0.0

        self._push_out_of_wall()

        dx   = px - self.x
        dy   = py - self.y
        dist = math.hypot(dx, dy)
        to_player_angle = math.atan2(dy, dx)
        can_see = dist < self.SIGHT_RANGE and has_los(self.x, self.y, px, py)
        can_hear = dist < self.hear_range   # proximity "noise" detection

        damage_dealt = 0.0

        # Remember last known player position whenever visible
        if can_see:
            self.last_px = px; self.last_py = py

        # State transitions
        if self.state == 'patrol':
            if can_see:
                self.state   = 'alert'
                self.alert_t = 0.25
            elif can_hear:
                # Heard the player - move toward the noise without full alert
                self.last_px = px; self.last_py = py
                self.state   = 'search'
                self.search_t = 4.0

        elif self.state == 'alert':
            self.alert_t -= dt
            self.angle = _lerp_angle(self.angle, to_player_angle, dt*10)
            if self.alert_t <= 0:
                self.state = 'chase'

        elif self.state == 'chase':
            if can_see:
                self.stuck_t = 0.0
                if dist < self.ATTACK_RANGE:
                    self.state = 'strafe'
            else:
                self.stuck_t += dt
                if self.stuck_t > 1.5:
                    # Lost sight - go to last known position
                    self.state    = 'search'
                    self.search_t = 5.0
                    self.stuck_t  = 0.0

        elif self.state == 'strafe':
            if dist > self.ATTACK_RANGE * 1.8 or not can_see:
                self.state = 'chase'

        elif self.state == 'search':
            if can_see:
                self.state   = 'alert'
                self.alert_t = 0.2
            elif can_hear:
                # Update noise source
                self.last_px = px; self.last_py = py
                self.search_t = max(self.search_t, 3.0)
            else:
                self.search_t -= dt
                if self.search_t <= 0:
                    self.state = 'patrol'

        # State actions
        if self.state == 'patrol':
            damage_dealt = self._do_patrol(dt, px, py)
        elif self.state == 'alert':
            pass
        elif self.state == 'chase':
            damage_dealt = self._do_chase(dt, px, py, dist, to_player_angle, can_see)
        elif self.state == 'strafe':
            damage_dealt = self._do_strafe(dt, px, py, dist, to_player_angle)
        elif self.state == 'search':
            damage_dealt = self._do_search(dt)

        # Separation
        for other in all_enemies:
            if other is self or not other.alive: continue
            ox = self.x - other.x; oy = self.y - other.y
            od2 = ox*ox + oy*oy
            if 0 < od2 < 0.7225:   # 0.85**2
                od = math.sqrt(od2)
                push = (0.85 - od) * 0.6
                self._try_move(ox/od*push, oy/od*push)

        if self.pain_t > 0: self.pain_t -= dt
        return damage_dealt

    # Hit by player
    def hit(self):
        """Returns True if enemy dies."""
        self.hp     -= 1
        self.pain_t  = 0.18
        if self.state == 'patrol':
            self.state   = 'alert'
            self.alert_t = 0.2
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    # Movement helpers
    MARGIN = 0.35   # keep this distance from any wall centre

    def _cell_free(self, x, y):
        """True if position (x,y) is inside a free cell with MARGIN clearance."""
        mx, my = int(x), int(y)
        if not (0 <= mx < MAP_W and 0 <= my < MAP_H): return False
        if WORLD_MAP[my][mx]: return False
        # Check margin against the four nearest wall boundaries
        if x - mx < self.MARGIN and mx > 0          and WORLD_MAP[my][mx-1]: return False
        if mx+1 - x < self.MARGIN and mx+1 < MAP_W  and WORLD_MAP[my][mx+1]: return False
        if y - my < self.MARGIN and my > 0           and WORLD_MAP[my-1][mx]: return False
        if my+1 - y < self.MARGIN and my+1 < MAP_H  and WORLD_MAP[my+1][mx]: return False
        return True

    def _try_move(self, dx, dy):
        """Attempt move with wall-margin safety; tries axes independently."""
        nx = self.x + dx
        ny = self.y + dy
        # Full move
        if self._cell_free(nx, ny):
            self.x = nx; self.y = ny; return True
        # Slide X only
        if self._cell_free(nx, self.y):
            self.x = nx; return True
        # Slide Y only
        if self._cell_free(self.x, ny):
            self.y = ny; return True
        return False

    def _push_out_of_wall(self):
        """If somehow inside geometry, push to nearest free position."""
        if self._cell_free(self.x, self.y): return
        for r in (0.4, 0.6, 0.8, 1.0, 1.4):
            for a in range(0, 360, 45):
                rad = math.radians(a)
                cx = self.x + math.cos(rad)*r
                cy = self.y + math.sin(rad)*r
                if self._cell_free(cx, cy):
                    self.x = cx; self.y = cy; return

    def _do_search(self, dt):
        """Walk toward last known player position, scanning left/right."""
        dx = self.last_px - self.x; dy = self.last_py - self.y
        d  = math.hypot(dx, dy)
        if d < 0.6:
            # Reached destination - scan by rotating
            self.angle += dt * 1.8 * self.strafe_dir
            return 0.0
        target_a = math.atan2(dy, dx)
        self.angle = _lerp_angle(self.angle, target_a, dt*5)
        spd = self.SPD_PATROL * 1.3 * dt
        self._try_move(math.cos(self.angle)*spd, math.sin(self.angle)*spd)
        return 0.0

    def _do_patrol(self, dt, px, py):
        # Skip waypoints that are inside walls
        for _ in range(len(_WAYPOINTS)):
            tx, ty = _WAYPOINTS[self.wp_idx]
            if self._cell_free(tx, ty): break
            self.wp_idx = (self.wp_idx + 1) % len(_WAYPOINTS)

        tx, ty = _WAYPOINTS[self.wp_idx]
        dx = tx - self.x; dy = ty - self.y
        d  = math.hypot(dx, dy)
        if d < 0.5:
            self.wp_idx = (self.wp_idx + 1) % len(_WAYPOINTS)
            return 0.0
        target_a = math.atan2(dy, dx)
        self.angle = _lerp_angle(self.angle, target_a, dt*3)
        spd = self.SPD_PATROL * dt
        moved = self._try_move(math.cos(self.angle)*spd, math.sin(self.angle)*spd)
        if not moved:
            # Nudge to next waypoint if stuck for too long
            self.stuck_t += dt
            if self.stuck_t > 1.5:
                self.wp_idx = (self.wp_idx + 1) % len(_WAYPOINTS)
                self.stuck_t = 0.0
        else:
            self.stuck_t = 0.0
        return 0.0

    def _do_chase(self, dt, px, py, dist, to_player_angle, can_see):
        damage = 0.0
        if can_see:
            self.angle = _lerp_angle(self.angle, to_player_angle, dt*6)

        spd = self.SPD_CHASE * dt
        moved = self._try_move(math.cos(self.angle)*spd, math.sin(self.angle)*spd)

        if not moved:
            self.stuck_t += dt
            if self.stuck_t > 0.3:
                # Try 8 directions, pick the one that gets us closer to player
                best_d = dist; best_a = self.angle
                for deg in range(0, 360, 45):
                    ta = math.radians(deg)
                    tx2 = self.x + math.cos(ta)*spd
                    ty2 = self.y + math.sin(ta)*spd
                    if self._cell_free(tx2, ty2):
                        nd = math.hypot(px-tx2, py-ty2)
                        if nd < best_d:
                            best_d = nd; best_a = ta
                self.angle = best_a
                self._try_move(math.cos(self.angle)*spd, math.sin(self.angle)*spd)
                if self.stuck_t > 2.0:
                    # Flip strafe direction as last resort
                    self.strafe_dir *= -1
                    self.stuck_t = 0.0
        else:
            self.stuck_t = 0.0

        if dist < self.MELEE_RANGE:
            damage = self.MELEE_DAMAGE * dt
        return damage

    def _do_strafe(self, dt, px, py, dist, to_player_angle):
        """Knife range: circle and slash. No ranged attack."""
        damage = 0.0
        # Always face player
        self.angle = _lerp_angle(self.angle, to_player_angle, dt*10)
        # Circle player while closing in
        strafe_a = to_player_angle + self.strafe_dir * math.pi/2
        spd = self.SPD_STRAFE * dt
        moved = self._try_move(math.cos(strafe_a)*spd, math.sin(strafe_a)*spd)
        if not moved:
            self.strafe_dir *= -1
        if random.random() < dt * 0.35:
            self.strafe_dir *= -1

        # Knife slash: damage when close enough
        self.attack_cd -= dt
        if dist < self.MELEE_RANGE and self.attack_cd <= 0:
            self.attack_cd = random.uniform(0.55, 1.1)  # slash cadence
            damage = self.MELEE_DAMAGE
        return damage
