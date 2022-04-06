# blackbox example (threading)
# date: 2022-04-04
# make: hbesthee@naver.com

from _queue import Empty
from multiprocessing import Queue
from threading import Thread
from typing import Final

import cv2
import time

CAMERA_ID: Final		= 0
FRAME_WIDTH: Final		= 640
FRAME_HEIGTH: Final		= 480


class VideoWriterThread(Thread):
	""" 영상 프레임 저장 스레드 """

	def __init__(self, video_file_name, video_codec = 'XVID', fps = 30, frame_size = (640, 480)) -> None:
		""" 생성자 """

		super(VideoWriterThread, self).__init__(name = self.__class__.__name__)

		self._out_file_name = video_file_name
		self._video_codec = video_codec
		self._fps = fps
		self._frame_size = frame_size
		# Define the codec and create VideoWriter object.
		self._out = cv2.VideoWriter(video_file_name, cv2.VideoWriter_fourcc(*video_codec), fps, frame_size)
		self._q = Queue() # 스레드간 동기화 처리를 위한 multiprocessing.Queue 객체


	def run(self):
		""" 스레드 실행부 """
		self._stopped = False
		prev_time = 0
		total_frames = 0
		start_time = time.time()

		while ( (self._stopped == False) and (self._out != None) ):
			curr_time = time.time()
			try:
				frame = self._q.get()
				total_frames = total_frames + 1

				term = curr_time - prev_time
				fps = 1 / term
				prev_time = curr_time
				fps_string = f'term = {term:.3f},  FPS = {fps:.2f}'
				print(fps_string)

				cv2.putText(frame, fps_string, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255))

				# Write the frame into the file (VideoWriter)
				# if (frame != None):
				self._out.write(frame)
			except Exception as e:
				if (isinstance(e, Empty) == False): # 실제 오류 발생
					print('queue error :', e)

		end_time = time.time()
		fps = total_frames / (start_time - end_time)
		print(f'total_frames = {total_frames},  avg FPS = {fps:.2f}')

		if (self._out != None):
			self._out.release()


	def stop(self):
		self._stopped = True
		self._q.put(None)


	def write(self, frame):
		self._q.put(frame)


if __name__ == '__main__':
	capture = cv2.VideoCapture(CAMERA_ID)
	if capture.isOpened() == False: # 카메라 정상상태 확인
		print(f'Can\'t open the Camera({CAMERA_ID})')
		exit()

	capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
	capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGTH)

	writer_thread = VideoWriterThread('output.mp4', frame_size = (FRAME_WIDTH, FRAME_HEIGTH))
	writer_thread.start()

	while cv2.waitKey(1) < 0:

		ret, frame = capture.read()

		# Write the frame into the file (VideoWriter)
		# out.write(frame)
		writer_thread.write(frame)

		time.sleep(0.01)

		cv2.imshow("VideoFrame", frame)

	writer_thread.stop()

	capture.release()
	cv2.destroyAllWindows()
