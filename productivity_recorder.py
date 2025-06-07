# main.py
import tkinter as tk
from tkinter import messagebox
import threading
import cv2
import numpy as np
import pyautogui
import mss
import time
import datetime
import os
import json

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

stop_event = threading.Event()
pause_event = threading.Event()
recording = False
session_folder = ""
recorded_seconds = 0

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def record_screen(filepath):
    global recorded_seconds
    with mss.mss() as sct:
        monitors = sct.monitors[1:]
        left = min(m['left'] for m in monitors)
        top = min(m['top'] for m in monitors)
        right = max(m['left'] + m['width'] for m in monitors)
        bottom = max(m['top'] + m['height'] for m in monitors)
        total_width = right - left
        total_height = bottom - top

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(filepath, fourcc, 10.0, (total_width, total_height))

        while not stop_event.is_set():
            if pause_event.is_set():
                time.sleep(0.1)
                continue
            img = sct.grab({"top": top, "left": left, "width": total_width, "height": total_height})
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            out.write(frame)
            recorded_seconds += 0.1
            time.sleep(0.1)
        out.release()

def record_webcam(filepath):
    global recorded_seconds
    cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    ret, frame = cap.read()
    height, width, _ = frame.shape
    out = cv2.VideoWriter(filepath, fourcc, 10.0, (width, height))

    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(0.1)
            continue
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        time.sleep(0.1)
    cap.release()
    out.release()

def save_metadata(task_info, folder):
    metadata_path = os.path.join(folder, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(task_info, f, indent=4)

def start_session(task_description, datetime_start, datetime_end):
    global session_folder, recorded_seconds, recording
    stop_event.clear()
    pause_event.clear()
    recorded_seconds = 0
    recording = True

    session_timestamp = get_timestamp()
    session_folder = os.path.join(OUTPUT_DIR, f"task_{session_timestamp}")
    os.makedirs(session_folder, exist_ok=True)

    metadata = {
        "task_description": task_description,
        "datetime_start": datetime_start,
        "datetime_end": datetime_end,
        "actual_start_time": session_timestamp
    }
    save_metadata(metadata, session_folder)

    screen_path = os.path.join(session_folder, "screen.mp4")
    webcam_path = os.path.join(session_folder, "webcam.mp4")

    screen_thread = threading.Thread(target=record_screen, args=(screen_path,))
    webcam_thread = threading.Thread(target=record_webcam, args=(webcam_path,))

    screen_thread.start()
    webcam_thread.start()

def update_timer():
    if recording and not stop_event.is_set():
        label_timer.config(text=f"Recorded: {int(recorded_seconds)}s")
    app.after(500, update_timer)

def on_start():
    try:
        task_description = entry_task.get()
        datetime_start = entry_datetime_start.get()
        datetime_end = entry_datetime_end.get()
        start_button.config(state="disabled")
        stop_button.config(state="normal")
        pause_button.config(state="normal")
        resume_button.config(state="disabled")
        threading.Thread(target=start_session, args=(task_description, datetime_start, datetime_end), daemon=True).start()
    except ValueError:
        messagebox.showerror("Invalid Input", "Invalid input data.")

def on_stop():
    stop_event.set()
    start_button.config(state="normal")
    stop_button.config(state="disabled")
    pause_button.config(state="disabled")
    resume_button.config(state="disabled")

def on_pause():
    pause_event.set()
    pause_button.config(state="disabled")
    resume_button.config(state="normal")

def on_resume():
    pause_event.clear()
    pause_button.config(state="normal")
    resume_button.config(state="disabled")

app = tk.Tk()
app.title("Productivity Recorder")
app.geometry("400x400")

tk.Label(app, text="Task Description:").pack(pady=5)
entry_task = tk.Entry(app)
entry_task.pack()

tk.Label(app, text="Allowed Start (YYYY-MM-DD HH:MM):").pack(pady=5)
entry_datetime_start = tk.Entry(app)
entry_datetime_start.pack()

tk.Label(app, text="Allowed End (YYYY-MM-DD HH:MM):").pack(pady=5)
entry_datetime_end = tk.Entry(app)
entry_datetime_end.pack()

start_button = tk.Button(app, text="Start Recording", command=on_start)
start_button.pack(pady=5)

pause_button = tk.Button(app, text="Pause Recording", command=on_pause, state="disabled")
pause_button.pack(pady=5)

resume_button = tk.Button(app, text="Resume Recording", command=on_resume, state="disabled")
resume_button.pack(pady=5)

stop_button = tk.Button(app, text="Stop Recording", command=on_stop, state="disabled")
stop_button.pack(pady=5)

label_timer = tk.Label(app, text="Recorded: 0s")
label_timer.pack(pady=10)

update_timer()
app.mainloop()
