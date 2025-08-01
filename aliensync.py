#This code syncs the Alienware PC to the Aurora R16 PC. Alienware runs QTM, and AuroraR16 runs VLC. 
#Need to run auroratriggerserver.py on Aurora FIRST. VLC does not need to  be opened.
#Open QTM, and get ready to record, making sure the duration is set to continuous. 
#Then run this aliensync.py on the Alienware PC. When you run it, a start/stop button will appear. When you click start, the clocks from both PCs will sync
#and then QTM will begin recording while the VLC plays the video on Aurora R16.

import tkinter as tk       # This helps us make windows and buttons for the user to click
import asyncio             # This helps run tasks in the background without stopping the program
import threading           # This lets us run multiple parts of the program at the same time
import qtm                 # This is a library to talk to Qualisys motion capture system
import requests            # This helps us send messages over the internet (like asking a website to do something)
import ntplib              # This lets us get the exact time from internet time servers
from datetime import datetime  # This helps work with dates and times

# === CONFIGURATION ===
QTM_IP = "127.0.0.1"  # The address where the QTM system is running (localhost means the same computer)
AURORA_IP = "130.39.121.10"  # The address of a computer named Aurora that runs VLC player
VLC_TRIGGER_ENDPOINT = f"http://{AURORA_IP}:5000/start"  # The web address to tell Aurora to start VLC
NTP_SERVER = "time.windows.com"  # The internet time server we use to get the exact current time

# === Global variables ===
qtm_connection = None  # This will hold our connection to QTM when we start it
loop = asyncio.new_event_loop()  # This is a special loop to run background tasks (asyncio stuff)

# === Asyncio thread setup ===
def start_event_loop():
    asyncio.set_event_loop(loop)  # Set the background task loop for this thread
    loop.run_forever()             # Keep this loop running forever to handle background tasks

# Start a new background thread to run the asyncio loop
threading.Thread(target=start_event_loop, daemon=True).start()

# === NTP SYNC FUNCTION ===
def sync_time_ntp(ntp_server):
    try:
        client = ntplib.NTPClient()  # Create a client to ask for time from the NTP server
        response = client.request(ntp_server, version=3)  # Ask the server for the current time
        ntp_time = datetime.fromtimestamp(response.tx_time)  # Convert the time to a readable format
        print(f"[✓] NTP Time Synced: {ntp_time}")  # Tell the user the time sync worked
    except Exception as e:
        print(f"[!] NTP sync failed: {e}")  # If something goes wrong, tell the user

# === QTM START ===
async def start_qtm_recording():
    global qtm_connection
    try:
        qtm_connection = await qtm.connect(QTM_IP)  # Connect to the QTM system
        if qtm_connection is None:
            print("[!] Failed to connect to QTM.")  # If we can’t connect, tell the user
            return
        await qtm_connection.take_control("")  # Take control of QTM (no password needed)
        await qtm_connection.start()           # Start recording motion data
        print("[✓] QTM recording started.")
    except Exception as e:
        print(f"[!] QTM start error: {e}")

# === QTM STOP ===
async def stop_qtm_recording():
    global qtm_connection
    try:
        if qtm_connection:                   # If we are connected to QTM
            await qtm_connection.stop()     # Stop the recording
            print("[✓] QTM recording stopped.")
            qtm_connection.disconnect()     # Disconnect from QTM
            print("[✓] QTM disconnected.")
            qtm_connection = None            # Clear the connection variable
        else:
            print("[!] No active QTM connection.")  # If not connected, tell the user
    except Exception as e:
        print(f"[!] QTM stop error: {e}")

# === VLC TRIGGER FUNCTION ===
def trigger_vlc_on_aurora():
    try:
        response = requests.post(VLC_TRIGGER_ENDPOINT)  # Send a request to Aurora to start VLC
        if response.status_code == 200:
            print("[✓] VLC playback triggered on Aurora.")  # Success message
        else:
            print(f"[!] Aurora responded with status: {response.status_code}")  # If not successful
    except Exception as e:
        print(f"[!] Failed to trigger VLC on Aurora: {e}")

# === VLC STOP FUNCTION ===
def stop_vlc_on_aurora():
    try:
        response = requests.post(f"http://{AURORA_IP}:5000/stop")  # Tell Aurora to stop VLC
        if response.status_code == 200:
            print("[✓] VLC stopped on Aurora.")  # Success message
        else:
            print(f"[!] Aurora responded with status: {response.status_code}")
    except Exception as e:
        print(f"[!] Failed to stop VLC on Aurora: {e}")

# === Button logic ===
def on_start_button_click():
    print("[*] Syncing clocks...")       # Tell user what we’re doing
    sync_time_ntp(NTP_SERVER)             # Sync computer clock with internet time
    print("[*] Starting QTM and triggering VLC...")  # Next step info
    asyncio.run_coroutine_threadsafe(start_qtm_recording(), loop)  # Start QTM recording in background
    trigger_vlc_on_aurora()               # Tell Aurora to start VLC

def on_stop_button_click():
    print("[*] Stopping QTM and VLC...")  # Tell user what we’re doing
    asyncio.run_coroutine_threadsafe(stop_qtm_recording(), loop)  # Stop QTM recording in background
    stop_vlc_on_aurora()                  # Tell Aurora to stop VLC

def on_close():
    loop.call_soon_threadsafe(loop.stop)  # Stop the background task loop safely
    root.destroy()                        # Close the GUI window

# === GUI ===
def launch_gui():
    global root
    root = tk.Tk()  # Create the main window
    root.title("Sync Controller")  # Window title
    root.geometry("300x200")       # Window size

    label = tk.Label(root, text="Click to Start/Stop Sync", font=("Helvetica", 14))  # Add text label
    label.pack(pady=20)  # Put it in the window with some space around

    start_button = tk.Button(root, text="START", font=("Helvetica", 16, "bold"),
                             bg="green", fg="white", command=on_start_button_click)  # Green Start button
    start_button.pack(pady=10)  # Add to window with spacing

    stop_button = tk.Button(root, text="STOP", font=("Helvetica", 16, "bold"),
                            bg="red", fg="white", command=on_stop_button_click)  # Red Stop button
    stop_button.pack(pady=10)  # Add to window

    root.protocol("WM_DELETE_WINDOW", on_close)  # What to do when user closes window
    root.mainloop()  # Start the window and wait for user interaction

# === MAIN ===
if __name__ == "__main__":
    launch_gui()  # Start the program by launching the window
