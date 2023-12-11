# QWidget 배경 그리기 예제 1
# make hbesthee@naver.com
# date 2023-12-11

import cv2
import sys
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QPen

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 400, 400)
        self.setWindowTitle('QtWidget 배경 그리기')
        self.show()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.drawBackground(qp)
        qp.end()

    def drawBackground(self, qp):
        qp.setPen(QColor(255, 255, 255))  # 흰색 펜 설정
        qp.setBrush(QColor(255, 20, 20))  # 붉은색 브러시 설정
        qp.drawRect(self.rect())  # 위젯 전체에 사각형 그리기

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    sys.exit(app.exec_())