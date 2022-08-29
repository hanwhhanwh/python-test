# YoloX example
# date: 2022-08-25
# make: hbesthee@naver.com

import cv2
import time
import numpy as np

CONFIDENCE_THRESHOLD = 0.7
NMS_THRESHOLD = 0.4
# NETWORK_SIZE = 416
NETWORK_SIZE = 288
COLORS = [(0, 255, 255), (255, 255, 0), (0, 255, 0), (255, 0, 0)]

CAMERA_ID = 0
FRAME_WIDTH = 640
FRAME_HEIGTH = 480
SCREEN_WIDTH = 1920
SCREEN_HEIGTH = 1080

WOINDOW_NAME = 'Detections'

# capture = cv2.VideoCapture(CAMERA_ID)
# capture = cv2.VideoCapture('C:/Temp/yeonsu/20220531/video/cam-20220510_0332.mp4')
capture = cv2.VideoCapture('C:/Temp/yeonsu/20220510/cam-20220510_0332.mp4')
if capture.isOpened() == False: # 카메라 정상상태 확인
	print(f'Can\'t open the Camera({CAMERA_ID})')
	exit()

capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGTH)



class_names = []
with open("classes.txt", "r") as f:
	class_names = [cname.strip() for cname in f.readlines()]

# 네트워크 설정 : YoloX / YoloX-tiny
net = cv2.dnn.readNet("yolox_tiny.onnx")

# 백엔드 설정 : CUDA (CPU) / NCS2
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)
# net.setPreferableBackend(cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE)
# net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)


cv2.namedWindow(WOINDOW_NAME, cv2.WINDOW_NORMAL)
# cv2.setWindowProperty(WOINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
print(f'getWindowImageRect() = {cv2.getWindowImageRect(WOINDOW_NAME)}')
# windowWidth = cv2.getWindowImageRect(WOINDOW_NAME)[2]
# windowHeight = cv2.getWindowImageRect(WOINDOW_NAME)[3]

while cv2.waitKey(1) < 1:
	(grabbed, frame) = capture.read()
	if not grabbed:
		print('camera error!')
		exit()

	start = time.time()
	# Prepare input blob and perform an inference
	blob = cv2.dnn.blobFromImage(cv2.resize(frame, (NETWORK_SIZE, NETWORK_SIZE)), size=(NETWORK_SIZE, NETWORK_SIZE), swapRB=True)
	net.setInput(blob)

	# classes, scores, boxes = model.detect(frame, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
	outputs = net.forward()

	boxes = list()
	class_ids = list()
	confidences = list()
	for output in outputs:
		for detections in output:
			scores = detections[5:] #80개 클래스 확률값 
			class_id = np.argmax(scores) #80개 클래스 중에서 가장 최대값을 가지는 확률값의 인덱스
			if ( not (class_id in [0, 2]) ):
				continue
			confidence = scores[class_id]
			if (confidence > CONFIDENCE_THRESHOLD):
				# map the class id to the class
				class_name = class_names[int(class_id)-1]
				color = (0, 255, 255) # COLORS[int(class_id)]
				# get the bounding box width and height
				box_width = int(detections[2] * FRAME_WIDTH)
				box_height = int(detections[3] * FRAME_HEIGTH)
				# get the bounding box coordinates
				box_x = int(detections[0] * FRAME_WIDTH - box_width / 2)
				box_y = int(detections[1] * FRAME_HEIGTH - box_height / 2)

				boxes.append([box_x, box_y, box_width, box_height])
				class_ids.append(int(class_id))
				confidences.append(float(confidence))
	indices = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
	end = time.time()

	for idx in indices: #각 객체당 선별된 박스가 for loop를 통해 정보 추출
		# print(i)
		i = idx
		sx, sy, bw, bh = boxes[i]
		label = f'{class_names[class_ids[i]]}: {confidences[i]:.2}'
		color = (0, 255, 255)
		cv2.rectangle(frame, (sx, sy, bw, bh), color, 2)
		cv2.putText(frame, label, (sx, sy - 10),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)

	#getPerfProfile: 실행시간 계산에 관련된 함수  
	t, _ = net.getPerfProfile()
	label = 'Inference time: %.2f ms' % (t * 1000.0 / cv2.getTickFrequency())
	cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
				0.7, (0, 0, 255), 1, cv2.LINE_AA)

	# start_drawing = time.time()
	# for (classid, score, box) in zip(classes, scores, boxes):
	# 	if ( hasattr(classid, "__len__") and hasattr(classid, '__getitem__') ):
	# 		classid = int(classid)
	# 	if (classid > 4):
	# 		continue
	# 	color = COLORS[int(classid) % len(COLORS)]
	# 	label = "%s : %.2f" % (class_names[classid], score)
	# 	cv2.rectangle(frame, box, color, 2)
	# 	cv2.putText(frame, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
	# end_drawing = time.time()
	
	#fps_label = "FPS: %.2f (excluding drawing time of %.2fms)" % (1 / (end - start), (end_drawing - start_drawing) * 1000)
	fps_label = "FPS: %.2f" % (1 / (end - start) )
	cv2.putText(frame, fps_label, (0, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
	# cv2.imshow(WOINDOW_NAME, cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGTH)))
	cv2.imshow(WOINDOW_NAME, frame)

capture.release()
cv2.destroyAllWindows()
