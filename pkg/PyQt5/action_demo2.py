# -*- coding: utf-8 -*-
# 액션 처리 예시
# date	2023-06-20
# author	hbesthee@naver.com

from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QPushButton

app = QApplication([])

# QMainWindow를 기반으로한 위젯 생성
main_window = QMainWindow()

action = QAction("Action", main_window) # QAction 생성

button = QPushButton("Click me", main_window) # QPushButton 생성
button.setGeometry(QRect(20, 28, 90, 25))

# QPushButton의 clicked 시그널과 람다 함수를 연결하여 QAction의 triggered 이벤트를 호출
button.clicked.connect(lambda: action.trigger())

# QAction의 triggered 시그널과 연결할 이벤트 핸들러 함수 정의
def handle_action():
	print("Action triggered!")

# QAction의 triggered 시그널과 이벤트 핸들러 함수를 연결
action.triggered.connect(handle_action)

main_window.menuBar().addAction(action) # 메뉴 바에 QAction 추가

main_window.show() # 위젯을 화면에 표시
app.exec_()