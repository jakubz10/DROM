import ctypes, os
from ctypes import wintypes

# Win32 setup
kernel32 = ctypes.windll.kernel32
user32   = ctypes.windll.user32

# Open real console output handle (works with py.exe / any launcher)
CONOUT = kernel32.CreateFileW(
    "CONOUT$",
    0xC0000000,          # GENERIC_READ | GENERIC_WRITE
    0x3,                 # FILE_SHARE_READ | FILE_SHARE_WRITE
    None, 3, 0, None     # OPEN_EXISTING
)

# Enable VT processing
kernel32.SetConsoleMode(CONOUT,
    0x0001 |   # ENABLE_PROCESSED_OUTPUT
    0x0002 |   # ENABLE_WRAP_AT_EOL_OUTPUT
    0x0004     # ENABLE_VIRTUAL_TERMINAL_PROCESSING
)

# WriteConsoleW straight to CONOUT$ – bypasses all stdout encoding
_wn = ctypes.c_ulong(0)
def _wcon(s: str):
    if s: kernel32.WriteConsoleW(CONOUT, s, len(s), ctypes.byref(_wn), None)

def _term_size():
    try:    c, r = os.get_terminal_size(); return c, r
    except: return 120, 40

# ANSI helpers
def _goto(x, y): return f"\x1b[{y+1};{x+1}H"
_fg_cache: dict = {}
_bg_cache: dict = {}
def _fg(r,g,b):
    k=(r,g,b); v=_fg_cache.get(k)
    if v is None: v=_fg_cache[k]=f"\x1b[38;2;{r};{g};{b}m"
    return v
def _bg(r,g,b):
    k=(r,g,b); v=_bg_cache.get(k)
    if v is None: v=_bg_cache[k]=f"\x1b[48;2;{r};{g};{b}m"
    return v

HIDE_CUR  = "\x1b[?25l"
SHOW_CUR  = "\x1b[?25h"
ALT_SCR   = "\x1b[?1049h"
NORM_SCR  = "\x1b[?1049l"
CLEAR_SCR = "\x1b[2J"
RESET_ALL = "\x1b[0m"
HOME      = "\x1b[H"
