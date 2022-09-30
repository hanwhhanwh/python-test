# blackbox example
# date: 2022-04-04
# make: hbesthee@naver.com

import cv2
import time

CAMERA_ID = 0
FRAME_WIDTH = 640
FRAME_HEIGTH = 480

capture = cv2.VideoCapture(CAMERA_ID)
if capture.isOpened() == False: # 카메라 정상상태 확인
	print(f'Can\'t open the Camera({CAMERA_ID})')
	exit()

capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGTH)

# Define the codec and create VideoWriter object. The output is stored in 'output.mp4' file.
# out = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'XVID'), 30, (FRAME_WIDTH, FRAME_HEIGTH))
gstream_pipeline_string = f'appsrc ! videoconvert ! v4l2h264enc ! video/x-h264,level=(string)4 ! h264parse ! mp4mux ! filesink location=out.mp4'
out = cv2.VideoWriter(gstream_pipeline_string, cv2.CAP_GSTREAMER, 0, 30, (FRAME_WIDTH, FRAME_HEIGTH))

prev_time = 0
total_frames = 0
start_time = time.time()
while cv2.waitKey(1) < 0:
	curr_time = time.time()

	ret, frame = capture.read()
	total_frames = total_frames + 1

	# Write the frame into the file (VideoWriter)
	out.write(frame)

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

out.release()
capture.release()
cv2.destroyAllWindows()
