# contour demo 3
# make hbesthee@naver.com
# date 2024-05-22

from os import getcwd, listdir, path

import cv2 as cv
import numpy as np


images_path = r'D:\Dev\VisionAI\ABN2\images'
labels_path = r'D:\Dev\VisionAI\ABN2\labels'

limit_angle = 1.0

print(f'{images_path=}')
file_list = listdir(images_path)


file_count, contour_count = 0, 0
for filename in file_list:
	file_count += 1
	if (file_count % 1000 == 0):
		print(f'{file_count=} processed...')

	image_file = f'{images_path}\\{filename}'
	# print(f'{image_file=}')
	# img is in BGR format if the underlying image is a color image
	img_color = cv.imdecode(np.fromfile(image_file, dtype=np.uint8), cv.IMREAD_UNCHANGED)
	img_height, img_width, img_channel = img_color.shape
	img_extent_limit = (img_height * img_width) * 0.15
	img_gray = cv.cvtColor(img_color, cv.COLOR_BGR2GRAY)
	ret, img_binary = cv.threshold(img_gray, 127, 255, 0)
	contours, hierarchy = cv.findContours(img_binary, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

	for cnt in contours:
		x, y, w, h = cv.boundingRect(cnt)
		cv.rectangle(img_color, (x, y), (x + w, y + h), (0, 255, 0), 1)

		# 가장 크고 가운데 부분을 차지하는 바운딩 박스를 찾음
		#   규칙 : w가 h의 2배 이상 / 전체 면적의 20% 이상 / 중앙 점이 화면 중앙에서 10% 이내에 있어야 함
		if ( (h << 1) > w ): # w가 h의 2배 이상
			continue

		if ( (w * h) < img_extent_limit ): # 전체 면적의 20% 이상
			continue

		margin_t, margin_b = y, img_height - y - h
		margin_l, margin_r = x, img_width - x - w
		if (margin_t == 0 and margin_b == 0):
			continue
		if (margin_l == 0 and margin_r == 0):
			continue
		
		rect = cv.minAreaRect(cnt)
		# 사각형의 각도 계산
		angle = (rect[-1] % 90)
		angle = angle if (angle < 45) else 90 - angle
		if (angle > limit_angle):
			continue

		# 결과 시각화
		box = cv.boxPoints(rect)
		box = np.int0(box)
		cv.drawContours(img_color, [box], 0, (0, 0, 255), 1)
		cv.putText(img_color, f'angle = {angle:.2f}', (0, 30), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv.LINE_AA)

		cv.imshow("result", img_color)
		cv.waitKey(0)
		break

print(f'total: {file_count=} / found: {contour_count=}')
