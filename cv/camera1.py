# camera capture example
# date: 2022-04-04
# make: hbesthee@naver.com

import cv2
import numpy as np


capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)

while cv2.waitKey(1) < 0:
	ret, frame = capture.read()
	cv2.imshow("VideoFrame", frame)

capture.release()
cv2.destroyAllWindows()
