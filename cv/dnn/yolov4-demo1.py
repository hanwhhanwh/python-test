# Yolo v4 example (threading)
# date: 2022-04-12
# make: hbesthee@naver.com
 
import cv2
import time

CONFIDENCE_THRESHOLD = 0.2
NMS_THRESHOLD = 0.4
COLORS = [(0, 255, 255), (255, 255, 0), (0, 255, 0), (255, 0, 0)]

CAMERA_ID = 0
FRAME_WIDTH = 640
FRAME_HEIGTH = 480

capture = cv2.VideoCapture(CAMERA_ID)
if capture.isOpened() == False: # 카메라 정상상태 확인
	print(f'Can\'t open the Camera({CAMERA_ID})')
	exit()

capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGTH)



class_names = []
with open("classes.txt", "r") as f:
	class_names = [cname.strip() for cname in f.readlines()]

# net = cv2.dnn.readNet("yolov4.weights", "yolov4.cfg")
net = cv2.dnn.readNet("yolov4-tiny.weights", "yolov4-tiny.cfg")
# net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
# net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)

model = cv2.dnn_DetectionModel(net)
model.setInputParams(size=(416, 416), scale=1/255, swapRB=True)

while cv2.waitKey(1) < 1:
	(grabbed, frame) = capture.read()
	if not grabbed:
		print('camera error!')
		exit()

	start = time.time()
	classes, scores, boxes = model.detect(frame, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
	end = time.time()

	start_drawing = time.time()
	for (classid, score, box) in zip(classes, scores, boxes):
		if (score < 0.5):
			continue
		color = COLORS[int(classid) % len(COLORS)]
		label = "%s : %.2f" % (class_names[classid[0]], score)
		cv2.rectangle(frame, box, color, 2)
		cv2.putText(frame, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
	end_drawing = time.time()
	
	#fps_label = "FPS: %.2f (excluding drawing time of %.2fms)" % (1 / (end - start), (end_drawing - start_drawing) * 1000)
	fps_label = "FPS: %.2f" % (1 / (end - start) )
	cv2.putText(frame, fps_label, (0, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
	cv2.imshow("detections", frame)
