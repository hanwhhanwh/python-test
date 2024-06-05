# 녹색 계열의 점이 몇 개나 있을까?
# make hbesthee@naver.com
# date 2024-06-05

from os import getcwd, listdir, makedirs, path, remove, rename

import cv2
import numpy as np


IMAGES_PATH = r'D:/Temp/org_images'

file_list = listdir(IMAGES_PATH)
for filename in file_list:

	# 이미지 파일 경로
	image_filename = f"{IMAGES_PATH}/{filename}"

	# 이미지 불러오기
	image = cv2.imdecode(np.fromfile(image_filename, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

	# 녹색 계열 색상 범위 설정 (HSV 색상 공간)
	lower_green = (36, 55, 55)
	upper_green = (86, 255, 255)

	# 이미지를 HSV 색상 공간으로 변환
	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

	# 녹색 계열 색상 마스크 생성
	mask = cv2.inRange(hsv, lower_green, upper_green)

	# 녹색 계열 픽셀 수 계산
	green_pixels = cv2.countNonZero(mask)

	# 전체 픽셀 수 계산
	total_pixels = image.size

	# 녹색 계열 픽셀 비율 계산
	green_ratio = (green_pixels / total_pixels) * 100

	print(f"{filename} {green_ratio:.3f}")

	# 비교 화면 만들기
	image_new = np.full((image.shape[0], image.shape[1] * 2, 3), (127, 127, 127), dtype = np.uint8)
	image_new[0:image.shape[0], 0:image.shape[1]] = image
	image_new[0:image.shape[0], image.shape[1]:image.shape[1] * 2] = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
	cv2.imshow('org vs hsv_mask', image_new)

	if (green_ratio > 1):
		cv2.waitKey(0)