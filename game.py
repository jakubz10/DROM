import math, time, random
from console import _wcon, _term_size, ALT_SCR, HIDE_CUR, CLEAR_SCR, SHOW_CUR, NORM_SCR, RESET_ALL
from console import kernel32, CONOUT
from input import poll_input
from map_data import WORLD_MAP, MAP_H, MAP_W
from raycaster import cast_ray
from enemy import Enemy
from pickups import _make_health_packs, _make_ammo_crates
from renderer import build_frame, build_splash, build_end, build_level_screen
from text import TEXT


def _enemies_for_level(level):
    """Level 1=8, level 2=12, level 3=16, ... (+4 each level)."""
    return 8 + (level - 1) * 4


def _make_enemies(count):
    """Spawn `count` enemies at random free positions across the map."""
    free = [(x+0.5, y+0.5)
            for y in range(1, MAP_H-1)
            for x in range(1, MAP_W-1)
            if WORLD_MAP[y][x] == 0]
    # Keep away from player start (2.5, 2.5)
    free = [(x,y) for x,y in free if math.hypot(x-2.5, y-2.5) > 5.0]
    random.shuffle(free)
    spawns = free[:count]
    return [Enemy(x, y, i) for i, (x, y) in enumerate(spawns)]


def new_game(level=1):
    count = _enemies_for_level(level)
    return dict(px=2.5, py=2.5, angle=0.0, hp=100.0, kills=0,
                enemies=_make_enemies(count),
                total_enemies=count, level=level,
                health_packs=_make_health_packs(5),
                ammo_crates=_make_ammo_crates(4),
                ammo=16, reserve=32,   # mag=16, reserve max=32, total max=48
                reload_anim=0.0,
                ammo_warn='',
                hit_flash=0,
                sflash=0, dalpha=0.0, msg='', msg_t=0,
                state='splash', close_warn=0.0)


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
            ks, shoot, flip, reload_key, quit_now = poll_input()
            if quit_now: break

            state=g['state']

            # SPLASH
            if state=='splash':
                fs=build_splash(cols,rows)
                if shoot: g=new_game(1); g['state']='play'

            # PLAY
            elif state=='play':
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
                        wd,_,_=cast_ray(px,py,angle)
                        be=None; bd=wd
                        for e in g['enemies']:
                            if not e.alive: continue
                            ex,ey=e.x-px,e.y-py; ed=math.hypot(ex,ey)
                            ea=math.atan2(ey,ex)-angle
                            ea=(ea+math.pi)%(2*math.pi)-math.pi
                            if abs(ea)<0.18 and ed<bd: be=e; bd=ed
                        if be:
                            died = be.hit()
                            if died:
                                g['kills']+=1
                                g['msg']=TEXT['msg_kill']; g['msg_t']=55
                                if all(not e.alive for e in g['enemies']): g['state']='levelwin'
                            else:
                                g['msg']=TEXT['msg_hit']; g['msg_t']=20
                            g['hit_flash'] = 8   # red crosshair on any hit
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

                # Enemy AI - new state machine
                for e in g['enemies']:
                    dmg = e.update(dt, px, py, g['enemies'])
                    if dmg > 0:
                        g['hp'] -= dmg
                        g['dalpha'] = min(1.0, g['dalpha']+0.5)
                        if g['hp'] <= 0:
                            g['hp'] = 0; g['state'] = 'dead'

                # Close-enemy warning
                WARN_DIST = 2.8
                any_close = any(
                    math.hypot(e.x-px, e.y-py) < WARN_DIST
                    for e in g['enemies'] if e.alive
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

                # Ammo warning state
                if g['ammo'] == 0 and g['reserve'] == 0:
                    g['ammo_warn'] = 'no_ammo'
                elif g['ammo'] == 0 and g['reload_anim'] <= 0:
                    g['ammo_warn'] = 'reload'
                else:
                    g['ammo_warn'] = ''

                fps_acc+=dt; fps_cnt+=1
                if fps_acc>=0.5: fps_val=int(fps_cnt/fps_acc); fps_acc=fps_cnt=0

                fs=build_frame(cols,rows,px,py,angle,g['enemies'],
                               g['hp'],g['kills'],g['sflash'],g['dalpha'],
                               g['msg'],g['msg_t'],fps_val,g['close_warn'],
                               g['level'],g['total_enemies'],
                               g['health_packs'],g['ammo_crates'],
                               g['ammo'],g['reserve'],g['reload_anim'],
                               g['ammo_warn'],g['hit_flash'])

            # LEVEL WIN
            elif state=='levelwin':
                fs=build_level_screen(cols,rows,g['level'],g['kills'],
                                      next_enemy_count=_enemies_for_level(g['level']+1))
                if shoot:
                    next_level = g['level'] + 1
                    g = new_game(next_level)
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
