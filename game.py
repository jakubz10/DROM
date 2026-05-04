import math, time, random, json, os, sys
from console import _wcon, _term_size, ALT_SCR, HIDE_CUR, CLEAR_SCR, SHOW_CUR, NORM_SCR, RESET_ALL
from console import kernel32, CONOUT
from input import poll_input
import input as _input_mod
from console import user32
from datetime import datetime
from map_data import WORLD_MAP, WAYPOINTS, load_map, WALL_BREAKS
from raycaster import cast_ray
from enemy import Enemy, Boss
from pickups import HealthPack, AmmoCrate, GunUpgrade, _make_health_packs, _make_ammo_crates, _make_gun_upgrade
from renderer import build_frame, build_splash, build_end, build_level_screen, build_endgame_menu
from text import TEXT

def _save_path():
    base = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base, 'drom_save.json')

def _load_stats():
    try:
        with open(_save_path(), 'r') as f:
            d = json.load(f)
        return dict(highest_level=d.get('highest_level', 0),
                    total_kills=d.get('total_kills',
                                      d.get('droms_killed', 0) + d.get('bosses_killed', 0)),
                    times_beat_5=d.get('times_beat_5', 0))
    except Exception:
        return dict(highest_level=0, total_kills=0, times_beat_5=0)

def _save_stats(stats):
    try:
        with open(_save_path(), 'w') as f:
            json.dump(stats, f)
    except Exception:
        pass


def _qsave_path():
    base = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base, 'drom_quicksave.json')


def _serialize_enemy(e):
    d = {s: getattr(e, s) for s in Enemy.__slots__}
    d['is_boss'] = e.is_boss
    if e.is_boss:
        d['_wall_break_cd'] = e._wall_break_cd
    return d


def _deserialize_enemy(d):
    cls = Boss if d.get('is_boss') else Enemy
    e = cls.__new__(cls)
    for s in Enemy.__slots__:
        setattr(e, s, d[s])
    if cls is Boss:
        e._wall_break_cd = d.get('_wall_break_cd', 0.0)
    return e


def _quicksave(g):
    data = {}
    for k, v in g.items():
        if k in ('enemies', 'bosses'):
            data[k] = [_serialize_enemy(e) for e in v]
        elif k in ('health_packs', 'ammo_crates'):
            data[k] = [{'x': p.x, 'y': p.y, 'active': p.active} for p in v]
        elif k == 'gun_upgrade':
            data[k] = {'x': v.x, 'y': v.y, 'active': v.active} if v else None
        elif k in ('wall_hp', 'wall_fall'):
            data[k] = {f"{kk[0]},{kk[1]}": vv for kk, vv in v.items()}
        elif k == 'blood_trail':
            data[k] = [[a, b] for a, b in v]
        else:
            data[k] = v
    save = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'world_map': [row[:] for row in WORLD_MAP],
        'game': data,
    }
    try:
        with open(_qsave_path(), 'w') as f:
            json.dump(save, f)
        return True
    except Exception:
        return False


def _quickload():
    try:
        with open(_qsave_path(), 'r') as f:
            save = json.load(f)
    except Exception:
        return None
    data = save['game']
    level = data['level']
    load_map(level)
    WORLD_MAP.clear()
    WORLD_MAP.extend([row[:] for row in save['world_map']])
    g = {}
    for k, v in data.items():
        if k == 'enemies':
            g[k] = [_deserialize_enemy(d) for d in v]
        elif k == 'bosses':
            g[k] = [_deserialize_enemy(d) for d in v]
        elif k == 'health_packs':
            g[k] = []
            for d in v:
                p = HealthPack(d['x'], d['y']); p.active = d['active']; g[k].append(p)
        elif k == 'ammo_crates':
            g[k] = []
            for d in v:
                p = AmmoCrate(d['x'], d['y']); p.active = d['active']; g[k].append(p)
        elif k == 'gun_upgrade':
            if v:
                gu = GunUpgrade(v['x'], v['y']); gu.active = v['active']
                g[k] = gu
            else:
                g[k] = None
        elif k in ('wall_hp', 'wall_fall'):
            g[k] = {}
            for sk, sv in v.items():
                parts = sk.split(',')
                g[k][(int(parts[0]), int(parts[1]))] = sv
        elif k == 'blood_trail':
            g[k] = {(a, b) for a, b in v}
        else:
            g[k] = v
    return g


def _get_save_info():
    try:
        with open(_qsave_path(), 'r') as f:
            save = json.load(f)
        return save.get('timestamp')
    except Exception:
        return None


MOVE_SPEED  = 3.8
ROT_SPEED   = 2.5
WALL_HP_BY_TYPE = {1: 4, 2: 5, 3: 6, 4: 7, 5: 2137}
RELOAD_TIME = 1.2
MAG_SIZE    = 16
MAX_RESERVE = 32
WARN_DIST   = 2.8


def _enemies_for_level(level):
    """Level 1=8, level 2=12, level 3=16, ... (+4 each level)."""
    return 8 + (level - 1) * 4


def _bosses_for_level(level):
    if level <= 2:
        return 1
    if level >= 5:
        return 3
    return 2


def _make_enemies(count):
    """Spawn `count` enemies at random free positions across the map."""
    free = [(x+0.5, y+0.5)
            for y in range(1, len(WORLD_MAP)-1)
            for x in range(1, len(WORLD_MAP[0])-1)
            if WORLD_MAP[y][x] == 0]
    # Keep away from player start (2.5, 2.5)
    free = [(x,y) for x,y in free if math.hypot(x-2.5, y-2.5) > 5.0]
    random.shuffle(free)
    spawns = free[:count]
    return [Enemy(x, y, i) for i, (x, y) in enumerate(spawns)]


def _make_bosses(count, id_offset=0):
    """Spawn `count` bosses at random free positions far from the player start."""
    free = [(x+0.5, y+0.5)
            for y in range(1, len(WORLD_MAP)-1)
            for x in range(1, len(WORLD_MAP[0])-1)
            if WORLD_MAP[y][x] == 0]
    free = [(x,y) for x,y in free if math.hypot(x-2.5, y-2.5) > 7.0]
    random.shuffle(free)
    spawns = free[:count]
    return [Boss(x, y, id_offset + i) for i, (x, y) in enumerate(spawns)]


def new_game(level=1):
    load_map(level)
    count = _enemies_for_level(level)
    boss_count = _bosses_for_level(level)
    return dict(px=2.5, py=2.5, angle=0.0, hp=100.0, kills=0,
                enemies=_make_enemies(count),
                total_enemies=count, level=level,
                health_packs=_make_health_packs(3),
                ammo_crates=_make_ammo_crates(min(level, 5)),
                gun_upgrade=_make_gun_upgrade(),
                gun_upgraded=False,
                gun_upgrade_anim=0.0,
                ammo=16, reserve=32,   # mag=16, reserve max=32, total max=48
                reload_anim=0.0,
                ammo_warn='',
                hit_flash=0,
                sflash=0, dalpha=0.0, msg='', msg_t=0,
                state='splash', close_warn=0.0,
                bosses=[], bosses_spawned=False,
                boss_count=boss_count,
                win_delay_t=0.0,
                wall_hp={}, wall_fall={}, wall_explosions=[],
                boss_art_t=0.0,
                blood_trail=set(),
                drom_kills=0, boss_kills=0)


_CHEAT_SEQ = [0x53, 0x4B, 0x4E, 0x52, 0x55, 0x53]  # S K N R U S
_cheat_pos = 0
_cheat_prev = [False] * 256

def _poll_cheat_key():
    global _cheat_pos
    vk = _CHEAT_SEQ[_cheat_pos]
    now = bool(user32.GetAsyncKeyState(vk) & 0x8000)
    edge = now and not _cheat_prev[vk]
    _cheat_prev[vk] = now
    if edge:
        _cheat_pos += 1
        if _cheat_pos >= len(_CHEAT_SEQ):
            _cheat_pos = 0
            _input_mod.CHEATS_ENABLED = True
            return True
    elif now:
        pass
    else:
        for i, v in enumerate(_CHEAT_SEQ):
            if i == _cheat_pos:
                continue
            was = bool(user32.GetAsyncKeyState(v) & 0x8000)
            if was and not _cheat_prev[v]:
                _cheat_pos = 0
            _cheat_prev[v] = was
    return False


def _commit_stats(g, stats):
    stats['total_kills'] += g['drom_kills'] + g['boss_kills']
    g['drom_kills'] = 0; g['boss_kills'] = 0
    lvl = g['level']
    if lvl > stats['highest_level']:
        stats['highest_level'] = lvl
    _save_stats(stats)


def main():
    _wcon(ALT_SCR + HIDE_CUR + CLEAR_SCR)

    cols,rows = _term_size()
    g=new_game()
    stats = _load_stats()
    last_t=time.perf_counter()
    fps_acc=fps_cnt=fps_val=frame=0
    save_ts_cache = _get_save_info()
    prev_state = None
    show_controls = False

    try:
        while True:
            now=time.perf_counter(); dt=min(now-last_t,0.05); last_t=now
            if frame%60==0:
                nc,nr=_term_size()
                if nc!=cols or nr!=rows:
                    cols,rows=nc,nr; _wcon(CLEAR_SCR)
            frame+=1

            ks, shoot, flip, reload_key, quit_now, cheat_l5, killall, cheat_ammo_up, cheat_heal, save_key, toggle_key = poll_input()

            state=g['state']
            if state == 'splash' and prev_state != 'splash':
                save_ts_cache = _get_save_info()
                show_controls = False
            prev_state = state

            if quit_now:
                if state == 'splash':
                    break
                else:
                    _commit_stats(g, stats)
                    g = new_game(1); g['state'] = 'splash'
                    _wcon(CLEAR_SCR)
                    continue

            # SPLASH
            if state=='splash':
                if not _input_mod.CHEATS_ENABLED:
                    _poll_cheat_key()
                if toggle_key:
                    show_controls = not show_controls
                    _wcon(CLEAR_SCR)
                fs=build_splash(cols,rows,_input_mod.CHEATS_ENABLED,stats,save_ts_cache,show_controls)
                if shoot: g=new_game(1); g['state']='play'
                elif cheat_l5: g=new_game(5); g['state']='play'
                elif save_key and save_ts_cache:
                    loaded = _quickload()
                    if loaded:
                        g = loaded; g['state'] = 'play'
                        _wcon(CLEAR_SCR)

            # PLAY
            elif state=='play':
                if save_key:
                    if _quicksave(g):
                        g['msg'] = '  STATE SAVED  '; g['msg_t'] = 60
                    else:
                        g['msg'] = '  SAVE FAILED  '; g['msg_t'] = 60
                # DEV: T = gun upgrade + full ammo
                if cheat_ammo_up:
                    g['gun_upgraded'] = True
                    g['ammo']    = 16
                    g['reserve'] = 32
                    g['msg'] = '  [DEV] GUN UPGRADED + AMMO FILLED  '; g['msg_t'] = 60
                # DEV: I = full heal
                if cheat_heal:
                    g['hp'] = 100.0
                    g['msg'] = '  [DEV] HEALTH RESTORED  '; g['msg_t'] = 60
                # DEV: Y = kill all enemies instantly
                if killall:
                    has_regular = any(_e.alive for _e in g['enemies'])
                    if has_regular:
                        for _e in g['enemies']:
                            if _e.alive:
                                _e.alive = False; _e.dying = True
                                _e.death_t = 1.0; _e.pain_t = 0.5
                                g['kills'] += 1; g['drom_kills'] += 1
                        g['msg'] = '  [DEV] ALL DROMS KILLED  '; g['msg_t'] = 60
                    else:
                        if not g['bosses_spawned']:
                            g['bosses'] = _make_bosses(g['boss_count'], id_offset=len(g['enemies']))
                            g['bosses_spawned'] = True
                        for _e in g['bosses']:
                            if _e.alive:
                                _e.alive = False; _e.dying = True
                                _e.death_t = 1.8; _e.pain_t = 0.9
                                g['kills'] += 1; g['boss_kills'] += 1
                        if g['win_delay_t'] <= 0:
                            g['win_delay_t'] = 6.0
                        g['msg'] = '  [DEV] BOSSES KILLED  '; g['msg_t'] = 60

                px,py,angle=g['px'],g['py'],g['angle']
                all_combatants = g['enemies'] + g['bosses']

                turn = 0.0
                if 'left'  in ks: turn -= ROT_SPEED*dt
                if 'right' in ks: turn += ROT_SPEED*dt
                if flip: turn += math.pi
                angle += turn

                fwd=side=0.0
                if 'w'  in ks: fwd  = MOVE_SPEED*dt
                if 's'  in ks: fwd  =-MOVE_SPEED*dt
                if 'sl' in ks: side =-MOVE_SPEED*dt*0.85
                if 'sr' in ks: side = MOVE_SPEED*dt*0.85

                nx=px+math.cos(angle)*fwd+math.cos(angle+math.pi/2)*side
                ny=py+math.sin(angle)*fwd+math.sin(angle+math.pi/2)*side
                if WORLD_MAP[int(ny)][int(px)]==0: py=ny
                if WORLD_MAP[int(py)][int(nx)]==0: px=nx
                g['px'],g['py'],g['angle']=px,py,angle

                if shoot:
                    if g['reload_anim'] > 0:
                        g['msg'] = '  RELOADING...  '; g['msg_t'] = 20
                    elif g['ammo'] > 0:
                        g['ammo'] -= 1
                        g['sflash']=8
                        shots = [angle] if not g['gun_upgraded'] else [angle-0.05, angle+0.05]
                        for sa in shots:
                            wd, _, wt = cast_ray(px, py, math.cos(sa), math.sin(sa))
                            be=None; bd=wd
                            for e in all_combatants:
                                if not e.alive: continue
                                ex,ey=e.x-px,e.y-py; ed=math.hypot(ex,ey)
                                ea=math.atan2(ey,ex)-sa
                                ea=(ea+math.pi)%(2*math.pi)-math.pi
                                if abs(ea)<0.09 and ed<bd: be=e; bd=ed
                            if be:
                                died=be.hit()
                                if died:
                                    g['kills']+=1
                                    if be.is_boss: g['boss_kills'] += 1
                                    else: g['drom_kills'] += 1
                                    if be.is_boss:
                                        g['msg']=TEXT['msg_boss_kill']; g['msg_t']=80
                                    else:
                                        g['msg']=TEXT['msg_kill']; g['msg_t']=55
                                    # Win check: all regular enemies dead + all bosses dead
                                    reg_clear  = all(not e.alive for e in g['enemies'])
                                    boss_clear = all(not b.alive for b in g['bosses'])
                                    if reg_clear and boss_clear and g['bosses_spawned'] and g['win_delay_t'] <= 0:
                                        g['win_delay_t'] = 6.0
                                        g['msg'] = '  LEVEL CLEAR!  '; g['msg_t'] = 180
                                g['hit_flash']=8
                            elif wt and 1 <= wt <= 5 and wd < 99.0:
                                hmx = int(px + math.cos(sa) * (wd + 0.01))
                                hmy = int(py + math.sin(sa) * (wd + 0.01))
                                key = (hmx, hmy)
                                if key not in g['wall_hp']:
                                    g['wall_hp'][key] = WALL_HP_BY_TYPE.get(wt, 8)
                                g['wall_hp'][key] -= 1
                                left = g['wall_hp'][key]
                                if left <= 0:
                                    del g['wall_hp'][key]
                                    g['wall_fall'][key] = 0.18  # start fall animation; removal deferred
                                    _ex, _ey = hmx + 0.5, hmy + 0.5
                                    g['wall_explosions'].append([_ex, _ey, 1.0])
                                    for _e in all_combatants:
                                        if _e.alive and math.hypot(_e.x - _ex, _e.y - _ey) < 2.0:
                                            if _e.hit():
                                                g['kills'] += 1
                                                if _e.is_boss: g['boss_kills'] += 1
                                                else: g['drom_kills'] += 1
                                            elif _e.alive and _e.hit():
                                                g['kills'] += 1
                                                if _e.is_boss: g['boss_kills'] += 1
                                                else: g['drom_kills'] += 1
                                    g['msg'] = '  WALL DESTROYED!  '; g['msg_t'] = 30
                                else:
                                    g['msg'] = f"  WALL: {left} HITS LEFT  "; g['msg_t'] = 15
                    else:
                        g['msg']='  NO AMMO! FIND A CRATE  '; g['msg_t']=40

                if reload_key and g['reload_anim'] <= 0:
                    needed = MAG_SIZE - g['ammo']
                    if needed <= 0:
                        g['msg'] = '  MAG ALREADY FULL  '; g['msg_t'] = 30
                    elif g['reserve'] <= 0:
                        g['msg'] = '  NO RESERVE AMMO  '; g['msg_t'] = 40
                    else:
                        g['reload_anim'] = RELOAD_TIME

                if g['reload_anim'] > 0:
                    g['reload_anim'] -= dt
                    if g['reload_anim'] <= 0:
                        g['reload_anim'] = 0.0
                        needed = MAG_SIZE - g['ammo']
                        take = min(needed, g['reserve'])
                        g['ammo']   += take
                        g['reserve'] -= take
                        g['msg'] = f"  RELOADED: {g['ammo']} IN MAG  "; g['msg_t'] = 40

                if g['sflash']>0: g['sflash']-=1
                if g['hit_flash']>0: g['hit_flash']-=1
                if g['msg_t']>0:  g['msg_t']-=1
                if g['dalpha']>0: g['dalpha']=max(0.0,g['dalpha']-2.5*dt)
                if g['gun_upgrade_anim']>0: g['gun_upgrade_anim']=max(0.0,g['gun_upgrade_anim']-dt)
                if g['boss_art_t']>0: g['boss_art_t']=max(0.0,g['boss_art_t']-dt)

                for e in g['enemies']:
                    dmg = e.update(dt, px, py, g['enemies'])
                    if dmg > 0:
                        g['hp'] -= dmg
                        g['dalpha'] = min(1.0, g['dalpha']+0.5)
                        if g['hp'] <= 0:
                            g['hp'] = 0; g['state'] = 'dead'

                # Boss spawn trigger: all regular enemies dead
                if not g['bosses_spawned'] and all(not e.alive for e in g['enemies']):
                    g['bosses'] = _make_bosses(g['boss_count'], id_offset=len(g['enemies']))
                    g['bosses_spawned'] = True
                    g['msg'] = '  WARNING: BOSS DROM INCOMING!  '; g['msg_t'] = 100
                    g['boss_art_t'] = 4.0

                for b in g['bosses']:
                    dmg = b.update(dt, px, py, all_combatants)
                    if b.alive or b.dying:
                        g['blood_trail'].add((int(b.x * 2), int(b.y * 2)))
                    if dmg > 0:
                        g['hp'] -= dmg
                        g['dalpha'] = min(1.0, g['dalpha']+0.5)
                        if g['hp'] <= 0:
                            g['hp'] = 0; g['state'] = 'dead'

                any_close = any(
                    math.hypot(e.x-px, e.y-py) < WARN_DIST
                    for e in all_combatants if e.alive
                )
                g['close_warn'] = 1.5 if any_close else 0.0

                for hp_pack in g['health_packs']:
                    if not hp_pack.active: continue
                    if math.hypot(hp_pack.x-px, hp_pack.y-py) < 0.8:
                        if g['hp'] >= 100.0:
                            g['msg'] = '  HEALTH ALREADY FULL  '; g['msg_t'] = 30
                        else:
                            heal = random.uniform(30, 50)
                            g['hp'] = min(100.0, g['hp'] + heal)
                            hp_pack.active = False
                            g['msg'] = f"  +{int(heal)}% HEALTH  "; g['msg_t'] = 50

                for ac in g['ammo_crates']:
                    if not ac.active: continue
                    if math.hypot(ac.x-px, ac.y-py) < 0.8:
                        total = g['ammo'] + g['reserve']
                        if total >= MAG_SIZE + MAX_RESERVE:
                            g['msg'] = '  AMMO ALREADY FULL  '; g['msg_t'] = 30
                        else:
                            ac.active = False
                            # Fill mag first, then reserve, hard-capped at MAX_RESERVE
                            needed = MAG_SIZE - g['ammo']
                            from_r  = min(needed, g['reserve'])
                            g['ammo']   += from_r
                            g['reserve'] -= from_r
                            space_in_res = MAX_RESERVE - g['reserve']
                            bonus = min(space_in_res, 16)
                            g['reserve'] += bonus
                            g['msg'] = f"  AMMO: {g['ammo']}+{g['reserve']}  "; g['msg_t'] = 50

                # Gun upgrade pickup - also fills magazine
                gu = g['gun_upgrade']
                if gu and gu.active and not g['gun_upgraded']:
                    if math.hypot(gu.x-px, gu.y-py) < 0.8:
                        gu.active = False
                        g['gun_upgraded'] = True
                        g['gun_upgrade_anim'] = 1.5
                        g['ammo'] = MAG_SIZE
                        g['msg'] = '  GUN UPGRADED! DOUBLE SHOT  '; g['msg_t'] = 80

                while WALL_BREAKS:
                    bwx, bwy = WALL_BREAKS.pop()
                    g['wall_explosions'].append([bwx, bwy, 1.0])
                    for _e in all_combatants:
                        if _e.alive and math.hypot(_e.x - bwx, _e.y - bwy) < 2.0:
                            if _e.hit():
                                g['kills'] += 1
                                if _e.is_boss: g['boss_kills'] += 1
                                else: g['drom_kills'] += 1
                            elif _e.alive and _e.hit():
                                g['kills'] += 1
                                if _e.is_boss: g['boss_kills'] += 1
                                else: g['drom_kills'] += 1

                g['wall_explosions'] = [
                    [wx, wy, t - dt] for wx, wy, t in g['wall_explosions'] if t - dt > 0
                ]

                for _wfk in list(g['wall_fall'].keys()):
                    g['wall_fall'][_wfk] -= dt
                    if g['wall_fall'][_wfk] <= 0:
                        _wmx, _wmy = _wfk
                        WORLD_MAP[_wmy][_wmx] = 0
                        del g['wall_fall'][_wfk]

                # Win delay countdown
                if g['win_delay_t'] > 0:
                    g['win_delay_t'] -= dt
                    secs = math.ceil(g['win_delay_t'])
                    if g['msg_t'] <= 0:
                        g['msg'] = f"  LEVEL CLEAR! NEXT IN {secs}...  "; g['msg_t'] = 5
                    if g['win_delay_t'] <= 0:
                        _commit_stats(g, stats)
                        if g['level'] >= 5:
                            stats['times_beat_5'] += 1; _save_stats(stats)
                        g['state'] = 'endgame' if g['level'] >= 5 else 'levelwin'

                # Ammo warning state
                if g['ammo'] == 0 and g['reserve'] == 0:
                    g['ammo_warn'] = 'no_ammo'
                elif g['ammo'] == 0 and g['reload_anim'] <= 0:
                    g['ammo_warn'] = 'reload'
                else:
                    g['ammo_warn'] = ''

                fps_acc+=dt; fps_cnt+=1
                if fps_acc>=0.5: fps_val=int(fps_cnt/fps_acc); fps_acc=fps_cnt=0

                fs=build_frame(cols,rows,px,py,angle,g['enemies']+g['bosses'],
                               g['hp'],g['kills'],g['sflash'],g['dalpha'],
                               g['msg'],g['msg_t'],fps_val,g['close_warn'],
                               g['level'],g['total_enemies'],
                               g['health_packs'],g['ammo_crates'],
                               g['ammo'],g['reserve'],g['reload_anim'],
                               g['ammo_warn'],g['hit_flash'],
                               g['gun_upgrade'],g['gun_upgraded'],
                               g['wall_explosions'],g['gun_upgrade_anim'],
                               g['wall_hp'],g['win_delay_t'],
                               wall_fall=g['wall_fall'],
                               boss_art_t=g['boss_art_t'],
                               cheats_on=_input_mod.CHEATS_ENABLED,
                               blood_trail=g['blood_trail'])

            # LEVEL WIN
            elif state=='levelwin':
                fs=build_level_screen(cols,rows,g['level'],
                                      next_enemy_count=_enemies_for_level(g['level']+1))
                if shoot:
                    next_level = g['level'] + 1
                    if next_level > 5:
                        g['state'] = 'endgame'
                    else:
                        g = new_game(next_level)
                        g['state'] = 'play'

            # CAMPAIGN COMPLETE — shown after level 5
            elif state=='endgame':
                fs=build_endgame_menu(cols, rows)
                if shoot:                      # SPACE → main menu
                    g = new_game(1); g['state'] = 'splash'
                elif 'w' in ks:               # W → infinite levels
                    g = new_game(g['level'] + 1)
                    g['state'] = 'play'

            # DEAD
            elif state=='dead':
                fs=build_end(cols,rows,
                             TEXT['dead_title'], TEXT['dead_subtitle'],
                             TEXT['dead_prompt'], g['kills'], False)
                if shoot:
                    _commit_stats(g, stats)
                    g=new_game(1); g['state']='splash'
            else:
                fs=""

            _wcon(fs)

            elapsed=time.perf_counter()-now
            st=max(0.0,1/30-elapsed)
            if st: time.sleep(st)

    finally:
        _wcon(SHOW_CUR+NORM_SCR+RESET_ALL)
        kernel32.CloseHandle(CONOUT)