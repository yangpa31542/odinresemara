import sys
import cv2
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox, QTextEdit
from PyQt5.QtCore import Qt, QTimer
import win32gui
import pyautogui
import numpy as np
import keyboard


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 윈도우 창 설정
        self.setWindowTitle("오딘 리세마라 v0.1")
        self.setGeometry(800, 600, 320, 400)
        self.setStyleSheet("background-color: #333333")

        # 버튼 및 체크박스 생성
        self.start_button = QPushButton("동작", self)
        self.pause_button = QPushButton("일시정지(home)", self)
        self.stop_button = QPushButton("중지", self)
        self.checkbox_50 = QCheckBox("50 리세", self)
        self.checkbox_60 = QCheckBox("60 리세", self)
        self.checkbox_70 = QCheckBox("70 리세", self)

        # 버튼 및 체크박스 레이아웃 설정
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.checkbox_50)
        checkbox_layout.addWidget(self.checkbox_60)
        checkbox_layout.addWidget(self.checkbox_70)

        # 버튼 스타일 설정
        self.start_button.setStyleSheet("background-color: #FF0000; color: #FFFFFF;")
        self.pause_button.setStyleSheet("background-color: #00FF00; color: #000000;")
        self.stop_button.setStyleSheet("background-color: #0000FF; color: #FFFFFF;")

        # 전체 레이아웃 설정
        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addLayout(checkbox_layout)

        # Log viewer
        self.log_viewer = QTextEdit()
        self.log_viewer.setFixedSize(310, 300)
        log_layout = QVBoxLayout()
        log_layout.addWidget(self.log_viewer)
        main_layout.addLayout(log_layout)
        self.log_viewer.setStyleSheet("background-color: #000000; color: #FFFFFF;")

        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)
        self.setStyleSheet("QLabel { color: #FFFFFF; }")

        # 버튼 클릭 이벤트 연결
        self.start_button.clicked.connect(self.start)
        self.pause_button.clicked.connect(self.pause)
        self.stop_button.clicked.connect(self.stop)

        # 이미지 인식에 사용할 이미지 파일 경로 설정
        self.image_files = ["./img/qfi1.png", 
                            "./img/qfi2.png", 
                            "./img/qfi3.png", 
                            "./img/qde.png", 
                            "./img/qst.png", 
                            "./img/qst2.png",
                             "./img/skip.png", 
                             "./img/fmove.png", 
                             "./img/qjump.png",
                             "./img/qok.png",
                              ]

        # 이미지 인식 범위 설정
        self.screen_width = 960
        self.screen_height = 510

        # 이미지 인식 성공 기준 설정
        self.match_threshold = 0.75

        # 이미지 인식 타이머
        self.timer = QTimer()
        self.timer.setInterval(500)  # 0.5초 딜레이 설정
        self.timer.timeout.connect(self.check_images)

        # 일시정지 상태
        self.paused = False

    def start(self):
        self.update_log("동작 시작")
        # ODIN 타이틀 윈도우 창 찾기
        hwnd = self.find_odin_window()
        if hwnd is None:
            self.update_log("ODIN을 찾을 수 없습니다.")
            return

        # ODIN 타이틀 윈도우 크기 및 위치 조정
        self.adjust_window_size(hwnd)

        # 이미지 인식 타이머 시작
        self.timer.start(1000)

    def find_odin_window(self):
        # 모든 윈도우 핸들 검색
        def callback(hwnd, extra):
            # ODIN  ,UnrealWindow
            if win32gui.GetWindowText(hwnd) == "ODIN  ":
                extra.append(hwnd)

        windows = []
        win32gui.EnumWindows(callback, windows)

        if len(windows) > 0:
            self.update_log("ODIN 창이 발견되었습니다.")
            return windows[0]
        else:
            return None

    def adjust_window_size(self, hwnd):
        # ODIN 타이틀 윈도우 크기 및 위치 조정
        # spy 에서 크기 974x547
        win32gui.MoveWindow(hwnd, 0, 0, 974, 547, True)
        self.update_log("ODIN 창 크기 및 위치 조정")

    def check_images(self):
        # 일시정지 상태일 경우 무시
        if self.paused:
            return

        # 화면 캡처
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 이미지 인식 및 클릭
        for image_file in self.image_files:
            image = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE) # Grayscale로 이미지 읽기
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY) # Screenshot을 Grayscale로 변환
            result = cv2.matchTemplate(screenshot_gray, image, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= self.match_threshold)

            for pt in zip(*locations[::-1]):
                x, y = pt[0] + image.shape[1] // 2, pt[1] + image.shape[0] // 2  # 중간지점 클릭
                pyautogui.click(x, y)
                self.update_log(f"이미지 {image_file} 인식, 클릭 위치: ({x}, {y})")

        # 체크박스 체크 여부 확인
        if self.checkbox_50.isChecked() or self.checkbox_60.isChecked() or self.checkbox_70.isChecked():
            # 자동 정지
            self.pause()

        # 체크박스 체크 여부에 따라 동작 종료
        if self.checkbox_50.isChecked():
            if self.check_image_match("./img/q50.png"):
                self.stop()
                self.update_log("50레벨 달성, 동작 종료")
        if self.checkbox_60.isChecked():
            if self.check_image_match("./img/q60.png"):
                self.stop()
                self.update_log("60레벨 달성, 동작 종료")
        if self.checkbox_70.isChecked():
            if self.check_image_match("./img/q70.png"):
                self.stop()
                self.update_log("70레벨 달성, 동작 종료")

    def check_image_match(self, image_file):
        # 화면 캡처
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 이미지 인식
        image = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE) # Grayscale로 이미지 읽기
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY) # Screenshot을 Grayscale로 변환
        result = cv2.matchTemplate(screenshot_gray, image, cv2.TM_CCOEFF_NORMED)

        # 일치 여부 확인
        if np.max(result) >= self.match_threshold:
            self.update_log(f"이미지 {image_file} 일치 확인")
            return True
        else:
            return False

    def pause(self):
        self.paused = not self.paused
        if self.paused:
            self.update_log("일시정지")
            self.pause_button.setText("재개(home)")
        else:
            self.update_log("재개")
            self.pause_button.setText("일시정지(home)")

    def stop(self):
        self.timer.stop()
        self.update_log("동작 종료")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Home:
            self.pause()
        elif event.key() == Qt.Key_End:
            self.stop()
            self.close()

    def update_log(self, message):
        self.log_viewer.append(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
