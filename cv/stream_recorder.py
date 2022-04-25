# StreamRecorder class
# date: 2022-04-24
# make: hbesthee@naver.com

from _queue import Empty
from datetime import datetime
from glob import glob
from multiprocessing import Process, Queue
from shutil import disk_usage
from struct import pack
# from typing import Final
from threading import Thread

import cv2
import io
import os
import time
import traceback


RECORD_PER_10MIN		= 60
RECORD_PER_30MIN		= 1800
RECORD_PER_HOUR			= 3600
RECORD_PER_2HOUR		= 7200


def do_guarentee_space(recording_path, guarentee_space = 4) -> None:
	""" 영상 저장 폴더에 대하여, 디스크 여유 공간 확보 작업을 수행합니다. 
		디스크의 공간이 부족한 경우, 오래된 영상부터 순차적으로 삭제합니다.
		recording_path : 영상 저장 폴더
		guarentee_space : 확보할 디스크 여유 공간의 크기값 ; 기본 4GB
	"""
	_, _, free = disk_usage(recording_path)
	guarentee_size = guarentee_space * (2 ** 30)
	if (free < guarentee_size ):
		# 여유공간 확보를 위하여, 영상 파일을 삭제 처리함

		file_list = glob(f'{recording_path}/*.mp4')
		file_list.sort() # 이름순 정렬
		for file_name in file_list:
			# file_basename = os.path.basename(file_name)
			file_size = os.path.getsize(file_name)
			os.remove(file_name)
			print(f'deleted file : {file_name} : {file_size:,}')
			free += file_size
			if (free > guarentee_size ):
				break


class StreamRecorder(Process):
	""" 스트림 영상 프레임 저장 프로세스 """

	def __init__(self, video_file_name, video_codec = 'XVID', fps = 30, frame_size = (640, 480)) -> None:
		""" 생성자 """

		super(StreamRecorder, self).__init__(name = self.__class__.__name__)

		self._frame_index = 0 # 영상 프레임 순번
		self._recording_path = './video' # 영상 저장 경로
		self._recording_term = RECORD_PER_10MIN # 1시간 단위로 파일을 쪼개 저장 처리

		self._out_file_name = video_file_name # 영상 파일 접두어
		self._video_codec = video_codec # 영상 코텍 ; window에서만 의미가 있음
		self._fps = fps # 영상 저장 프레임
		self._frame_size = frame_size # 영상 크기

		self._q = Queue() # 영상 저장 프로세스와 다른 프로세스간 간 동기화 처리를 위한 multiprocessing.Queue 객체
		self._out = None # 영상 저장 객체 (내부용)


	def preprocess_frame(self, frame) -> None:
		""" 프레임에 대한 영상 처리가 필요한 경우, override하여 영상을 처리 로직을 작성합니다. """

		pass


	def run(self):
		""" 영상 저장 프로세스 실행부 """
		if (not os.path.exists(self._recording_path)):
			os.makedirs(self._recording_path) # 영상 저장 폴더가 없으면 생성

		video_file_name = ''
		total_frame = 0
		start_time = time.time()		
		prev_time = 0
		video_index_file = None
		while ( True ):
			try:
				frame, frame_index = self._q.get()

				if (frame_index == -2):
					break

				current_time = time.time()
				if ( (self._recording_term > 0) and (start_time + self._recording_term) < current_time ):
					if (self._out != None):
						self._out.release()
					if (video_index_file != None):
						video_index_file.close()
					self._out = None
					prev_time = start_time
					start_time = current_time

				try:
					if ( (self._out == None) ):
						fps = (total_frame / (current_time - prev_time))
						print(f'fps [{video_file_name}] = {fps:.3f}')
						start_time = current_time
						total_frame = 0

						# Define the codec and create VideoWriter object.
						video_file_name = f'{self._recording_path}/{self._out_file_name}-{datetime.now().strftime("%Y%m%d_%H%M")}.mp4'
						if (os.name == "nt"):
							self._out = cv2.VideoWriter(video_file_name, cv2.VideoWriter_fourcc(*self._video_codec), self._fps, self._frame_size)
						elif (os.name == "posix"):
							self._out = cv2.VideoWriter(f'appsrc ! videoconvert ! video/x-raw ! x264enc tune=zerolatency bitrate=1024 speed-preset=2 ! mp4mux ! filesink location={video_file_name}'
								, cv2.CAP_GSTREAMER, 0, self._fps, self._frame_size)
							# speed-preset = 2 (superfast)
						video_index_file = open(f'{video_file_name}.idx', 'wb')
				except Exception as ex:
					video_index_file = None
					errors = io.StringIO()
					traceback.print_exc(file=errors)
					contents = str(errors.getvalue())
					print(contents)
					errors.close()

				self.preprocess_frame(frame) # 영상 처리

				self._out.write(frame) # 영상 저장
				video_index_file.write(pack('i', frame_index)) # 영상 프레임 인덱스 정보 저장
				total_frame += 1
			except Exception as e:
				if (frame_index == -2):
					break

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
			self._out = None


	def set_recording_path(self, recording_path) -> None:
		""" 영상 저장 폴더를 설정합니다. """
		self._recording_path = recording_path
		if (not os.path.exists(self._recording_path)):
			os.makedirs(self._recording_path) # 영상 저장 폴더가 없으면 생성


	def stop(self) -> None:
		""" 프로세스를 종료합니다. """
		self._q.put((None, -2))


	def write(self, frame, frame_index = -1) -> int:
		""" 저장할 영상 프레임을 기록합니다. """
		try:
			_ = self._q.get(False) # 남아 있는 영상 프레임을 제거합니다.
		except:
			pass
		self._q.put((frame, frame_index))


if __name__ == '__main__':
	CAMERA_ID			= 0
	FRAME_WIDTH			= 640
	FRAME_HEIGTH		= 480


	def do_guarentee_space_thread_handler(recording_path, guarentee_space) -> None:
		while (True):
			do_guarentee_space(recording_path, guarentee_space)
			time.sleep(1800) # 30분 동안 대기

	capture = cv2.VideoCapture(CAMERA_ID)
	if capture.isOpened() == False: # 카메라 정상상태 확인
		print(f'Can\'t open the Camera({CAMERA_ID})')
		exit()

	capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
	capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGTH)

	recorder_process = StreamRecorder('output', video_codec = 'mp4v'
		, frame_size = (FRAME_WIDTH, FRAME_HEIGTH))

	recording_path = os.getcwd() + '/video'
	recorder_process.set_recording_path(recording_path)
	recorder_process.start()

	guarentee_space = 23 # 최소 확보 용량 (단위 : GB)
	guarentee_space_thread = Thread(target = do_guarentee_space_thread_handler
		, args = (recording_path, guarentee_space))
	guarentee_space_thread.start()

	total_frame = 0
	while cv2.waitKey(1) < 0:

		ret, frame = capture.read()
		total_frame += 1

		# Write the frame into the StreamRecorder
		recorder_process.write(frame, total_frame)

		if (os.name == "nt"):
			cv2.imshow("VideoStream", frame)

	recorder_process.stop()
	recorder_process.join()
	guarentee_space_thread.join()

	capture.release()
	if (os.name == "nt"):
		cv2.destroyAllWindows()
