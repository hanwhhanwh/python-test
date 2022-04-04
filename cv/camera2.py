# camera capture example (with fps)
# date: 2022-04-04
# make: hbesthee@naver.com

import cv2 as cv2
import time

CAMERA_ID = 0

capture = cv2.VideoCapture(CAMERA_ID)
if capture.isOpened() == False: # 카메라 정상상태 확인
	print(f'Can\'t open the Camera({CAMERA_ID})')
	exit()

capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)

prev_time = 0
total_frames = 0
start_time = time.time()
while cv2.waitKey(1) < 0:
	curr_time = time.time()

	ret, frame = capture.read()
	total_frames = total_frames + 1

	term = curr_time - prev_time
	fps = 1 / term
	prev_time = curr_time
	fps_string = f'term = {term:.3f},  FPS = {fps:.2f}'
	print(fps_string)

	cv2.putText(frame, fps_string, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255))
	cv2.imshow("VideoFrame", frame)

end_time = time.time()
fps = total_frames / (start_time - end_time)
print(f'total_frames = {total_frames},  avg FPS = {fps:.2f}')

capture.release()
cv2.destroyAllWindows()
