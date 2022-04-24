# StreamRecorder class
# date: 2022-04-24
# make: hbesthee@naver.com

from _queue import Empty
from datetime import datetime
from multiprocessing import Process, Queue
from typing import Final

import cv2
import io
import os
import time
import traceback


RECORD_PER_10MIN: Final		= 600
RECORD_PER_30MIN: Final		= 1800
RECORD_PER_HOUR: Final		= 3600
RECORD_PER_2HOUR: Final		= 7200



class StreamRecorder(Process):
	""" 스트림 영상 프레임 저장 프로세스 """

	def __init__(self, video_file_name, video_codec = 'XVID', fps = 30, frame_size = (640, 480)) -> None:
		""" 생성자 """

		super(StreamRecorder, self).__init__(name = self.__class__.__name__)

		self._out_file_name = video_file_name
		self._recording_term = RECORD_PER_10MIN # 1시간 단위로 파일을 쪼개 저장 처리
		self._video_codec = video_codec
		self._fps = fps
		self._frame_size = frame_size
		self._frame_index = 0
		self._q = Queue() # 영상 저장 프로세스와 다른 프로세스간 간 동기화 처리를 위한 multiprocessing.Queue 객체
		self._out = None


	def preprocess_frame(self, frame) -> None:
		""" 프레임에 대한 영상 처리가 필요한 경우, override하여 영상을 처리 로직을 작성합니다. """

		pass


	def run(self):
		""" 영상 저장 프로세스 실행부 """
		self._stopped = False
		start_time = time.time()
		while ( True ):
			try:
				frame, frame_index = self._q.get()

				if (self._stopped):
					break

				current_time = time.time()
				if ( (self._recording_term > 0) and (start_time + self._recording_term) < current_time ):
					if (self._out != None):
						self._out.release()
					self._out = None
					start_time = current_time

				try:
					if ( (self._out == None) ):
						# Define the codec and create VideoWriter object.
						video_file_name = self._out_file_name + '-' + datetime.now().strftime('%Y%m%d_%H%M') + '.mp4'
						if (os.name == "nt"):
							self._out = cv2.VideoWriter(video_file_name, cv2.VideoWriter_fourcc(*self._video_codec), self._fps, self._frame_size)
						elif (os.name == "posix"):
							self._out = cv2.VideoWriter(f'appsrc ! videoconvert ! video/x-raw ! x264enc tune=zerolatency bitrate=1024 speed-preset=superfast ! mp4mux ! filesink location={video_file_name}'
								, cv2.CAP_GSTREAMER, 0, self._fps, self._frame_size)
						start_time = time.time()
				except Exception as ex:
					errors = io.StringIO()
					traceback.print_exc(file=errors)
					contents = str(errors.getvalue())
					print(contents)
					errors.close()

				self.preprocess_frame(frame) # 영상 처리

				self._out.write(frame) # 영상 저장
			except Exception as e:
				if (isinstance(e, Empty) == False): # 실제 오류 발생
					print('recorder error :', e)
					try:
						self._out.release()
					except Exception as ex:
						errors = io.StringIO()
						traceback.print_exc(file=errors)
						contents = str(errors.getvalue())
						print(contents)
						errors.close()
					self._out = None

		if (self._out != None):
			self._out.release()


	def stop(self):
		""" 프로세스를 종료합니다. """
		self._stopped = True
		self._q.put(None)


	def write(self, frame, frame_index = -1) -> int:
		""" 저장할 영상 프레임을 기록합니다. """
		try:
			_ = self._q.get(False) # 남아 있는 영상 프레임을 제거합니다.
		except:
			pass
		self._q.put((frame, frame_index))


if __name__ == '__main__':
	CAMERA_ID: Final		= 0
	FRAME_WIDTH: Final		= 640
	FRAME_HEIGTH: Final		= 480


	capture = cv2.VideoCapture(CAMERA_ID)
	if capture.isOpened() == False: # 카메라 정상상태 확인
		print(f'Can\'t open the Camera({CAMERA_ID})')
		exit()

	capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
	capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGTH)

	recorder_process = StreamRecorder('output', frame_size = (FRAME_WIDTH, FRAME_HEIGTH))
	recorder_process.start()

	while cv2.waitKey(1) < 0:

		ret, frame = capture.read()

		# Write the frame into the file (VideoWriter)
		# out.write(frame)
		recorder_process.write(frame)

		time.sleep(0.02)

		cv2.imshow("VideoStream", frame)

	recorder_process.stop()

	capture.release()
	cv2.destroyAllWindows()
