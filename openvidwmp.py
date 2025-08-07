from flask import Flask
import subprocess
import os
import time
from pywinauto import Application, Desktop

app = Flask(__name__)
wmp_process = None  # Global placeholder

from flask import Flask
import subprocess
import time
from pywinauto import Application, Desktop

app = Flask(__name__)
wmp_process = None  # Global variable to track WMP process

@app.route('/start', methods=['POST'])
def start_wmp():
    global wmp_process
    try:
        video_path = r"C:\Users\B24-Lab\Desktop\Videos\1_Ball_Social-.mp4"

        # Launch Windows Media Player with the video
        wmp_process = subprocess.Popen(
            ['start', 'wmplayer', video_path],
            shell=True
        )

        # Wait up to 10 seconds for WMP window to appear
        MAX_WAIT = 10
        INTERVAL = 0.5

        wmp_window = None
        start_time = time.time()
        while time.time() - start_time < MAX_WAIT:
            wmp_windows = Desktop(backend="uia").windows(class_name="WMP Skin Host")
            if wmp_windows:
                wmp_window = wmp_windows[0]
                break
            time.sleep(INTERVAL)

        if wmp_window is None:
            return "Error: WMP window not found", 500

        # Connect to the window
        app_connected = Application(backend="uia").connect(handle=wmp_window.handle)
        window = app_connected.window(handle=wmp_window.handle)
        window.set_focus()

        print(f"[Debug] Connected to window: {window.window_text()}")

        # Try fullscreen via button or ALT+ENTER (only once)
        full_screen_button = window.child_window(title="View Full Screen", control_type="Button")
        if full_screen_button.exists():
            try:
                full_screen_button.click_input()
                print("[✓] Clicked 'View Full Screen' button.")
            except Exception as e:
                print(f"[!] Error clicking full screen button: {e}")
        else:
            print("[!] Full screen button not found. Sending ALT+ENTER once.")
            window.type_keys("%{ENTER}")

        return "WMP launched and switched to full screen (or attempted fullscreen).", 200

    except Exception as e:
        return f"Error starting WMP: {e}", 500




@app.route('/stop', methods=['POST'])
def stop_wmp():
    try:
        os.system("taskkill /im wmplayer.exe /f")
        return "WMP stopped", 200
    except Exception as e:
        return f"Error stopping WMP: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
