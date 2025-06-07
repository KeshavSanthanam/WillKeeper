# main.py (PyQt5 version)
import sys
import threading
import time
import os
import json
import datetime
import cv2
import numpy as np
import pyautogui
import mss
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QDateTimeEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QTimer, Qt, QDateTime

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

    threading.Thread(target=record_screen, args=(screen_path,), daemon=True).start()
    threading.Thread(target=record_webcam, args=(webcam_path,), daemon=True).start()

class RecorderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(500)

    def init_ui(self):
        self.setWindowTitle("Productivity Recorder")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.label_task = QLabel("Task Description:")
        self.entry_task = QLineEdit()

        self.label_start = QLabel("Allowed Start:")
        self.datetime_start = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_start.setCalendarPopup(True)
        self.datetime_start.setDisplayFormat("yyyy-MM-dd HH:mm")

        self.label_end = QLabel("Allowed End:")
        self.datetime_end = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_end.setCalendarPopup(True)
        self.datetime_end.setDisplayFormat("yyyy-MM-dd HH:mm")

        self.label_timer = QLabel("Recorded: 0s")

        self.btn_start = QPushButton("Start Recording")
        self.btn_start.clicked.connect(self.on_start)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.clicked.connect(self.on_pause)
        self.btn_pause.setEnabled(False)

        self.btn_resume = QPushButton("Resume")
        self.btn_resume.clicked.connect(self.on_resume)
        self.btn_resume.setEnabled(False)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.on_stop)
        self.btn_stop.setEnabled(False)

        for w in [self.label_task, self.entry_task, self.label_start, self.datetime_start,
                  self.label_end, self.datetime_end, self.btn_start, self.btn_pause,
                  self.btn_resume, self.btn_stop, self.label_timer]:
            layout.addWidget(w)

        self.setLayout(layout)

    def update_timer(self):
        if recording and not stop_event.is_set():
            self.label_timer.setText(f"Recorded: {int(recorded_seconds)}s")

    def on_start(self):
        desc = self.entry_task.text()
        start = self.datetime_start.dateTime().toString("yyyy-MM-dd HH:mm")
        end = self.datetime_end.dateTime().toString("yyyy-MM-dd HH:mm")
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_resume.setEnabled(False)
        threading.Thread(target=start_session, args=(desc, start, end), daemon=True).start()

    def on_pause(self):
        pause_event.set()
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(True)

    def on_resume(self):
        pause_event.clear()
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)

    def on_stop(self):
        stop_event.set()
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.btn_stop.setEnabled(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RecorderApp()
    window.show()
    sys.exit(app.exec_())
