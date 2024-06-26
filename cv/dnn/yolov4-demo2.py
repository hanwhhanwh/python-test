# YoloV4 example (multi-processing)
# date: 2022-04-13
# make: hbesthee@naver.com

from _queue import Empty
from multiprocessing import Process, Queue
from os import getpid, name, makedirs
from threading import Thread
# from typing import Final

import cv2
import time


if (__name__ == '__main__'):
	import sys
	from os import path
	print( path.abspath('../..') )
	# sys.path.append(path.dirname( path.dirname( path.abspath(__file__) ) ))
	sys.path.append( path.abspath('../..') )

from lib.file_logger import createLogger


CONFIDENCE_THRESHOLD = 0.6
NMS_THRESHOLD = 0.4
# NETWORK_SIZE = 416
NETWORK_SIZE = 288
COLORS = [(0, 255, 255), (255, 255, 0), (0, 255, 0), (255, 0, 0)]

CAMERA_ID			= 0
FRAME_WIDTH			= 640
FRAME_HEIGTH		= 480

WOINDOW_NAME = 'Detections'


_frame = None # 메인 프로세스 및 스레드간 공유를 위한 영상 프레임 전역 변수

_class_names = [] # 객체 클래스 이름
_frame_q = Queue() # 프로세스간 영상 프레임 공유를 위한 큐
_detections_q = Queue() # 프로세스간 객체 인식 결과 공유를 위한 큐



def clear_queue(queue):
	""" 큐를 초기화합니다. """
	while(not queue.empty()):
		_ = queue.get()


class YoloDetector(Process):
	""" Yolo detector class """

	def __init__(self, frame_q, detections_q
			, confidence_threshold = CONFIDENCE_THRESHOLD
			, nms_threshold = NMS_THRESHOLD
			, backend = cv2.dnn.DNN_BACKEND_CUDA
			, target = cv2.dnn.DNN_TARGET_CUDA_FP16
			, yolo_version = 4, is_tiny = True
			, network_size = NETWORK_SIZE ) -> None:
		""" YoloDetector class 생성자\n
			frame_q 프로세스간 영상 프레임 공유를 위한 큐\n
			detections_q 프로세스간 객체 인식 결과 공유를 위한 큐\n
			backend : or cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE = NCS2\n
			target : or cv2.dnn.DNN_TARGET_MYRIAD = NCS2
		"""
		super(YoloDetector, self).__init__(name = self.__class__.__name__)

		self._frame_q = frame_q
		self._detections_q = detections_q

		self._confidence_threshold = confidence_threshold
		self._nms_threshold = nms_threshold
		self._yolo_version = yolo_version
		self._is_tiny = is_tiny
		self._backend = backend
		self._target = target
		self._network_size = network_size


	def init_model(self):

		# 네트워크 설정 : YoloV4 / YoloV4-tiny
		# net = cv2.dnn.readNet("yolov4.weights", "yolov4.cfg")
		# self._net = cv2.dnn.readNet("./data/yolov4-tiny.weights", "./data/yolov4-tiny.cfg")
		self._net = cv2.dnn.readNet("yolov4-tiny.weights", "yolov4-tiny.cfg")

		# 백엔드 설정 : CUDA (CPU) / NCS2
		# net.setPreferableBackend(cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE)
		# net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)
		self._net.setPreferableBackend(self._backend)
		self._net.setPreferableTarget(self._target)

		self._model = cv2.dnn_DetectionModel(self._net)
		self._model.setInputParams(size = (self._network_size, self._network_size), scale=1/255, swapRB=True)


	def run(self):
		""" Yolo detector 실행부 """
		
		self._detection_log = createLogger(log_filename = 'detection', log_level = 20)
		self._detection_log.info(f'Yolo detector started. PID = {getpid()}')

		self.init_model()
		prev_time = time.time()
		processed_frame_count = 0
		while (True):
			frame, frame_index = self._frame_q.get()

			if (frame_index == -2):
				break

			# 객체 인식 처리
			start_time = time.time()
			classes, scores, boxes = self._model.detect(frame, self._confidence_threshold, self._nms_threshold)
			end_time = time.time()
			processed_frame_count += 1
			inference_time = end_time - prev_time
			if (inference_time > 60):
				self._detection_log.info(f'Inference Time = {inference_time:.1f}  /  processed_frame_count = {processed_frame_count}  /  Inference FPS = {(processed_frame_count / inference_time):0.3f}')
				prev_time = end_time
				processed_frame_count = 0

			# 객체 인식 결과 정보를 공유
			detections = dict()
			detections['frame_index'] = frame_index
			detections['classes'] = classes
			detections['scores'] = scores
			detections['boxes'] = boxes
			detections['start_time'] = start_time
			detections['end_time'] = end_time
			clear_queue(self._detections_q)
			self._detections_q.put(detections)


	def stop(self):
		""" Yolo detector 프로세스 종료 처리 """
		clear_queue(self._frame_q)
		self._frame_q.put((None, -2))


class VideoWriterThread(Thread):
	""" 영상 프레임 저장 스레드 """

	def __init__(self, video_file_name, video_codec = 'XVID', fps = 30, frame_size = (640, 480)) -> None:
		""" 생성자 """

		super(VideoWriterThread, self).__init__(name = self.__class__.__name__)

		self._out_file_name = video_file_name
		self._video_codec = video_codec
		self._fps = fps
		self._frame_size = frame_size
		self._q = Queue() # 스레드간 동기화 처리를 위한 multiprocessing.Queue 객체


	def run(self):
		""" 스레드 실행부 """
		self._stopped = False
		global _frame
		self._writer_log = createLogger(log_filename = 'video_writer', log_level = 20)
		self._writer_log.info(f'VideoWriterThread started.')

		# Define the codec and create VideoWriter object.
		# self._out = cv2.VideoWriter(video_file_name, cv2.VideoWriter_fourcc(*video_codec), fps, frame_size)
		video_file_name = self._out_file_name
		gstream_pipeline_string = f'appsrc ! videoconvert ! video/x-raw ! x264enc tune=zerolatency bitrate=1024 speed-preset=fast ! mp4mux ! filesink location={video_file_name}'
		if (name == 'posix'):
			gstream_pipeline_string = f'appsrc ! autovideoconvert ! v4l2h264enc ! video/x-h264,level=(string)4 ! h264parse ! mp4mux ! filesink location={video_file_name}'
		self._out = cv2.VideoWriter(gstream_pipeline_string, cv2.CAP_GSTREAMER, 0, self._fps, self._frame_size)

		prev_time = time.time()
		frame_count = 0
		while ( (self._stopped == False) and (self._out != None) ):
			try:
				_ = self._q.get()

				# Write the frame into the file (VideoWriter)
				self._out.write(_frame)
				frame_count += 1
				end_time = time.time()
				process_time = end_time - prev_time
				if (process_time > 60):
					self._writer_log.info(f'Writing time = {process_time:.1f}  /  frame_count = {frame_count}  /  writer FPS = {(frame_count / process_time):0.3f}')
					prev_time = end_time
					frame_count = 0
			except Exception as e:
				self._writer_log.exception(e)
				if (isinstance(e, Empty) == False): # 실제 오류 발생
					print('queue error :', e)

		if (self._out != None):
			self._out.release()


	def stop(self):
		self._stopped = True
		self._q.put(None)


	def write(self, frame):
		self._q.put(frame)


def draw_detections(frame):
	""" _detections_q에 공유된 객체 인식 결과 정보를 주어진 영상 프레임에 그려줍니다. """

	if (_detections_q.empty()):
		return # 객체 인식 결과가 없음

	try:
		detections = _detections_q.get(False)
	except Empty as e:
		return

	_detections_q.put(detections) # 다시 큐에 공유함 ; 다음 프레임에서도 동일한 객체 인식 결과 표시
	classes = detections.get('classes')
	scores = detections.get('scores')
	boxes = detections.get('boxes')
	start_time = detections.get('start_time')
	end_time = detections.get('end_time')
	for (classid, score, box) in zip(classes, scores, boxes):
		if ( hasattr(classid, "__len__") and hasattr(classid, '__getitem__') ):
			classid = int(classid)
		if (classid > 4):
			continue
		color = COLORS[int(classid) % len(COLORS)]
		label = "%s : %.2f" % (_class_names[classid], score)
		cv2.rectangle(frame, box, color, 2)
		cv2.putText(frame, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

	infernece_time = end_time - start_time
	fps_label = f"infernece time: {infernece_time:.3f}  /  infernece FPS: {(1 / (infernece_time)):.3f}"
	cv2.putText(frame, fps_label, (0, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

if (__name__ == '__main__'):
	is_windows = (name == 'nt')
	camera_id = CAMERA_ID
	if (not is_windows):
		camera_id = -1
	capture = cv2.VideoCapture(CAMERA_ID)
	if capture.isOpened() == False: # 카메라 정상상태 확인
		print(f'Can\'t open the Camera({CAMERA_ID})')
		exit()

	if (not path.exists('./logs')):
		makedirs('./logs')

	capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
	capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGTH)

	backend = cv2.dnn.DNN_BACKEND_CUDA
	target = cv2.dnn.DNN_TARGET_CUDA
	if (not is_windows):
		backend = cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE
		target = cv2.dnn.DNN_TARGET_MYRIAD
	# detector = YoloDetector(_frame_q, _detections_q)
	detector = YoloDetector(_frame_q, _detections_q
		, backend = backend
		, target = target
	)
	detector.start()

	writer_thread = VideoWriterThread('output.mp4', video_codec = 'H264', frame_size = (FRAME_WIDTH, FRAME_HEIGTH))
	writer_thread.start()

	with open("classes.txt", "r") as f:
		_class_names = [cname.strip() for cname in f.readlines()]

	frame_index = 0
	while cv2.waitKey(1) < 0:

		ret, _frame = capture.read()
		frame_index += 1
		try: # 객체 감지용 영상 프레임이 있을 경우 기존 프레임 삭제
			_ = _frame_q.get(False)
		except:
			pass
		_frame_q.put((_frame, frame_index)) # 계속 새로운 영상 프레임을 공유해줌

		draw_detections(_frame)
		writer_thread.write(1)

		if ( (is_windows) or (False) ):
			cv2.imshow(WOINDOW_NAME, _frame)

	detector.stop()
	writer_thread.stop()

	capture.release()
	cv2.destroyAllWindows()
