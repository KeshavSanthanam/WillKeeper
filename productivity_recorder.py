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

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

stop_event = threading.Event()

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def record_screen(duration_sec, filename):
    timestamp = get_timestamp()
    filepath = os.path.join(OUTPUT_DIR, f"{filename}_{timestamp}.mp4")

    with mss.mss() as sct:
        monitors = sct.monitors[1:]  # skip index 0, it's the virtual full desktop

        # Get bounding box for all monitors
        left = min(monitor['left'] for monitor in monitors)
        top = min(monitor['top'] for monitor in monitors)
        right = max(monitor['left'] + monitor['width'] for monitor in monitors)
        bottom = max(monitor['top'] + monitor['height'] for monitor in monitors)

        total_width = right - left
        total_height = bottom - top

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(filepath, fourcc, 10.0, (total_width, total_height))

        start_time = time.time()
        while time.time() - start_time < duration_sec:
            if stop_event.is_set():
                break
            img = sct.grab({"top": top, "left": left, "width": total_width, "height": total_height})
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            out.write(frame)
        out.release()

def record_webcam(duration_sec, filename):
    timestamp = get_timestamp()
    filepath = os.path.join(OUTPUT_DIR, f"{filename}_{timestamp}.mp4")

    cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    ret, frame = cap.read()
    height, width, _ = frame.shape
    out = cv2.VideoWriter(filepath, fourcc, 10.0, (width, height))

    start_time = time.time()
    while time.time() - start_time < duration_sec:
        if stop_event.is_set():
            break
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
    cap.release()
    out.release()

def start_session(duration_min):
    stop_event.clear()
    duration_sec = duration_min * 60
    screen_thread = threading.Thread(target=record_screen, args=(duration_sec, "screen"))
    webcam_thread = threading.Thread(target=record_webcam, args=(duration_sec, "webcam"))

    screen_thread.start()
    webcam_thread.start()

    screen_thread.join()
    webcam_thread.join()

    messagebox.showinfo("Session Done", "Your session recordings have been saved.")
    start_button.config(state="normal")
    stop_button.config(state="disabled")

def on_start():
    try:
        minutes = int(entry.get())
        if minutes <= 0:
            raise ValueError
        start_button.config(state="disabled")
        stop_button.config(state="normal")
        threading.Thread(target=start_session, args=(minutes,), daemon=True).start()
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid number of minutes.")

def on_stop():
    stop_event.set()

app = tk.Tk()
app.title("Productivity Recorder")
app.geometry("300x200")

label = tk.Label(app, text="Session Length (minutes):")
label.pack(pady=10)

entry = tk.Entry(app)
entry.pack()

start_button = tk.Button(app, text="Start Session", command=on_start)
start_button.pack(pady=10)

stop_button = tk.Button(app, text="Stop Session", command=on_stop, state="disabled")
stop_button.pack(pady=5)

app.mainloop()
