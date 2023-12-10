# Fullscreen example 1
# make hbesthee@naver.com
# date 2023-12-10

#from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Fullscreen Window")
		# ... 기타 초기화 코드 ...

	def bringToFront(self):
		self.activateWindow()
		self.raise_()

# 애플리케이션 실행
app = QApplication([])
main_window = MainWindow()
#main_window.show()
#main_window.bringToFront()
#main_window.setWindowState(main_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
main_window.showFullScreen()
app.exec_()
