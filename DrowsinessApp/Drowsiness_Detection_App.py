import sys
import os
import cv2
from pygame import mixer 
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,
    QHBoxLayout, QFrame, QSizePolicy, QSpacerItem, QMessageBox, QToolButton
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSize
from PyQt5.QtGui import QImage, QPixmap, QFont, QIcon
from ultralytics import YOLO

# -------------------- Function to get correct file paths --------------------
def resource_path(relative_path):
    """ Get the correct path for files whether running as exe or python script """
    try:
        # If running as exe
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# -------------------- Initialize audio mixer --------------------
mixer.init()

# -------------------- Video processing thread --------------------
class VideoThread(QThread):
    # Convert image 
    change_pixmap_signal = pyqtSignal(QImage)
    status_signal = pyqtSignal(str, int, bool)  # label_name, drowsy_counter, alarm_active

    def __init__(self, model, labels_dict, window_size=30):
        super().__init__()
        self.model = model
        self.labels_dict = labels_dict
        self.window_size = window_size
        self.running = False
        self.cap = None
        self.drowsy_counter = 0
        self.alert_triggered = False
        
        # Load alarm sound file
        try:
            mixer.music.load(resource_path("alarm.mp3"))
        except Exception as e:
            print(f"Error loading alarm.mp3: {e}")

    def run(self):
        self.cap = cv2.VideoCapture(0)
        
        self.running = True
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            input_frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            results = self.model.predict(input_frame, verbose=False)
            label_index = int(results[0].probs.top1)
            label_name = self.labels_dict.get(label_index, "unknown")

            # Variable to track alarm state
            alarm_is_active = False

            if label_name == "drowsy":
                self.drowsy_counter += 1
            else:
                self.drowsy_counter = 0
                self.alert_triggered = False
                try:
                    mixer.music.stop()
                except:
                    pass

            # Activate alarm only when threshold is exceeded
            if self.drowsy_counter >= self.window_size and not self.alert_triggered:
                try:
                    mixer.music.play(-1)
                except Exception as e:
                    print(f"Error playing alarm: {e}")
                self.alert_triggered = True
            
            # Determine if alarm is currently active
            if self.drowsy_counter >= self.window_size:
                alarm_is_active = True

            # Show the frame on the screen to user
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.change_pixmap_signal.emit(qimg)
            # Send alarm state with data
            self.status_signal.emit(label_name, self.drowsy_counter, alarm_is_active)

        if self.cap is not None:
            self.cap.release()

# -------------------- Main interface --------------------
class DrowsinessApp(QWidget):
    def __init__(self):
        super().__init__()
        # Title 
        self.setWindowTitle("Drowsiness Detection System")
        # Window size
        self.setMinimumSize(950, 900)

        # Load model
        self.model = YOLO(resource_path("best.pt"))
        self.labels_dict = {0: 'absent', 1: 'awake', 2: 'drowsy'}

        self.create_ui()

        # Create thread at the beginning
        self.thread = VideoThread(self.model, self.labels_dict, window_size=30)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.status_signal.connect(self.update_status)

    def create_ui(self):
        # ------------ Header title ------------
        title = QLabel("Drowsiness Detection System")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 25, QFont.Bold))
        title.setObjectName("title_label")

        # ------------ Logo ----------------
        logo = QLabel()
        logo.setObjectName("logo_label")
        pixmap = QPixmap(resource_path("images/logo.jpeg"))  
        pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)

        # ------------ Info Button ------------
        info_btn = QToolButton()
        info_btn.setIcon(QIcon(resource_path("images/info_icon.png")))
        info_btn.setIconSize(QSize(40, 40))
        info_btn.setToolTip("About Drowsiness Detection System")
        info_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                color: white;
                font-size: 18px;
            }
            QToolButton:hover {
                color: #a8c8ff;
            }
        """)
        info_btn.clicked.connect(self.show_info_dialog)

        # ------------ Header Layout ------------
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background:#0e5f8a;
                border-radius: 8px;
                padding: 12px;
            }
            QLabel#title_label {
                color: white;  // color of title 
            }
        """)

        header_layout = QHBoxLayout()
        header_layout.addWidget(logo)
        header_layout.addSpacing(10)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(info_btn)
        # add all elements in one hedear layout
        header_frame.setLayout(header_layout)

        # ------------ Video area ------------
        self.video_label = QLabel()
        self.video_label.setStyleSheet("background: #2b3240; border-radius: 8px;")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("Click Start to begin detection")
        self.video_label.setStyleSheet("color: #9fb3c8; background:#1f2a36; border-radius:10px;")
        self.video_label.setMinimumSize(720, 420)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ------------ Status bar under video ------------
        # Driver state
        status_label = QLabel("Current Status:")
        status_label.setFont(QFont("Arial", 10))
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(16, 16)
        self.status_dot.setStyleSheet("background: #808080; border-radius:8px;")
        self.status_text = QLabel("Inactive")
        self.status_text.setFont(QFont("Arial", 11))
        self.status_text.setStyleSheet("color: #0078d7; font-weight: bold;")


        # Camera state
        detection_label = QLabel("Detection Mode:")
        detection_label.setFont(QFont("Arial", 10))
        self.mode_text = QLabel("Inactive")
        self.mode_text.setFont(QFont("Arial", 11))
        self.mode_text.setStyleSheet("color: #0078d7; font-weight: bold;")

        # Put together in layout
        status_row = QHBoxLayout()
        status_row.addWidget(status_label)
        status_row.addWidget(self.status_dot)
        status_row.addSpacing(8)
        status_row.addWidget(self.status_text)
        status_row.addStretch()
        status_row.addWidget(detection_label)
        status_row.addWidget(self.mode_text)

        status_frame = QFrame()
        status_frame.setStyleSheet("background: #f4f7f9; border-radius:8px; padding:12px;")
        status_frame.setLayout(status_row)

        # ------------ Buttons ------------
        self.start_btn = QPushButton("▶ Start Detection")
        self.stop_btn = QPushButton("◼ Stop Detection")
        self.start_btn.setStyleSheet("QPushButton{background:#16a3ab; color:white; padding:10px 22px; border-radius:8px;} QPushButton:hover{background:#13b3bb;}")
        self.stop_btn.setStyleSheet("QPushButton{background:#bdbdbd; color:#444; padding:10px 22px; border-radius:8px;} QPushButton:hover{background:#d32f2f; color:white;}")
        self.stop_btn.setEnabled(False)

        # Actions
        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn.clicked.connect(self.on_stop)

        # Layout
        btn_layout = QHBoxLayout()
        btn_layout.addSpacerItem(QSpacerItem(40, 20))
        btn_layout.addWidget(self.start_btn)
        btn_layout.addSpacing(12)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addSpacerItem(QSpacerItem(40, 20))

        # ------------ Footer ------------
        footer = QLabel("Real-time drowsiness monitoring system • Built with computer vision ")
        footer.setStyleSheet("color: #6b7a85;")
        footer.setAlignment(Qt.AlignCenter)

        # ------------ Main layout (contains everything) ------------
        main_layout = QVBoxLayout()# vertial 
        main_layout.addWidget(header_frame)
        main_layout.addSpacing(12)
        main_layout.addWidget(self.video_label, stretch=1)
        main_layout.addSpacing(12)
        main_layout.addWidget(status_frame)
        main_layout.addSpacing(12)
        main_layout.addLayout(btn_layout)
        main_layout.addSpacing(8)
        main_layout.addWidget(footer)
        main_layout.setContentsMargins(12, 12, 12, 12)
        self.setLayout(main_layout)# integrate everythings

    # ------------ Show Info Dialog ------------
    def show_info_dialog(self):
        info = QMessageBox(self)
        info.setWindowTitle("About Drowsiness Detection System")
        info.setIcon(QMessageBox.Information)
        info.setTextFormat(Qt.RichText)
        info.setText("""
        <h3>Drowsiness Detection System</h3>
        <p>An app designed to keep drivers safe by monitoring alertness and delivering instant warnings when signs of drowsiness are detected.</p><br>
        <b>Purpose:</b>
        <p>To support safer driving and reduce the risk of accidents caused by fatigue.</p><br>
        <b>Model:</b>
        <p>YOLO Nano v11-class</p><br>
       
        <i>Drive Safe • Stay Alert • Save Lives</i>
        """)
        info.setStandardButtons(QMessageBox.Ok)
        info.exec_()

    # ------------ Start/Stop Logic ------------
    def on_start(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.mode_text.setText("Active")

        if not self.thread.isRunning():
            self.thread = VideoThread(self.model, self.labels_dict, window_size=30)
            self.thread.change_pixmap_signal.connect(self.update_image)
            self.thread.status_signal.connect(self.update_status)

        self.thread.start()

    def on_stop(self):
        self.stop_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.mode_text.setText("Inactive")

        if self.thread.isRunning():
            self.thread.running = False
            self.thread.wait()

        try:
            self.thread.change_pixmap_signal.disconnect(self.update_image)
            self.thread.status_signal.disconnect(self.update_status)
        except TypeError:
            pass

        try:
            mixer.music.stop()
        except:
            pass

        self.video_label.clear()
        self.video_label.setText("Click Start to begin detection")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("color: #9fb3c8; background:#1f2a36; border-radius:10px;")
        self.status_text.setText("Inactive")
        self.status_dot.setStyleSheet("background: #808080; border-radius:8px;")
        self.status_text.setStyleSheet("color: #0078d7; font-weight: bold;")

        self.thread.drowsy_counter = 0
        self.thread.alert_triggered = False
        self.thread.running = False

    def update_image(self, qimg):
        if not self.thread.running:
            return
        pix = QPixmap.fromImage(qimg)
        scaled = pix.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled)

    def update_status(self, label_name, counter, alarm_active):
        """
        Status update logic:
        1. Green LED when face is present (awake or drowsy before threshold)
        2. Red LED only when absent
        3. "Drowsy" text turns red when alarm is triggered (after threshold)
        4. Status changes to Drowsy only when threshold is exceeded
        """
        
        if label_name == "absent":
            # Red LED - Face not detected
            self.status_text.setText("Face not detected")
            self.status_text.setStyleSheet("color: #e67e22; font-weight: bold;")
            self.status_dot.setStyleSheet("background: #e74c3c; border-radius:8px;")
        
        elif label_name == "awake":
            # Green LED - Person is awake
            self.status_text.setText("Awake")
            self.status_text.setStyleSheet("color: #2ecc71; font-weight: bold;")
            self.status_dot.setStyleSheet("background: #2ecc71; border-radius:8px;")
        
        elif label_name == "drowsy":
            # Green LED - Face is present (before reaching threshold)
            self.status_dot.setStyleSheet("background: #2ecc71; border-radius:8px;")
            
            if alarm_active:
                # After threshold - Text turns red and status changes to Drowsy
                self.status_text.setText(" DROWSY - ALERT")
                self.status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")
            else:
                # Before threshold - Status remains Awake (but model detected drowsy)
                self.status_text.setText("Awake")
                self.status_text.setStyleSheet("color: #2ecc71; font-weight: bold;")

# ------------ Main ------------
def main():
    app = QApplication(sys.argv)
    win = DrowsinessApp()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

    

