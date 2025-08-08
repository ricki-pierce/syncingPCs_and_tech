from flask import Flask, request
import subprocess
import os
import time
from pywinauto import Application, Desktop
from datetime import datetime

app = Flask(__name__)
wmp_process = None  # Global variable to track WMP process

VIDEO_FOLDER_PATH = r"C:\Users\B24-Lab\Desktop\Videos"

def log_event(message, start_time=None):
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Millisecond precision
    if start_time:
        delay = now - start_time
        print(f"[{timestamp}] {message} | Delay: {delay.total_seconds():.3f} seconds")
    else:
        print(f"[{timestamp}] {message}")
    return now

@app.route('/videos', methods=['GET'])
def list_videos():
    try:
        files = [f for f in os.listdir(VIDEO_FOLDER_PATH)
                 if f.endswith('.mp4') and os.path.isfile(os.path.join(VIDEO_FOLDER_PATH, f))]
        return {"videos": files}, 200
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/start', methods=['POST'])
def start_wmp():
    global wmp_process
    try:
        start_overall = log_event("Received request to START WMP")

        data = request.get_json()
        video_name = data.get("video_file")
        if not video_name:
            return "Error: 'video_file' not provided", 400

        video_path = os.path.join(VIDEO_FOLDER_PATH, video_name)

        # Validate file exists and is an mp4 file
        if not os.path.isfile(video_path) or not video_path.endswith(".mp4"):
            return f"Error: File not found or invalid type: {video_name}", 404

        log_event(f"Launching Windows Media Player with: {video_name}", start_overall)
        wmp_process = subprocess.Popen(['start', 'wmplayer', video_path], shell=True)
        launch_time = log_event("WMP launch command issued", start_overall)

        # Wait for WMP window to appear
        log_event("Waiting for WMP window to appear...", launch_time)
        MAX_WAIT = 10
        INTERVAL = 0.5
        wmp_window = None
        start_wait = time.time()

        while time.time() - start_wait < MAX_WAIT:
            wmp_windows = Desktop(backend="uia").windows(class_name="WMP Skin Host")
            if wmp_windows:
                wmp_window = wmp_windows[0]
                break
            time.sleep(INTERVAL)

        if wmp_window is None:
            log_event("Error: WMP window not found", launch_time)
            return "Error: WMP window not found", 500

        window_detected_time = log_event("WMP window detected", launch_time)

        # Connect to WMP window
        app_connected = Application(backend="uia").connect(handle=wmp_window.handle)
        window = app_connected.window(handle=wmp_window.handle)
        window.set_focus()
        log_event(f"Connected to WMP window: {window.window_text()}", window_detected_time)

        # Attempt fullscreen
        full_screen_button = window.child_window(title="View Full Screen", control_type="Button")
        if full_screen_button.exists():
            try:
                full_screen_button.click_input()
                log_event("Clicked 'View Full Screen' button.", window_detected_time)
            except Exception as e:
                log_event(f"Error clicking full screen button: {e}", window_detected_time)
        else:
            log_event("Fullscreen button not found. Sending ALT+ENTER...", window_detected_time)
            window.type_keys("%{ENTER}")

        done_time = log_event("WMP launched and fullscreen attempted", start_overall)

        return "WMP launched and switched to full screen (or attempted fullscreen).", 200

    except Exception as e:
        log_event(f"Exception occurred during /start: {e}")
        return f"Error starting WMP: {e}", 500

@app.route('/stop', methods=['POST'])
def stop_wmp():
    try:
        start_time = log_event("Received request to STOP WMP")
        os.system("taskkill /im wmplayer.exe /f")
        log_event("WMP process terminated", start_time)
        return "WMP stopped", 200
    except Exception as e:
        log_event(f"Exception occurred during /stop: {e}")
        return f"Error stopping WMP: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
