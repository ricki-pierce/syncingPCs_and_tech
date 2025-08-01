#Dr Su requested videos be played through Windows Media Player rather than VLC
# Import Flask so we can create a simple web server on this computer
from flask import Flask

# These two libraries let us open programs (like videos) and control running apps
import subprocess
import os

# This line creates the actual web app we’ll use
app = Flask(__name__)

# This variable will help us remember if Windows Media Player is running
wmp_process = None

# -------------------------- START VIDEO --------------------------

# This sets up a special web link (called an "endpoint") that, when used, will start a video
@app.route('/start', methods=['POST'])  # This means we can send a POST request to http://<ip>:5000/start
def start_wmp():
    global wmp_process  # So we can update the variable from outside the function too

    try:
        # This is the full location of the video we want to play on the computer
        video_path = r"C:\Users\B24-Lab\Desktop\Videos\1_Ball_Social-.mp4"

        # This tells Windows to open Windows Media Player and play the video
        # 'start' means open something, 'wmplayer' is Windows Media Player
        wmp_process = subprocess.Popen(
            ['start', 'wmplayer', video_path],
            shell=True  # 'shell=True' lets us use Windows-style commands
        )

        return "Windows Media Player started", 200  # Return a success message if all goes well
    except Exception as e:
        return f"Error starting Windows Media Player: {e}", 500  # Return an error if something goes wrong

# -------------------------- STOP VIDEO --------------------------

# This sets up another link that stops the video playing
@app.route('/stop', methods=['POST'])  # Send a POST request to http://<ip>:5000/stop to run this
def stop_wmp():
    try:
        # This command forces Windows to shut down Windows Media Player if it's running
        os.system("taskkill /im wmplayer.exe /f")
        return "Windows Media Player stopped", 200  # If successful, tell the user
    except Exception as e:
        return f"Error stopping Windows Media Player: {e}", 500  # If there's an issue, report it

# -------------------------- START SERVER --------------------------

# This tells Python to actually start the web server when we run this file
# 'host=0.0.0.0' means anyone on the local network can send commands to it
# 'port=5000' is just the door number for communication (like a street address + apartment number)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
