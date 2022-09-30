# Yolo v4 example (threading)
# date: 2022-04-12
# make: hbesthee@naver.com
 
import cv2
import time

CONFIDENCE_THRESHOLD = 0.6
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

capture = cv2.VideoCapture(CAMERA_ID)
if capture.isOpened() == False: # 카메라 정상상태 확인
	print(f'Can\'t open the Camera({CAMERA_ID})')
	exit()

capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGTH)



class_names = []
with open("classes.txt", "r") as f:
	class_names = [cname.strip() for cname in f.readlines()]

# 네트워크 설정 : YoloV4 / YoloV4-tiny
# net = cv2.dnn.readNet("yolov4.weights", "yolov4.cfg")
net = cv2.dnn.readNet("yolov4-tiny.weights", "yolov4-tiny.cfg")
# net = cv2.dnn.readNet("yolov7-tiny.weights", "yolov7-tiny.cfg")

# 백엔드 설정 : CUDA (CPU) / NCS2
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)
# net.setPreferableBackend(cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE)
# net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)

model = cv2.dnn_DetectionModel(net)
model.setInputParams(size=(NETWORK_SIZE, NETWORK_SIZE), scale=1/255, swapRB=True)

cv2.namedWindow(WOINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(WOINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
print(f'getWindowImageRect() = {cv2.getWindowImageRect(WOINDOW_NAME)}')
# windowWidth = cv2.getWindowImageRect(WOINDOW_NAME)[2]
# windowHeight = cv2.getWindowImageRect(WOINDOW_NAME)[3]

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
		if ( hasattr(classid, "__len__") and hasattr(classid, '__getitem__') ):
			classid = int(classid)
		if (classid > 4):
			continue
		color = COLORS[int(classid) % len(COLORS)]
		label = "%s : %.2f" % (class_names[classid], score)
		cv2.rectangle(frame, box, color, 2)
		cv2.putText(frame, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
	end_drawing = time.time()
	
	#fps_label = "FPS: %.2f (excluding drawing time of %.2fms)" % (1 / (end - start), (end_drawing - start_drawing) * 1000)
	fps_label = "FPS: %.2f" % (1 / (end - start) )
	cv2.putText(frame, fps_label, (0, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
	cv2.imshow(WOINDOW_NAME, cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGTH)))

capture.release()
cv2.destroyAllWindows()
