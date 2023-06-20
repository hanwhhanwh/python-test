# -*- coding: utf-8 -*-
# 위젯 닫기 이벤트 처리 예시 2
# date	2023-06-20
# author	hbesthee@naver.com

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QEvent

class MyWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.installEventFilter(self)  # 이벤트 필터 등록

	def eventFilter(self, obj, event):
		if event.type() == QEvent.Close:
			# 필요한 처리 작업 수행
			# 예: 데이터 저장, 리소스 해제 등
			print(f'QEvent.Close')
			event.accept()  # 위젯을 닫음
			return True

		return super().eventFilter(obj, event)

# 예시 실행 코드
app = QApplication([])
widget = MyWidget()
widget.show()
app.exec_()
