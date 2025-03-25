#!/usr/bin/env python3
from Xlib import X, display, Xatom
import sys
import subprocess

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
        event_mask=(X.ExposureMask | X.StructureNotifyMask)
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
    
    # (Optional) set opacity if desired
    # For example, to set 80% opacity:
    # opacity = int(0.8 * 0xFFFFFFFF)
    # NET_WM_WINDOW_OPACITY = d.intern_atom("_NET_WM_WINDOW_OPACITY")
    # win.change_property(NET_WM_WINDOW_OPACITY, Xatom.CARDINAL, 32, [opacity])

    # Prepare the command: replace any occurrence of "WID" in the arguments with our window ID in hex
    win_id_hex = "0x{:x}".format(win.id)
    cmd = [arg.replace("WID", win_id_hex) for arg in sys.argv[1:]]
    print("[INFO] Executing command:", cmd)
    
    # Launch the external command (for example, a video player that accepts a window ID)
    proc = subprocess.Popen(cmd)
    
    # Enter an event loop to keep the window alive while the external process is running
    try:
        while proc.poll() is None:
            event = d.next_event()  # blocking; process events if needed
            # (For debugging, you could print events here)
    except KeyboardInterrupt:
        proc.terminate()
        print("[INFO] Terminated by user")
    
    win.destroy()
    d.flush()
    d.close()
    print("[INFO] Exiting.")

if __name__ == "__main__":
    main()

