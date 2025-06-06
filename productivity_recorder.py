import tkinter as tk
from tkinter import messagebox
import threading
import cv2
import numpy as np
import pyautogui
import time
import datetime
import os
#s
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def record_screen(duration_sec, filename):
    timestamp = get_timestamp()
    filepath = os.path.join(OUTPUT_DIR, f"{filename}_{timestamp}.mp4")

    screen_size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filepath, fourcc, 10.0, screen_size)

    start_time = time.time()
    while time.time() - start_time < duration_sec:
        img = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
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
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
    cap.release()
    out.release()

def start_session(duration_min):
    duration_sec = duration_min * 60
    screen_thread = threading.Thread(target=record_screen, args=(duration_sec, "screen"))
    webcam_thread = threading.Thread(target=record_webcam, args=(duration_sec, "webcam"))

    screen_thread.start()
    webcam_thread.start()

    screen_thread.join()
    webcam_thread.join()

    messagebox.showinfo("Session Done", "Your session recordings have been saved.")

def on_start():
    try:
        minutes = int(entry.get())
        if minutes <= 0:
            raise ValueError
        start_button.config(state="disabled")
        threading.Thread(target=start_session, args=(minutes,), daemon=True).start()
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid number of minutes.")

app = tk.Tk()
app.title("Productivity Recorder")
app.geometry("300x150")

label = tk.Label(app, text="Session Length (minutes):")
label.pack(pady=10)

entry = tk.Entry(app)
entry.pack()

start_button = tk.Button(app, text="Start Session", command=on_start)
start_button.pack(pady=20)

app.mainloop()
