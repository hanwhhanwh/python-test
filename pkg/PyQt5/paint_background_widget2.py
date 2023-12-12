# QWidget 배경 그리기 예제 2
# make hbesthee@naver.com
# date 2023-12-11

import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPainter
from queue import Queue
from time import sleep


class VideoThread(QThread):
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

class App(QWidget):
	def __init__(self):
		super().__init__()
		self._queue: Queue = Queue(1)
		self._bg_image: QImage = None
		self.initUI()
		self.thread = VideoThread(self._queue)
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


if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = App()
	sys.exit(app.exec_())
