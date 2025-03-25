# xLiveWall | Video Background for Xorg

xLiveWall is a Python application that creates a dedicated desktop window in your Xorg session and launches an external command (such as a video player) with the window ID (WID) automatically embedded into its arguments. This allows you to seamlessly display video backgrounds behind your desktop icons.

## Features

- **Desktop Window Creation:**  
  Creates a full-screen, override_redirect window so that your window manager does not interfere. The window is set as a DESKTOP type, making it ideal for use as a background.

- **Automatic WID Injection:**  
  The script automatically retrieves the created window's ID and replaces any occurrence of the string `WID` in your command arguments with this hexadecimal window ID. If you do not explicitly supply a `--wid` flag, it automatically appends one.

- **Default Looping:**  
  If no looping option (`--loop`) is provided, the script automatically adds it—ensuring that your video repeats continuously.

- **Built-in Default Flags for mpv:**  
  When using mpv, xLiveWall automatically appends several default flags if they are not already provided:
  - `--no-osc`: Hides on-screen controls.
  - `--hwdec=auto`: Enables hardware decoding.
  - `--cache=yes` and `--cache-secs=60`: Activates caching with a 60-second buffer, making it ideal for long videos.
  - `--volume=0`: Sets the initial volume to 0.
  - `--input-ipc-server=<ipc_path>`: Establishes an IPC socket for volume control via key bindings.

- **Runtime Volume Control:**  
  The script listens for Up/Down key presses and adjusts the volume in mpv accordingly through its IPC interface.

## Prerequisites

- **Python 3:**  
  Ensure that Python 3 is installed on your system.

- **python3-xlib:**  
  The script depends on the `python3-xlib` package for interacting with the X server.  
  On Debian/Ubuntu systems, install it with:  
  ```bash
  sudo apt-get update
  sudo apt-get install python3-xlib
  ```

- **Xorg Environment:**  
  xLiveWall is designed for use in an Xorg session.

- **External Video Player:**  
  Any external command that accepts a window ID (for example, mpv). When using mpv to stream online videos (e.g., YouTube), ensure that your PATH or mpv’s downloader configuration (like `--ytdl-path`) is set correctly.

## Installation

1. **Install Python 3:**  
   Download Python 3 from the [official website](https://www.python.org/downloads/) or use your distribution’s package manager.

2. **Install python3-xlib:**  
   Refer to the Prerequisites section above.

3. **Download xLiveWall:**  
   Clone or download the repository containing `xlivewall.py` and make it executable:
   ```bash
   chmod +x xlivewall.py
   ```

## Usage

The script requires at least one argument—the command to be executed with its arguments. The string `WID` in any argument is automatically replaced with the actual window ID (in hexadecimal) of the created desktop window.

### Basic Command Format

```bash
./xlivewall.py COMMAND [ARGS...]
```

### Example Usage

To use mpv for displaying a local video as your background (with auto-injected `--wid` and default looping), run:

```bash
./xlivewall.py mpv '/path/to/video.mp4'
```

For a YouTube video—ensure that mpv can access your downloader (e.g., yt-dlp). You might need to set your PATH or specify the downloader's full path:
  
```bash
./xlivewall.py mpv --ytdl-path=/home/zach/.asdf/installs/python/3.11.11/bin/yt-dlp 'https://www.youtube.com/watch?v=example'
```

*Note:* The script will automatically add `--wid=<window_id>`, `--loop`, and the other default flags (such as `--no-osc`, `--hwdec=auto`, caching options, `--volume=0`, and `--input-ipc-server=<ipc_path>`) if they are not already included in your command.

## How It Works

1. **Window Creation & WID Injection:**  
   - Connects to the X server and retrieves the screen dimensions.
   - Creates a full-screen window with the `override_redirect` attribute to avoid window manager interference.
   - Configures the window as a DESKTOP type.
   - Replaces any occurrence of `WID` in your command with the hexadecimal window ID.
   - Automatically appends `--wid=<window_id>` if it isn’t already provided.

2. **Default mpv Options:**  
   - If no looping option (`--loop`) is present, the script adds it.
   - Appends default flags for hiding on-screen controls, enabling hardware decoding, caching, initial volume, and setting up an IPC server for runtime volume control.

3. **Volume Control:**  
   - An event loop listens for key presses (Up and Down arrows) and sends commands via the IPC socket to adjust mpv's volume accordingly.

## Troubleshooting

- **Black Screen Issues with YouTube:**  
  If you experience a black screen when attempting to play a YouTube video, ensure that:
  - mpv’s PATH includes your yt-dlp (or youtube-dl) installation directory.
  - You can explicitly set the downloader path using `--ytdl-path`.
  - The environment used by your window manager (e.g., i3) includes the correct PATH.

- **X Display Issues:**  
  Verify that your `DISPLAY` environment variable is set correctly and that you are running the script in an Xorg session.

- **Dependency Errors:**  
  Make sure that `python3-xlib` is installed and that the script has the necessary permissions.

## License

This project is open source and available under the MIT License.
