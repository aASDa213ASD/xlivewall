#!/usr/bin/env python3
import sys
import subprocess
import time
import json
import socket
from Xlib import X, display, Xatom, XK

def send_ipc_command(ipc_path, command):
    """Send a JSON command to the mpv IPC socket."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(ipc_path)
            client.sendall((json.dumps(command) + "\n").encode('utf-8'))
    except Exception as e:
        print("[ERROR] Failed to send IPC command:", e)

def main():
    if len(sys.argv) < 2:
        print("Usage: {} COMMAND [ARGS...]".format(sys.argv[0]))
        print("\nRequired Arguments:")
        print("  COMMAND: The external command to execute (e.g., mpv)")
        print("  ARGS: Optional arguments for the command.")
        print("        Any occurrence of 'WID' in the arguments will be replaced by the window ID (in hexadecimal) of the created desktop window.")
        sys.exit(1)

    # Open X display and get the root window
    d = display.Display()
    screen = d.screen()
    root = screen.root
    width = screen.width_in_pixels
    height = screen.height_in_pixels
    print("[INFO] Screen dimensions: {}x{}".format(width, height))

    # Create a full-screen window with override_redirect so that the window manager doesn't interfere
    win = root.create_window(
        0, 0, width, height, 0,
        screen.root_depth,
        X.InputOutput,
        X.CopyFromParent,
        background_pixel=0,
        event_mask=(X.ExposureMask | X.StructureNotifyMask | X.KeyPressMask)
    )
    win.change_attributes(override_redirect=True)

    # Set window type to DESKTOP so that it's treated as a background window
    NET_WM_WINDOW_TYPE = d.intern_atom("_NET_WM_WINDOW_TYPE")
    NET_WM_WINDOW_TYPE_DESKTOP = d.intern_atom("_NET_WM_WINDOW_TYPE_DESKTOP")
    win.change_property(NET_WM_WINDOW_TYPE, Xatom.ATOM, 32, [NET_WM_WINDOW_TYPE_DESKTOP])
    
    # Map and lower the window (send it to the bottom)
    win.map()
    d.sync()
    win.configure(stack_mode=X.Below)
    print("[INFO] Created desktop window with id: 0x{:x}".format(win.id))
    
    # Prepare IPC socket path for mpv; we embed the window id to make it unique.
    ipc_path = f"/tmp/mpv-ipc-0x{win.id:x}.sock"
    
    # Prepare the command: replace any occurrence of "WID" with our window ID in hex.
    win_id_hex = "0x{:x}".format(win.id)
    cmd = [arg.replace("WID", win_id_hex) for arg in sys.argv[1:]]
    
    # Automatically insert the --wid flag if not provided.
    if not any("--wid" in arg for arg in cmd):
        cmd.append(f"--wid={win_id_hex}")
    
    # Default to --loop if no loop flag is provided.
    if not any("--loop" in arg for arg in cmd):
        cmd.append("--loop")
    
    # Append other default flags if not already provided:
    # - Hide on-screen controls
    if not any("--no-osc" in arg for arg in cmd):
        cmd.append("--no-osc")
    # - Enable hardware decoding
    if not any("--hwdec" in arg for arg in cmd):
        cmd.append("--hwdec=auto")
    # - Enable caching and set cache seconds for long videos
    if not any("--cache=yes" in arg for arg in cmd):
        cmd.append("--cache=yes")
    if not any("--cache-secs" in arg for arg in cmd):
        cmd.append("--cache-secs=60")
    # - Set initial volume to 0
    if not any("--volume=" in arg for arg in cmd):
        cmd.append("--volume=0")
    # - Provide the IPC socket path for volume control
    if not any("--input-ipc-server" in arg for arg in cmd):
        cmd.append(f"--input-ipc-server={ipc_path}")
    
    print("[INFO] Executing command:", cmd)
    
    # Launch the external command (e.g., mpv)
    proc = subprocess.Popen(cmd)
    
    # Wait a moment for mpv to create the IPC socket
    timeout = 5  # seconds
    waited = 0
    while waited < timeout:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(ipc_path)
            print("[INFO] Connected to mpv IPC socket.")
            break
        except Exception:
            time.sleep(0.1)
            waited += 0.1
    else:
        print("[WARNING] Could not connect to mpv IPC socket.")

    # Set up a default volume level starting at 0
    current_volume = 0
    volume_step = 5

    # Enter an event loop to keep the window alive while the external process is running
    try:
        while proc.poll() is None:
            event = d.next_event()  # blocking; process events if needed
            if event.type == X.KeyPress:
                keysym = d.keycode_to_keysym(event.detail, 0)
                if keysym == XK.XK_Up:
                    current_volume += volume_step
                    print("[INFO] Increasing volume to", current_volume)
                    send_ipc_command(ipc_path, {"command": ["set_property", "volume", current_volume]})
                elif keysym == XK.XK_Down:
                    current_volume = max(0, current_volume - volume_step)
                    print("[INFO] Decreasing volume to", current_volume)
                    send_ipc_command(ipc_path, {"command": ["set_property", "volume", current_volume]})
    except KeyboardInterrupt:
        proc.terminate()
        print("[INFO] Terminated by user")
    
    win.destroy()
    d.flush()
    d.close()
    print("[INFO] Exiting.")

if __name__ == "__main__":
    main()

