import math, time, random
from console import _wcon, _term_size, ALT_SCR, HIDE_CUR, CLEAR_SCR, SHOW_CUR, NORM_SCR, RESET_ALL
from console import kernel32, CONOUT
from input import poll_input
from map_data import WORLD_MAP, load_map, WALL_BREAKS
from raycaster import cast_ray
from enemy import Enemy, Boss
from pickups import _make_health_packs, _make_ammo_crates, _make_gun_upgrade
from renderer import build_frame, build_splash, build_end, build_level_screen, build_endgame_menu
from text import TEXT


def _enemies_for_level(level):
    """Level 1=8, level 2=12, level 3=16, ... (+4 each level)."""
    return 8 + (level - 1) * 4


def _bosses_for_level(level):
    """1 boss on levels 1-2, 2 bosses on level 3+."""
    return 1 if level <= 2 else 2


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
                ammo_crates=_make_ammo_crates(4),
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
                wall_hp={}, wall_explosions=[])


def main():
    _wcon(ALT_SCR + HIDE_CUR + CLEAR_SCR)

    cols,rows = _term_size()
    MOVE_SPEED=3.8; ROT_SPEED=2.5
    g=new_game()
    last_t=time.perf_counter()
    fps_acc=fps_cnt=fps_val=frame=0

    try:
        while True:
            now=time.perf_counter(); dt=min(now-last_t,0.05); last_t=now
            if frame%60==0:
                nc,nr=_term_size()
                if nc!=cols or nr!=rows:
                    cols,rows=nc,nr; _wcon(CLEAR_SCR)
            frame+=1

            # Poll all input this frame
            ks, shoot, flip, reload_key, quit_now, cheat_l5, killall = poll_input()
            if quit_now: break

            state=g['state']

            # SPLASH
            if state=='splash':
                fs=build_splash(cols,rows)
                if shoot: g=new_game(1); g['state']='play'
                elif cheat_l5: g=new_game(5); g['state']='play'

            # PLAY
            elif state=='play':
                # DEV: Y = kill all enemies instantly
                if killall:
                    for _e in g['enemies'] + g['bosses']:
                        if _e.alive:
                            _e.alive = False; _e.dying = True
                            _e.death_t = 1.8 if _e.is_boss else 1.0
                            _e.pain_t  = 0.9 if _e.is_boss else 0.5
                            g['kills'] += 1
                    g['msg'] = '  [DEV] ALL DROMS KILLED  '; g['msg_t'] = 60

                px,py,angle=g['px'],g['py'],g['angle']

                # Rotate: Q/E keys and arrow keys; UP/DOWN = 180 deg flip
                turn = 0.0
                if 'left'  in ks: turn -= ROT_SPEED*dt
                if 'right' in ks: turn += ROT_SPEED*dt
                if flip: turn += math.pi
                angle += turn

                # Move
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

                # Shoot (blocked during reload animation)
                if shoot:
                    if g['reload_anim'] > 0:
                        g['msg'] = '  RELOADING...  '; g['msg_t'] = 20
                    elif g['ammo'] > 0:
                        g['ammo'] -= 1
                        g['sflash']=8
                        shots = [angle] if not g['gun_upgraded'] else [angle-0.05, angle+0.05]
                        for sa in shots:
                            wd, _, wt = cast_ray(px, py, sa)
                            be=None; bd=wd
                            all_combatants = g['enemies'] + g['bosses']
                            for e in all_combatants:
                                if not e.alive: continue
                                ex,ey=e.x-px,e.y-py; ed=math.hypot(ex,ey)
                                ea=math.atan2(ey,ex)-sa
                                ea=(ea+math.pi)%(2*math.pi)-math.pi
                                if abs(ea)<0.18 and ed<bd: be=e; bd=ed
                            if be:
                                died=be.hit()
                                if died:
                                    g['kills']+=1
                                    if be.is_boss:
                                        g['msg']=TEXT['msg_boss_kill']; g['msg_t']=80
                                    else:
                                        g['msg']=TEXT['msg_kill']; g['msg_t']=55
                                    # Win check: all regular enemies dead + all bosses dead
                                    reg_clear  = all(not e.alive for e in g['enemies'])
                                    boss_clear = all(not b.alive for b in g['bosses'])
                                    if reg_clear and boss_clear and g['bosses_spawned'] and g['win_delay_t'] <= 0:
                                        g['win_delay_t'] = 3.0
                                        g['msg'] = '  LEVEL CLEAR!  '; g['msg_t'] = 180
                                else:
                                    g['msg']=TEXT['msg_hit']; g['msg_t']=20
                                g['hit_flash']=8
                            elif wt and 1 <= wt <= 4 and wd < 99.0:
                                # Player can destroy type 1-4 walls (8 shots)
                                WALL_SHOTS = 8
                                hmx = int(px + math.cos(sa) * (wd + 0.01))
                                hmy = int(py + math.sin(sa) * (wd + 0.01))
                                key = (hmx, hmy)
                                if key not in g['wall_hp']:
                                    g['wall_hp'][key] = WALL_SHOTS
                                g['wall_hp'][key] -= 1
                                left = g['wall_hp'][key]
                                if left <= 0:
                                    del g['wall_hp'][key]
                                    WORLD_MAP[hmy][hmx] = 0
                                    _ex, _ey = hmx + 0.5, hmy + 0.5
                                    g['wall_explosions'].append([_ex, _ey, 1.0])
                                    for _e in g['enemies'] + g['bosses']:
                                        if _e.alive and math.hypot(_e.x - _ex, _e.y - _ey) < 2.0:
                                            if _e.hit(): g['kills'] += 1
                                            elif _e.alive and _e.hit(): g['kills'] += 1
                                    g['msg'] = '  WALL DESTROYED!  '; g['msg_t'] = 30
                                else:
                                    g['msg'] = f"  WALL: {left} HITS LEFT  "; g['msg_t'] = 15
                    else:
                        g['msg']='  NO AMMO! FIND A CRATE  '; g['msg_t']=40

                # Reload with R (1.2s animation, completes on finish)
                RELOAD_TIME = 1.2
                MAG_SIZE    = 16
                if reload_key and g['reload_anim'] <= 0:
                    needed = MAG_SIZE - g['ammo']
                    if needed <= 0:
                        g['msg'] = '  MAG ALREADY FULL  '; g['msg_t'] = 30
                    elif g['reserve'] <= 0:
                        g['msg'] = '  NO RESERVE AMMO  '; g['msg_t'] = 40
                    else:
                        g['reload_anim'] = RELOAD_TIME

                # Tick reload animation; apply ammo on completion
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

                # Enemy AI - new state machine
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

                # Boss AI
                for b in g['bosses']:
                    all_c = g['enemies'] + g['bosses']
                    dmg = b.update(dt, px, py, all_c)
                    if dmg > 0:
                        g['hp'] -= dmg
                        g['dalpha'] = min(1.0, g['dalpha']+0.5)
                        if g['hp'] <= 0:
                            g['hp'] = 0; g['state'] = 'dead'

                # Close-enemy warning
                WARN_DIST = 2.8
                any_close = any(
                    math.hypot(e.x-px, e.y-py) < WARN_DIST
                    for e in (g['enemies'] + g['bosses']) if e.alive
                )
                g['close_warn'] = 1.5 if any_close else 0.0

                # Health pack pickup - blocked when HP is full
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

                # Ammo crate pickup - blocked when ammo is at max (16 mag + 32 reserve = 48)
                MAX_RESERVE = 32
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

                # Drain boss wall-break events into game explosion list
                while WALL_BREAKS:
                    bwx, bwy = WALL_BREAKS.pop()
                    g['wall_explosions'].append([bwx, bwy, 1.0])
                    for _e in g['enemies'] + g['bosses']:
                        if _e.alive and math.hypot(_e.x - bwx, _e.y - bwy) < 2.0:
                            if _e.hit(): g['kills'] += 1
                            elif _e.alive and _e.hit(): g['kills'] += 1

                # Tick wall explosions
                g['wall_explosions'] = [
                    [wx, wy, t - dt] for wx, wy, t in g['wall_explosions'] if t - dt > 0
                ]

                # Win delay countdown
                if g['win_delay_t'] > 0:
                    g['win_delay_t'] -= dt
                    secs = math.ceil(g['win_delay_t'])
                    if g['msg_t'] <= 0:
                        g['msg'] = f"  LEVEL CLEAR! NEXT IN {secs}...  "; g['msg_t'] = 5
                    if g['win_delay_t'] <= 0:
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
                               g['wall_hp'],g['win_delay_t'])

            # LEVEL WIN
            elif state=='levelwin':
                fs=build_level_screen(cols,rows,g['level'],g['kills'],
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
                if shoot: g=new_game(1); g['state']='splash'
            else:
                fs=""

            _wcon(fs)

            elapsed=time.perf_counter()-now
            st=max(0.0,1/30-elapsed)
            if st: time.sleep(st)

    finally:
        _wcon(SHOW_CUR+NORM_SCR+RESET_ALL)
        kernel32.CloseHandle(CONOUT)
