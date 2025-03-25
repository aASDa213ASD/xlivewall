# xLiveWall | Video Background for Xorg

This Python application creates a desktop window on an Xorg session and then launches an external command (for example, a video player) with the window ID (WID) embedded in its arguments. It is designed to allow you to display video backgrounds behind your desktop icons.

## Features

- **Desktop Window Creation:** The script creates a full-screen, non-interfering (override_redirect) window.
- **WID Injection:** It automatically retrieves the window ID and replaces the placeholder `WID` in your command arguments with the actual window ID in hexadecimal format.
- **Flexible External Command:** Use any external command that accepts a window ID (e.g., video players like `mpv`).

## Prerequisites

- **Python 3:** Ensure Python 3 is installed on your system.
- **Xlib:** The application depends on the `python3-xlib` package to interact with the X server.
- **Xorg Environment:** This script is intended to be used in an Xorg session.

## Installation

1. **Install Python 3:**  
   If you do not already have Python 3 installed, download it from the [official website](https://www.python.org/downloads/) or use your distribution's package manager.

2. **Install python3-xlib:**  
   On Debian/Ubuntu-based systems, run:  
   ```bash
   sudo apt-get update
   sudo apt-get install python3-xlib
   ```
   On other distributions, use your package manager to install the equivalent package (e.g., `python-xlib`).

3. **Download the Script:**  
   Clone or download the repository containing the script. Make sure the script is executable:
   ```bash
   chmod +x xlivewall.py
   ```

## Usage

The script expects at least one argument – the command to be executed with its arguments. Any occurrence of the string `WID` in the command will be replaced by the actual window ID (in hexadecimal) of the created desktop window.

### Basic Command Format

```bash
./xlivewall.py COMMAND [ARGS...]
```

### Example

For example, if you want to use `mpv` to display a video as your background and it accepts a window ID parameter via the option `--wid`, you can run:

```bash
./xlivewall.py mpv --wid=WID /path/to/video.mp4 --loop
```

In this example:
- The script creates a full-screen desktop window.
- It prints the window ID (e.g., `0x2600008`) to the terminal.
- It replaces `WID` in the command with the actual window ID before executing `mpv`.

## Getting the Window ID (WID)

The window ID is automatically retrieved by the script using the Xlib API. The steps are as follows:
1. The script connects to the X display and retrieves the root window.
2. It then creates a full-screen window with the `override_redirect` attribute to prevent window manager interference.
3. After mapping the window and configuring it as a desktop type, the script outputs the window ID in hexadecimal format.
4. Any command-line argument containing `WID` is automatically substituted with this window ID.

This makes it seamless to pass the correct window ID to any external application that requires it.

## Troubleshooting

- **X Display Issues:** Ensure that your `DISPLAY` environment variable is correctly set and that you are running the script within an Xorg session.
- **Dependencies:** Verify that `python3-xlib` is installed and accessible to your Python 3 interpreter.
- **Permission Errors:** If you encounter permission issues, make sure that the script is executable and that you have the necessary permissions to create windows on your Xorg display.

## License

This project is open source and available under the MIT License.
