import ctypes
from console import user32

# Virtual key codes
VK_W     = 0x57; VK_S = 0x53; VK_A = 0x41; VK_D = 0x44
VK_Q     = 0x51; VK_E = 0x45; VK_R = 0x52; VK_U = 0x55; VK_Y = 0x59
VK_T     = 0x54; VK_I = 0x49; VK_Z = 0x5A; VK_X = 0x58
#cheats:
#t - upgrades and fills gun with ammo
#i - heals you fully
#y - kills all droms
#u - skips to 5th level

CHEATS_ENABLED = False
VK_LEFT  = 0x25; VK_RIGHT = 0x27
VK_UP    = 0x26; VK_DOWN  = 0x28
VK_SPACE = 0x20
VK_ESC   = 0x1B; VK_BACK = 0x08

_prev_space  = False
_prev_flip   = False
_prev_reload = False
_prev_esc    = False
_prev_save   = False
_prev_toggle = False
_prev_cheat   = False
_prev_killall = False
_prev_ammo_up = False
_prev_heal    = False

def poll_input():
    """
    Returns (keys_set, shoot_now, quit_now).
    Turn left:  Q or LEFT arrow
    Turn right: E or RIGHT arrow
    Move fwd:   W or UP arrow
    Move back:  S or DOWN arrow
    Strafe:     A / D
    Turn:       Q/E or LEFT/RIGHT arrows
    180 deg flip:  UP or DOWN arrow
    Shoot:      SPACE
    Quit:       ESC or BACKSPACE
    """
    global _prev_space, _prev_flip, _prev_reload, _prev_esc, _prev_save, _prev_toggle, _prev_cheat, _prev_killall, _prev_ammo_up, _prev_heal

    def down(vk):
        return bool(user32.GetAsyncKeyState(vk) & 0x8000)

    keys = set()
    if down(VK_W):   keys.add('w')
    if down(VK_S):   keys.add('s')
    if down(VK_A):   keys.add('sl')
    if down(VK_D):   keys.add('sr')
    if down(VK_Q) or down(VK_LEFT):  keys.add('left')
    if down(VK_E) or down(VK_RIGHT): keys.add('right')

    sp_now      = down(VK_SPACE)
    shoot       = sp_now and not _prev_space
    _prev_space = sp_now

    flip_now  = down(VK_UP) or down(VK_DOWN)
    flip      = flip_now and not _prev_flip
    _prev_flip = flip_now

    rl_now       = down(VK_R)
    reload_key   = rl_now and not _prev_reload
    _prev_reload = rl_now

    esc_now    = down(VK_ESC) or down(VK_BACK)
    quit_now   = esc_now and not _prev_esc
    _prev_esc  = esc_now

    sv_now     = down(VK_Z)
    save_key   = sv_now and not _prev_save
    _prev_save = sv_now

    tg_now       = down(VK_X)
    toggle_key   = tg_now and not _prev_toggle
    _prev_toggle = tg_now

    # Cheats: U=level5  Y=killall  T=gun+ammo  I=heal  (toggle: CHEATS_ENABLED at top)
    cheat_l5 = killall = cheat_ammo_up = cheat_heal = False
    if CHEATS_ENABLED:
        ch_now        = down(VK_U)
        cheat_l5      = ch_now and not _prev_cheat
        _prev_cheat   = ch_now
        ka_now        = down(VK_Y)
        killall       = ka_now and not _prev_killall
        _prev_killall = ka_now
        au_now        = down(VK_T)
        cheat_ammo_up = au_now and not _prev_ammo_up
        _prev_ammo_up = au_now
        hl_now        = down(VK_I)
        cheat_heal    = hl_now and not _prev_heal
        _prev_heal    = hl_now

    return keys, shoot, flip, reload_key, quit_now, cheat_l5, killall, cheat_ammo_up, cheat_heal, save_key, toggle_key
