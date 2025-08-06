from flask import Flask
import subprocess
import os
import time
from pywinauto import Application, Desktop

app = Flask(__name__)
wmp_process = None

@app.route('/start', methods=['POST'])
def start_wmp():
    global wmp_process
    try:
        video_path = r"C:\Users\B24-Lab\Desktop\Videos\1_Ball_Social-.mp4"

        # Launch WMP via subprocess
        wmp_process = subprocess.Popen(
            ['start', 'wmplayer', video_path],
            shell=True
        )

        # Give WMP time to launch and load video
        time.sleep(5)

        # Connect to the WMP window
        app = Application(backend="uia").connect(title_re=".*Windows Media Player.*")
        window = app.window(title_re=".*Windows Media Player.*")
        window.set_focus()

        # Look for "View Full Screen" button
        full_screen_button = window.child_window(title="View Full Screen", control_type="Button")
        if full_screen_button.exists():
            full_screen_button.click_input()
            return "WMP launched and switched to full screen.", 200
        else:
            return "WMP launched, but full screen button not found.", 500

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
