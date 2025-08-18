 from flask import Flask, request, jsonify
from datetime import datetime
import threading
import time
import openpyxl
import os
import re
import subprocess
import pytz

app = Flask(__name__)

NTP_SERVER = "time.google.com"

def sync_windows_time():
    try:
        output = subprocess.check_output(['w32tm', '/resync'], shell=True, stderr=subprocess.STDOUT, text=True)
        print(f"Time sync success:\n{output}")
    except subprocess.CalledProcessError as e:
        print(f"Time sync failed:\n{e.output}")

excel_file_path = None  # path to Excel file, set dynamically
log_buffer = []    # buffer logs if Excel not ready
buffer_lock = threading.Lock()


current_trial = None  # global to track current trial number or label

def append_log_to_excel(message):
    global excel_file_path, current_trial
    try:
        if not excel_file_path or not os.path.exists(excel_file_path):
            return False

        wb = openpyxl.load_workbook(excel_file_path)
        ws = wb.active

        # Handle TRIAL lines first
        if message.startswith("TRIAL"):
            # Extract the "TRIAL #" part (like "TRIAL 1")
            trial_match = re.match(r"(TRIAL \d+)", message)
            if trial_match:
                current_trial = trial_match.group(1)
                # Extract the rest after "TRIAL #" for message text (scheduled start time etc)
                rest_message = message[len(current_trial):].strip()
                # Write trial number in A, message in B, leave timestamp empty in C
                ws.append([current_trial, rest_message, ""])
            else:
                # fallback: just write whole message in B with empty A and C
                ws.append(["", message, ""])

        else:
            # For other lines, extract timestamp inside square brackets or at start
            # Example formats:
            # "[2025-08-11 14:42:27.117] Received request to START WMP"
            # or
            # "2025-08-11 14:42:27.117 Received request to START WMP"
            timestamp = ""
            msg_text = message

            # Try extracting timestamp inside square brackets
            timestamp_match = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\]\s*(.*)", message)
            if timestamp_match:
                timestamp = timestamp_match.group(1)
                msg_text = timestamp_match.group(2)
            else:
                # Try extracting timestamp at the very start without brackets
                timestamp_match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\s*(.*)", message)
                if timestamp_match:
                    timestamp = timestamp_match.group(1)
                    msg_text = timestamp_match.group(2)

            # Write empty in A (because not trial line), message in B, timestamp in C
            ws.append(["", msg_text, timestamp])

        wb.save(excel_file_path)
        return True

    except Exception as e:
        print(f"[Error writing log to Excel]: {e}")
        return False

def flush_buffered_logs():
    global log_buffer
    with buffer_lock:
        if not excel_file_path or not os.path.exists(excel_file_path):
            return
        for msg in log_buffer:
            append_log_to_excel(msg)
        log_buffer = []


@app.route('/set_excel_file_path', methods=['POST'])
def set_excel_file_path():
    global excel_file_path
    data = request.get_json()
    path = data.get("excel_file_path")
    if not path:
        return "Missing 'excel_file_path' in request", 400

    excel_file_path = path
    print(f"[+] Excel path set to: {excel_file_path}")

    # Flush any buffered logs now that Excel path is set
    flush_buffered_logs()

    return "Excel file path updated", 200


@app.route('/log', methods=['POST'])
def log_event():
    global log_buffer
    data = request.get_json()
    message = data.get("log")
    if not message:
        return "Missing 'log' in request", 400

    print(f"Log received: {message}")

    success = append_log_to_excel(message)
    if not success:
        # Buffer log for later if Excel not ready
        with buffer_lock:
            log_buffer.append(message)
        print("[!] Excel file not ready, log buffered.")

    return "Log processed", 200


if __name__ == '__main__':
    sync_windows_time()           # Windows system time sync
    print("Starting Alienware Flask server...")
    app.run(host='0.0.0.0', port=8000)

