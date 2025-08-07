#This code syncs the Alienware PC to the Aurora R16 PC. Alienware runs QTM, and AuroraR16 runs VLC. 
#Need to run auroratriggerserver.py on Aurora FIRST. VLC does not need to  be opened.
#Open QTM, and get ready to record, making sure the duration is set to continuous. 
#Then run this aliensync.py on the Alienware PC. When you run it, a start/stop button will appear. When you click start, the clocks from both PCs will sync
#and then QTM will begin recording while the VLC plays the video on Aurora R16.
import tkinter as tk
import asyncio
import threading
import qtm
import requests
import ntplib
from datetime import datetime, timedelta
from datetime import timezone
import json

# === CONFIGURATION ===
QTM_IP = "127.0.0.1"
AURORA_IP = "130.39.121.10"
VLC_TRIGGER_ENDPOINT = f"http://{AURORA_IP}:5000/start"
NTP_SERVER = "time.google.com"

# === Global variables ===
qtm_connection = None
loop = asyncio.new_event_loop()

# === Asyncio thread setup ===
def start_event_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_event_loop, daemon=True).start()

# === NTP SYNC FUNCTION ===
def sync_time_ntp(ntp_server):
    try:
        client = ntplib.NTPClient()
        response = client.request(ntp_server, version=3)
        ntp_time = datetime.fromtimestamp(response.tx_time)
        print(f"[✓] NTP Time Synced: {ntp_time}")
    except Exception as e:
        print(f"[!] NTP sync failed: {e}")

# === QTM START ===
async def start_qtm_recording():
    global qtm_connection
    try:
        qtm_connection = await qtm.connect(QTM_IP)
        if qtm_connection is None:
            print("[!] Failed to connect to QTM.")
            return
        await qtm_connection.take_control("")  # No password
        await qtm_connection.start()
        print("[✓] QTM recording started.")
    except Exception as e:
        print(f"[!] QTM start error: {e}")

# === QTM STOP ===
async def stop_qtm_recording():
    global qtm_connection
    try:
        if qtm_connection:
            await qtm_connection.stop()
            print("[✓] QTM recording stopped.")
            qtm_connection.disconnect()
            print("[✓] QTM disconnected.")
            qtm_connection = None
        else:
            print("[!] No active QTM connection.")
    except Exception as e:
        print(f"[!] QTM stop error: {e}")

# === VLC TRIGGER FUNCTION ===
def trigger_vlc_on_aurora(start_time):
    try:
        payload = {"start_time": start_time.isoformat()}
        response = requests.post(VLC_TRIGGER_ENDPOINT, json=payload)

        if response.status_code == 200:
            print("[✓] VLC playback triggered on Aurora.")
        else:
            print(f"[!] Aurora responded with status: {response.status_code}")
    except Exception as e:
        print(f"[!] Failed to trigger VLC on Aurora: {e}")


# === VLC STOP FUNCTION ===
def stop_vlc_on_aurora():
    try:
        response = requests.post(f"http://{AURORA_IP}:5000/stop")
        if response.status_code == 200:
            print("[✓] VLC stopped on Aurora.")
        else:
            print(f"[!] Aurora responded with status: {response.status_code}")
    except Exception as e:
        print(f"[!] Failed to stop VLC on Aurora: {e}")


# === Button logic ===
def on_start_button_click():
    print("[*] Syncing clocks...")
    sync_time_ntp(NTP_SERVER)

    # Add a small buffer so Aurora has time to prepare
    buffer_seconds = 5
    start_time = datetime.now(timezone.utc) + timedelta(seconds=buffer_seconds)
    print(f"[*] Intended sync start time (UTC + {buffer_seconds}s buffer): {start_time}")

    # Start QTM asynchronously
    print(f"[*] Triggering QTM at {datetime.now(timezone.utc)} (UTC)")
    asyncio.run_coroutine_threadsafe(start_qtm_recording(), loop)

    # Trigger VLC playback with epoch timestamp
    print(f"[*] Triggering VLC at {datetime.now(timezone.utc)} (UTC)")
    try:
        payload = {"start_time": start_time.timestamp()}
        response = requests.post(VLC_TRIGGER_ENDPOINT, json=payload)

        if response.status_code == 200:
            print("[✓] VLC playback triggered on Aurora.")
        else:
            print(f"[!] Aurora responded with status: {response.status_code}")
            print(f"[!] Response body: {response.text}")  # log details
    except Exception as e:
        print(f"[!] Failed to trigger VLC on Aurora: {e}")



def on_stop_button_click():
    print("[*] Stopping QTM and VLC...")
    asyncio.run_coroutine_threadsafe(stop_qtm_recording(), loop)
    stop_vlc_on_aurora()

def on_close():
    loop.call_soon_threadsafe(loop.stop)
    root.destroy()

# === GUI ===
def launch_gui():
    global root
    root = tk.Tk()
    root.title("Sync Controller")
    root.geometry("300x200")

    label = tk.Label(root, text="Click to Start/Stop Sync", font=("Helvetica", 14))
    label.pack(pady=20)

    start_button = tk.Button(root, text="START", font=("Helvetica", 16, "bold"),
                             bg="green", fg="white", command=on_start_button_click)
    start_button.pack(pady=10)

    stop_button = tk.Button(root, text="STOP", font=("Helvetica", 16, "bold"),
                            bg="red", fg="white", command=on_stop_button_click)
    stop_button.pack(pady=10)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

# === MAIN ===
if __name__ == "__main__":
    launch_gui()
