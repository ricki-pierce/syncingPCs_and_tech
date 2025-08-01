#This code creates a flask server to be run on Aurora R16 PC BEFORE you run the main aliensync.py on Alienware.
#Unlike QTM being opneed already on Alienware, VLC DOES NOT have to be opened prior to running the script. 
#You will need to change the destination of the video file. 


# Importing the Flask web framework, which lets us easily create a simple web server
from flask import Flask

# These help us run programs on the computer and control processes
import subprocess
import os
import signal

# Create a Flask web app instance — this is like setting up your server
app = Flask(__name__)

# We'll use this variable to keep track of whether VLC is running
vlc_process = None  # Global means it's available throughout the program

# This sets up a route (URL endpoint) that people or apps can visit to start a video
@app.route('/start', methods=['POST'])  # Only responds to POST requests (not GET)
def start_vlc():
    global vlc_process  # Use the global variable so we can update it

    try:
        # Set the path to the video file and the VLC media player app on this computer
        video_path = r"C:\Users\B24-Lab\Desktop\Videos\1_Ball_Social-.mp4"
        vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"

        # Start playing the video in fullscreen using VLC through a subprocess (basically running a command)
        vlc_process = subprocess.Popen([vlc_path, video_path, "--fullscreen"])

        return "VLC started", 200  # Return a success message with status code 200
    except Exception as e:
        return f"Error starting VLC: {e}", 500  # Return an error message with status code 500 (server error)

# This sets up another route (URL endpoint) to stop the video that's playing
@app.route('/stop', methods=['POST'])  # Also only responds to POST requests
def stop_vlc():
    global vlc_process  # Use the global variable

    try:
        # Force VLC to close using a system command that ends the VLC process
        os.system("taskkill /im vlc.exe /f")
        vlc_process = None  # Reset the variable to show VLC is no longer running

        return "VLC stopped", 200  # Success message
    except Exception as e:
        return f"Error stopping VLC: {e}", 500  # Error message

# This is needed to actually start the server. It runs on all network interfaces (0.0.0.0) and port 5000.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
