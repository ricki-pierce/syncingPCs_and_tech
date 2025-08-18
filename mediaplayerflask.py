  #This is the flask server to be used on Aurora.
#Timestamps according to the domain controller clock (Windows)
from flask import Flask, request, jsonify
import subprocess
import os
import time
from pywinauto import Application, Desktop
from datetime import datetime
import random
import requests
import json
import pytz
import pyautogui

app = Flask(__name__)

def sync_windows_time():
    try:
        output = subprocess.check_output(['w32tm', '/resync'], shell=True, stderr=subprocess.STDOUT, text=True)
        print(f"Time sync success:\n{output}")
    except subprocess.CalledProcessError as e:
        print(f"Time sync failed:\n{e.output}")

CENTRAL_TZ = pytz.timezone('America/Chicago')

def ntp_time_central(tx_time):
    return datetime.fromtimestamp(tx_time, CENTRAL_TZ)


VIDEO_FOLDER_PATH = r"C:\Users\B24-Lab\Desktop\Videos2"

# Track remaining videos so none are repeated in a session
social_remaining = []
nonsocial_remaining = []


def send_log_to_alienware(log_message):
    url = 'http://10.39.120.115:8000/log'
    try:
        requests.post(url, json={'log': log_message})
    except Exception as e:
        print(f"Failed to send log: {e}")


def log_event(message, start_time=None):
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Millisecond precision
    if start_time:
        delay = now - start_time
        log_line = f"[{timestamp}] {message} | Delay: {delay.total_seconds():.3f} seconds"
    else:
        log_line = f"[{timestamp}] {message}"
    
    print(log_line)
    send_log_to_alienware(log_line)  # <--- send every log line
    return now


def load_video_lists():
    """Load fresh lists of social and nonsocial videos from folder."""
    global social_remaining, nonsocial_remaining
    try:
        files = [f for f in os.listdir(VIDEO_FOLDER_PATH)
                 if f.lower().endswith('.mp4') and os.path.isfile(os.path.join(VIDEO_FOLDER_PATH, f))]

        # Ensure strict filtering
        nonsocial_remaining = [
            f for f in files
            if "_nonsocial-" in f.lower() and "_social-" not in f.lower()
        ]
        social_remaining = [
            f for f in files
            if "_social-" in f.lower() and "_nonsocial-" not in f.lower()
        ]

        print(f"[✓] Loaded {len(social_remaining)} social and {len(nonsocial_remaining)} nonsocial videos.")
    except Exception as e:
        print(f"[!] Error loading video lists: {e}")
        social_remaining = []
        nonsocial_remaining = []

@app.route('/videos', methods=['GET'])
def list_videos():
    """Return all videos in the folder."""
    try:
        files = [f for f in os.listdir(VIDEO_FOLDER_PATH)
                 if f.lower().endswith('.mp4') and os.path.isfile(os.path.join(VIDEO_FOLDER_PATH, f))]
        return {"videos": files}, 200
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/random_social', methods=['GET'])
def random_social():
    """Return a random unused social video."""
    global social_remaining
    if not social_remaining:
        return {"error": "No more social videos available"}, 404
    choice = random.choice(social_remaining)
    social_remaining.remove(choice)
    return jsonify({"video": choice})

@app.route('/random_nonsocial', methods=['GET'])
def random_nonsocial():
    """Return a random unused nonsocial video."""
    global nonsocial_remaining
    if not nonsocial_remaining:
        return {"error": "No more nonsocial videos available"}, 404
    choice = random.choice(nonsocial_remaining)
    nonsocial_remaining.remove(choice)
    return jsonify({"video": choice})

@app.route('/start', methods=['POST'])
def start_media_player():
    try:
        start_overall = log_event("Received request to START Microsoft Media Player")

        data = request.get_json()
        video_name = data.get("video_file")
        if not video_name:
            return "Error: 'video_file' not provided", 400

        video_path = os.path.join(VIDEO_FOLDER_PATH, video_name)
        if not os.path.isfile(video_path):
            return f"Error: File not found: {video_name}", 404

        log_event(f"Launching video file directly: {video_name}", start_overall)

        # Launch video file with default associated app (Media Player UWP)
        # Using powershell Start-Process on the video file path
        powershell_command = f'Start-Process -FilePath "{video_path}"'
        subprocess.Popen(["powershell", "-Command", powershell_command], shell=True)

        # Wait for the Media Player window to appear
        MAX_WAIT = 15
        INTERVAL = 0.5
        mp_window = None
        start_wait = time.time()
        while time.time() - start_wait < MAX_WAIT:
            try:
                windows = Desktop(backend="uia").windows()
                for w in windows:
                    if "media player" in w.window_text().lower():
                        mp_window = w
                        break
                if mp_window:
                    break
            except Exception:
                pass
            time.sleep(INTERVAL)

        if mp_window is None:
            log_event("Error: Microsoft Media Player window not found", start_overall)
            return "Error: Media Player window not found", 500

        log_event("Microsoft Media Player window detected", start_overall)

        # Connect and focus
        app_connected = Application(backend="uia").connect(handle=mp_window.handle)
        window = app_connected.window(handle=mp_window.handle)
        window.set_focus()

        # Send fullscreen key (ALT+ENTER)
        window.type_keys("%{ENTER}")
        log_event("Sent ALT+ENTER for fullscreen", start_overall)

        # Send Pixelwarp fit-to-screen keys
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'shift', 'z')
        log_event("Sent Ctrl+Shift+Z for Pixelwarp fit-to-screen", start_overall)

        # Try to click Play button if exists
        play_button = window.child_window(title="Play", control_type="Button")
        if play_button.exists():
            try:
                play_button.click_input()
                log_event("Clicked Play button", start_overall)
            except Exception as e:
                log_event(f"Error clicking Play button: {e}", start_overall)
        else:
            log_event("Play button not found", start_overall)

        log_event("Video started successfully", start_overall)
        return "Video started successfully", 200

    except Exception as e:
        log_event(f"Exception occurred during /start: {e}")
        return f"Error starting Microsoft Media Player: {e}", 500


@app.route('/stop', methods=['POST'])
def stop_media_player():
    try:
        start_time = log_event("Received request to STOP Media Player")
        # Close window(s) with "Media Player" in title
        windows = Desktop(backend="uia").windows()
        closed_any = False
        for w in windows:
            if "Media Player" in w.window_text():
                try:
                    w.close()
                    closed_any = True
                except Exception as e:
                    log_event(f"Error closing Media Player window: {e}", start_time)
        # If no window closed, fallback to kill process (may affect other UWP apps)
        if not closed_any:
            os.system("taskkill /f /im ApplicationFrameHost.exe")
            log_event("Killed ApplicationFrameHost.exe", start_time)

        log_event("Media Player stopped", start_time)
        return "Media Player stopped", 200
    except Exception as e:
        log_event(f"Exception stopping Media Player: {e}")
        return f"Error stopping Media Player: {e}", 500

    except Exception as e:
        log_event(f"Exception during replay: {e}")
        return f"Error during replay: {e}", 500


if __name__ == '__main__':
    sync_windows_time()         # Then Windows time sync
    load_video_lists()  # Load lists at startup
    app.run(host='0.0.0.0', port=5000)

