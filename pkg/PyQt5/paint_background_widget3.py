# -*- coding: utf-8 -*-
# QWidget 배경 그리기 예제 3
# make hbesthee@naver.com
# date 2023-12-12

import sys
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QToolButton, QWidget, QVBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, QSize, QRect, QMetaObject
from PyQt5.QtGui import QImage, QPainter, QMouseEvent
from queue import Queue
from time import sleep


class BackgroundVideoThread(QThread):
	""" 배경을 그려줄 동영상을 로딩하는 스레드 """
	changeFrame = pyqtSignal()

	def __init__(self, frame_queue: Queue):
		super().__init__()
		self._frame_queue = frame_queue


	def run(self):
		# OpenCV를 사용하여 비디오 캡처 객체를 생성합니다.
		cap = cv2.VideoCapture(r'D:\Temp\1654.mp4')
		while True:
			ret, frame = cap.read()
			if ret:
				# OpenCV에서 가져온 프레임을 QImage로 변환합니다.
				rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
				h, w, ch = rgbImage.shape
				bytesPerLine = ch * w
				# 시그널을 통해 메인 스레드에 QImage 객체를 전달합니다.
				new_frame = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
				try:
					self._frame_queue.get_nowait() # 기존에 남아 있는 프레임 제거
				except:
					pass
				self._frame_queue.put(new_frame)
				self.changeFrame.emit()
				sleep(0.033)

class QBackgroundVideoWidget(QWidget):
	def __init__(self, parent: QWidget):
		super().__init__(parent)
		self._queue: Queue = Queue(1)
		self._bg_image: QImage = None
		self.initUI()
		self.thread = BackgroundVideoThread(self._queue)
		self.thread.changeFrame.connect(self.setFrame)
		self.thread.start()

	def initUI(self):
		self.setGeometry(300, 300, 400, 300)
		self.setWindowTitle('OpenCV 프레임 예제')
		self.show()

	def paintEvent(self, event):
		if (not self._queue.empty()):
			self._bg_image = self._queue.get()

		if (self._bg_image == None):
			super().paintEvent(event)
			return
		painter = QPainter()
		painter.begin(self)
		# QPainter를 사용하여 위젯의 배경에 이미지를 그립니다.
		painter.drawImage(self.rect(), self._bg_image)
		painter.end()

	def setFrame(self):
		self.update()


class Ui_MainWindow(QMainWindow):

	def mousePressEvent(self, a0: QMouseEvent | None) -> None:
		self.lblTime.setText(f'clicked: {a0.x()=} / {a0.y()=} / {a0.globalX()=} / {a0.globalY()=}')
		self.widgetTop.setVisible(not self.widgetTop.isVisible())
		return super().mouseMoveEvent(a0)


	def setupUi(self, MainWindow: QMainWindow):
		if not MainWindow.objectName():
			MainWindow.setObjectName(u"MainWindow")
		MainWindow.resize(706, 568)
		self.central = QBackgroundVideoWidget(MainWindow)
		self.central.setObjectName(u"central")
		self.verticalLayout = QVBoxLayout(self.central)
		self.verticalLayout.setSpacing(0)
		self.verticalLayout.setObjectName(u"verticalLayout")
		self.verticalLayout.setContentsMargins(0, 0, 0, 0)
		self.widgetTop = QWidget(self.central)
		self.widgetTop.setObjectName(u"widgetTop")
		self.widgetTop.setMinimumSize(QSize(0, 30))
		self.widgetTop.setMaximumSize(QSize(16777215, 30))
		self.toolButton = QToolButton(self.widgetTop)
		self.toolButton.setObjectName(u"toolButton")
		self.toolButton.setGeometry(QRect(10, 10, 27, 18))
		self.toolButton_2 = QToolButton(self.widgetTop)
		self.toolButton_2.setObjectName(u"toolButton_2")
		self.toolButton_2.setGeometry(QRect(50, 10, 27, 18))
		self.toolButton_3 = QToolButton(self.widgetTop)
		self.toolButton_3.setObjectName(u"toolButton_3")
		self.toolButton_3.setGeometry(QRect(90, 10, 27, 18))

		self.verticalLayout.addWidget(self.widgetTop)

		self.verticalSpacer = QSpacerItem(30, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

		self.verticalLayout.addItem(self.verticalSpacer)

		self.widgetStatus = QWidget(self.central)
		self.widgetStatus.setObjectName(u"widgetStatus")
		self.widgetStatus.setMinimumSize(QSize(0, 20))
		self.widgetStatus.setMaximumSize(QSize(16777215, 20))
		self.lblTime = QLabel(self.widgetStatus)
		self.lblTime.setObjectName(u"lblTime")
		self.lblTime.setGeometry(QRect(2, 2, 150, 12))

		self.verticalLayout.addWidget(self.widgetStatus)

		MainWindow.setCentralWidget(self.central)

		self.retranslateUi(MainWindow)

		QMetaObject.connectSlotsByName(MainWindow)
	# setupUi

	def retranslateUi(self, MainWindow: QMainWindow):
		MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"BlackBoxMainWindow", None))
		self.toolButton.setText(QCoreApplication.translate("MainWindow", u"...", None))
		self.toolButton_2.setText(QCoreApplication.translate("MainWindow", u"...", None))
		self.toolButton_3.setText(QCoreApplication.translate("MainWindow", u"...", None))
		self.lblTime.setText("")
	# retranslateUi


	def initUI(self) -> None:
		self.setupUi(self)

		self.widgetTop.setVisible(False)
		self.setMouseTracking(False)


if __name__ == '__main__':
	app = QApplication(sys.argv)
	mainWindow = Ui_MainWindow()
	mainWindow.initUI()
	mainWindow.show()
	sys.exit(app.exec_())
