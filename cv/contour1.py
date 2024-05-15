# contour demo 1
# make hbesthee@naver.com
# date 2024-05-15

from os import getcwd, listdir

import cv2 as cv
import numpy as np


images_path = f'{getcwd()}\\images'
print(f'{images_path=}')
file_list = listdir(images_path)


for filename in file_list:
	image_file = f'{images_path}\\{filename}'
	print(f'{image_file=}')
	# img_color = cv.imread(image_file)
	# img is in BGR format if the underlying image is a color image
	img_color = cv.imdecode(np.fromfile(image_file, dtype=np.uint8), cv.IMREAD_UNCHANGED)
	img_gray = cv.cvtColor(img_color, cv.COLOR_BGR2GRAY)
	ret, img_binary = cv.threshold(img_gray, 127, 255, 0)
	contours, hierarchy = cv.findContours(img_binary, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)


	for cnt in contours:
		cv.drawContours(img_color, [cnt], 0, (255, 0, 0), 3)  # blue

	cv.imshow("result", img_color)

	cv.waitKey(0)


	for cnt in contours:

		x, y, w, h = cv.boundingRect(cnt)
		cv.rectangle(img_color, (x, y), (x + w, y + h), (0, 255, 0), 2)


	cv.imshow("result", img_color)

	cv.waitKey(0)



	for cnt in contours:

		rect = cv.minAreaRect(cnt)
		box = cv.boxPoints(rect)
		box = np.int0(box)
		cv.drawContours(img_color,[box],0,(0,0,255),2)


	cv.imshow("result", img_color)

	cv.waitKey(0)