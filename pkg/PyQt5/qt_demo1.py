# Qt demo 1
# date	2023-02-15
# author	hbesthee@naver.com

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import sys


class TestProgressDialog(QDialog):
	def __init__(self):
		super(TestProgressDialog, self).__init__()
		self.setupUi(self)


	def setupUi(self, Dialog):
		if not Dialog.objectName():
			Dialog.setObjectName(u"Dialog")
		Dialog.resize(393, 368)
		self.groupBox = QGroupBox(Dialog)
		self.groupBox.setObjectName(u"groupBox")
		self.groupBox.setGeometry(QRect(10, 150, 371, 161))
		self.pbProgress = QProgressBar(self.groupBox)
		self.pbProgress.setObjectName(u"pbProgress")
		self.pbProgress.setGeometry(QRect(10, 80, 361, 16))
		self.pbProgress.setMaximum(16)
		self.pbProgress.setValue(4)
		self.btnAutoStart = QPushButton(self.groupBox)
		self.btnAutoStart.setObjectName(u"btnAutoStart")
		self.btnAutoStart.setGeometry(QRect(10, 20, 100, 30))
		self.btnAutoStop = QPushButton(self.groupBox)
		self.btnAutoStop.setObjectName(u"btnAutoStop")
		self.btnAutoStop.setGeometry(QRect(240, 20, 100, 30))
		self.label_5 = QLabel(self.groupBox)
		self.label_5.setObjectName(u"label_5")
		self.label_5.setGeometry(QRect(10, 60, 321, 16))
		self.label_6 = QLabel(self.groupBox)
		self.label_6.setObjectName(u"label_6")
		self.label_6.setGeometry(QRect(10, 110, 321, 16))
		self.pbProgress_2 = QProgressBar(self.groupBox)
		self.pbProgress_2.setObjectName(u"pbProgress_2")
		self.pbProgress_2.setGeometry(QRect(10, 130, 361, 16))
		self.pbProgress_2.setMaximum(41)
		self.pbProgress_2.setValue(12)
		self.btnClose = QPushButton(Dialog)
		self.btnClose.setObjectName(u"btnClose")
		self.btnClose.setGeometry(QRect(140, 330, 100, 30))
		self.groupBox_2 = QGroupBox(Dialog)
		self.groupBox_2.setObjectName(u"groupBox_2")
		self.groupBox_2.setGeometry(QRect(10, 10, 371, 61))
		self.label = QLabel(self.groupBox_2)
		self.label.setObjectName(u"label")
		self.label.setGeometry(QRect(20, 20, 151, 16))
		self.label_2 = QLabel(self.groupBox_2)
		self.label_2.setObjectName(u"label_2")
		self.label_2.setGeometry(QRect(190, 20, 141, 16))
		self.groupBox_3 = QGroupBox(Dialog)
		self.groupBox_3.setObjectName(u"groupBox_3")
		self.groupBox_3.setGeometry(QRect(10, 80, 371, 61))
		self.label_3 = QLabel(self.groupBox_3)
		self.label_3.setObjectName(u"label_3")
		self.label_3.setGeometry(QRect(20, 30, 85, 12))
		self.label_4 = QLabel(self.groupBox_3)
		self.label_4.setObjectName(u"label_4")
		self.label_4.setGeometry(QRect(240, 30, 35, 12))
		self.lineEdit = QLineEdit(self.groupBox_3)
		self.lineEdit.setObjectName(u"lineEdit")
		self.lineEdit.setEnabled(True)
		self.lineEdit.setGeometry(QRect(110, 25, 81, 20))
		self.lineEdit.setReadOnly(True)
		self.lineEdit_2 = QLineEdit(self.groupBox_3)
		self.lineEdit_2.setObjectName(u"lineEdit_2")
		self.lineEdit_2.setEnabled(True)
		self.lineEdit_2.setGeometry(QRect(280, 25, 51, 20))
		self.lineEdit_2.setReadOnly(True)

		self.retranslateUi(Dialog)

		QMetaObject.connectSlotsByName(Dialog)

		self.btnClose.clicked.connect(self.close_progress)


	def retranslateUi(self, Dialog):
		Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"\uc790\ub3d9\ud654 \uc9c4\ud589 \uc0c1\ud0dc - \uc804\ub2e8\uc99d\ud3ed\ubaa8\ub4c8", None))
		self.groupBox.setTitle(QCoreApplication.translate("Dialog", u"\uc790\ub3d9\ud654", None))
		self.btnAutoStart.setText(QCoreApplication.translate("Dialog", u"\uc2dc\uc791", None))
		self.btnAutoStop.setText(QCoreApplication.translate("Dialog", u"\uc911\uc9c0", None))
		self.label_5.setText(QCoreApplication.translate("Dialog", u"Channel 4 / \uc218\uc9c1", None))
		self.label_6.setText(QCoreApplication.translate("Dialog", u"Freq : 18.5GHz  (\uc9c1\uc804 \uce21\uc815 : 18.0GHz / -32.53)", None))
		self.btnClose.setText(QCoreApplication.translate("Dialog", u"닫기(&C)", None))
		self.groupBox_2.setTitle(QCoreApplication.translate("Dialog", u"\uc2dc\ud5d8 \ub300\uc0c1 \uc815\ubcf4", None))
		self.label.setText(QCoreApplication.translate("Dialog", u"\ub300\uc5ed3\uc804\ub2e8\uc99d\ud3ed\ubaa8\ub4c8", None))
		self.label_2.setText(QCoreApplication.translate("Dialog", u"\uc2dc\ud5d8\uc885\ub958 : \ud558\ubaa8\ub2c9", None))
		self.groupBox_3.setTitle(QCoreApplication.translate("Dialog", u"\ubaa8\ub4c8 \uc815\ubcf4", None))
		self.label_3.setText(QCoreApplication.translate("Dialog", u"CCA \uc77c\ub828\ubc88\ud638 :", None))
		self.label_4.setText(QCoreApplication.translate("Dialog", u"\uc628\ub3c4 : ", None))
		self.lineEdit.setInputMask(QCoreApplication.translate("Dialog", u"123", None))
		self.lineEdit_2.setText(QCoreApplication.translate("Dialog", u"22.25", None))


	def close_progress(self):
		self.close()


if __name__ == '__main__':
	# from os import environ
	from PyQt5 import QtWidgets, QtCore, QtGui #pyqt stuff

	def processAmpModule():
		dlgAmpModule = TestProgressDialog()
		dlgAmpModule.exec()

	# environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'  # 모니터 해상도에 따른 폰트 및 컨트롤 크기 자동 조정
	QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
	QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons

	app = QApplication(sys.argv)
	button = QPushButton("전단증폭모듈 자동화")
	button.clicked.connect(processAmpModule)
	button.show()
	app.exec_()