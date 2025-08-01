This project allows you to synchronize a QTM recording session on an Alienware PC with VLC media playback on a separate Aurora R16 PC over a local network. It uses:
  Tkinter GUI for user control (Alienware),
  Async QTM recording (Alienware),
  NTP time sync (Alienware),
  Flask API server to control VLC (Aurora R16).

Setup Instructions:
  On the Alienware PC, have QTM installed and calibrated and open. It should be ready to record. 
  Be able to run Python (preferably in Visual Studio Code). Have all necessary libraries imported.
  (If not using the Alienware PC and Aurora R16 PC, IPs and Servers will need to be changed.
      For the Human Development and Daily Life Lab in B2, AURORA_IP = "130.39.121.10" and Alienware IP = 130.39.254.33)
  Make sure QTM is open and ready to record data. Duration should be set to continuous. 

  On the Aurora R16 PC, have VLC or Windows Media Player installed. It does not have to be open.
  Be able to run Python (preferably in Visual Studio Code). Have all necessary libraries imported.
  Update the video path to match where your file is: video_path = r"C:\Users\B24-Lab\Desktop\Videos\1_Ball_Social-.mp4"
  Also ensure vlc_path points to the actual VLC installation: vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"

Running the Code:
  Run the Flask server auroratriggerserver.py On the Aurora R16 PC.
  You should see:  Running on http://0.0.0.0:5000/ (Press CTRL+C to quit).
  Run aliensync.py on the Alienware PC.
  Click START in the GUI:
    Clock is synced via NTP,
    QTM begins recording,
    Aurora begins video playback via VLC.
  Click STOP when done:
    QTM recording stops,
    VLC is terminated remotely.
  


