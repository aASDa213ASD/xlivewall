#!/usr/bin/env python3
"""
Live-loop a video (or random pick from a folder) as the XOrg desktop background using mpv IPC.
Ensures single-instance behavior: new launches replace the video in the running instance.
Optimized for suckless/dwm environments with compact, PEP8-compliant code.

Clears any existing video filters on each continuous launch before applying new ones.
"""

import argparse
import json
import logging
import random
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from Xlib import X, display, Xatom, XK

# Supported video extensions for folder mode
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv'}
# Fixed IPC socket path for single-instance control
IPC_PATH = Path('/tmp/mpv-background.sock')

# Configure structured logging
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def send_ipc(ipc: Path, cmd: Dict[str, Any]) -> None:
    """Send JSON IPC commands to mpv, logging on failure."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(str(ipc))
            s.sendall((json.dumps(cmd) + '\n').encode())
    except (OSError, TypeError) as e:
        logger.error('IPC error: %s', e)

def wait_socket(ipc: Path, timeout: float = 5.0) -> bool:
    """Wait up to `timeout` seconds for the mpv IPC socket to accept connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                s.connect(str(ipc))
                return True
        except (FileNotFoundError, ConnectionRefusedError, OSError):
            time.sleep(0.1)
    return False

def pick_video(cmd_args: List[str]) -> str:
    """Resolve a file or random pick from a folder if the second arg is a directory.
    Updates cmd_args in-place when a folder was provided."""
    if len(cmd_args) > 1:
        pot = Path(cmd_args[1])
        if pot.is_dir():
            vids = [str(f) for f in pot.iterdir()
                    if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS]
            if not vids:
                logger.error('No video files found in %s', pot)
                sys.exit(1)
            choice = random.choice(vids)
            logger.info('Random video selected: %s', choice)
            cmd_args[1] = choice
            return choice
    for arg in cmd_args:
        if not arg.startswith('-'):
            return arg
    logger.error('No video file specified')
    sys.exit(1)

def build_cmd(args: List[str], wid: str, ipc: Path) -> List[str]:
    """Construct mpv command with defaults, replacing 'WID' placeholder."""
    base = [arg.replace('WID', wid) for arg in args]
    defaults = {
        '--wid': wid,
        '--loop': None,
        '--no-osc': None,
        '--hwdec': 'auto',
        '--cache': 'yes',
        '--cache-secs': '60',
        '--volume': '0',
        '--input-ipc-server': str(ipc),
        '--no-input-default-bindings': None,
    }
    for k, v in defaults.items():
        if not any(a.startswith(k) for a in base):
            base.append(k if v is None else f'{k}={v}')
    return base

def create_window(d: display.Display):
    """Create a full-screen desktop window below all others."""
    scr = d.screen()
    root = scr.root
    win = root.create_window(
        0, 0, scr.width_in_pixels, scr.height_in_pixels, 0,
        scr.root_depth, X.InputOutput, X.CopyFromParent,
        background_pixel=0,
        event_mask=X.ExposureMask | X.StructureNotifyMask | X.KeyPressMask,
    )
    win.change_attributes(override_redirect=True)
    atoms = (d.intern_atom('_NET_WM_WINDOW_TYPE'),
             d.intern_atom('_NET_WM_WINDOW_TYPE_DESKTOP'))
    win.change_property(atoms[0], Xatom.ATOM, 32, [atoms[1]])
    win.map()
    d.sync()
    win.configure(stack_mode=X.Below)
    logger.info('Window id: 0x%x', win.id)
    return win

def main():
    """Parse args, enforce single-instance, handle video selection and filter flags."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('cmd', nargs=argparse.REMAINDER,
                   help='mpv args; use "WID" for window ID; second arg may be a folder')
    p.add_argument('--socket-timeout', '-t', type=float, default=5.0,
                   help='timeout in seconds for mpv IPC socket readiness')
    opts = p.parse_args()

    if not opts.cmd:
        p.error('Provide mpv invocation, e.g., "mpv video.mp4" or "mpv /path/to/videos/"')

    video = pick_video(opts.cmd)

    # Detect existing instance
    if wait_socket(IPC_PATH, timeout=0.1):
        logger.info('Existing instance detected; loading %s', video)
        # clear any existing filters
        send_ipc(IPC_PATH, {'command': ['vf', 'clear']})
        # replace the video file
        send_ipc(IPC_PATH, {'command': ['loadfile', video, 'replace']})
        # reapply only the new --vf filters
        for arg in opts.cmd:
            if arg.startswith('--vf='):
                spec = arg.split('=', 1)[1]
                send_ipc(IPC_PATH, {'command': ['vf', 'set', spec]})
        return

    # No running instance; start a new one
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda s, f: sys.exit(0))

    d = display.Display()
    win = create_window(d)
    wid = f'0x{win.id:x}'
    cmd = build_cmd(opts.cmd, wid, IPC_PATH)
    logger.info('Executing: %s', cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             stdin=subprocess.DEVNULL)

    if not wait_socket(IPC_PATH, opts.socket_timeout):
        proc.terminate()
        sys.exit(1)

    vol, step = 0, 5
    try:
        while proc.poll() is None:
            ev = d.next_event()
            if ev.type != X.KeyPress:
                continue
            key = d.keycode_to_keysym(ev.detail, 0)
            if key == XK.XK_Up:
                vol = min(100, vol + step)
            elif key == XK.XK_Down:
                vol = max(0, vol - step)
            else:
                continue
            logger.info('Volume: %d%%', vol)
            send_ipc(IPC_PATH, {'command': ['set_property', 'volume', vol]})
    finally:
        proc.terminate()
        d.close()
        logger.info('Exited cleanly.')

if __name__ == '__main__':
    main()
