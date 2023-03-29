# Qt demo width QThread
# date	2023-03-29
# author	hbesthee@naver.com

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import sys


class LoginDialog(QDialog):

	def __init__(self):
		super(LoginDialog, self).__init__()
		self.setupUi()


	def setupUi(self):
		self.setWindowTitle("Login Dialog")
		self.resize(254, 113)
		self.verticalLayout = QVBoxLayout(self)
		self.gridLayout = QGridLayout()

		self.label = QLabel(self)
		self.label.setText("ID :")
		self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

		self.lineEdit = QLineEdit(self)
		self.gridLayout.addWidget(self.lineEdit, 0, 1, 1, 1)

		self.label_2 = QLabel(self)
		self.label_2.setText("Password :")
		self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)

		self.lineEdit_2 = QLineEdit(self)
		self.gridLayout.addWidget(self.lineEdit_2, 2, 1, 1, 1)

		self.lbTimer = QLabel(self)
		self.lbTimer.setText("10 seconds remain...")
		self.gridLayout.addWidget(self.lbTimer, 3, 1, 1, 1)

		self.verticalLayout.addLayout(self.gridLayout)

		self.buttonBox = QDialogButtonBox(self)
		self.buttonBox.setObjectName(u"buttonBox")
		self.buttonBox.setOrientation(Qt.Horizontal)
		self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

		self.verticalLayout.addWidget(self.buttonBox)


	def closeDialog(self):
		self.done(0)


	@pyqtSlot(int)
	def handleTimer(self, sec):
		self.lbTimer.setText(f"{sec} seconds remain...")
		if (sec == 0):
			self.done(0)


class LoginTimer(QThread):
	timer_signal = pyqtSignal(int)

	def __init__(self, parent: QDialog = None, sec: int = 10) -> None:
		super().__init__()
		self._parent = parent
		self._sec = sec
		self._is_stopped = False
		self.timer_signal.connect(parent.handleTimer)


	def run(self) -> None:
		while (not self._is_stopped):
			self.timer_signal.emit(self._sec)
			self.sleep(1)

			self._sec -= 1
			if (self._sec == 0):
				break

		self.timer_signal.emit(self._sec)
		print("thread end")

if __name__ == '__main__':
	# from os import environ
	from PyQt5 import QtWidgets, QtCore, QtGui #pyqt stuff

	def openLoginDialog():
		loginDialog = LoginDialog()
		thread = LoginTimer(loginDialog, 15)
		thread.start()
		loginDialog.exec()

	# environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'  # 모니터 해상도에 따른 폰트 및 컨트롤 크기 자동 조정
	QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
	QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons

	app = QApplication(sys.argv)
	button = QPushButton("Login")
	button.clicked.connect(openLoginDialog)
	button.show()
	app.exec_()
	print("end")