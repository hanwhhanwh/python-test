# 이미지들 중에서 RGBA 형식의 이미지를 확인하여 목록을 출력합니다.
# make hbesthee@naver.com
# date 2024-05-27


from os import getcwd, listdir, makedirs, path, remove, rename, fstat
from PIL import Image
from typing import Final

import cv2


DATASET_BASE: Final				= r'D:\Temp'
ORG_IMAGES_PATH: Final			= f'{DATASET_BASE}\\org_images'


def main() -> int:

	file_list = listdir(ORG_IMAGES_PATH)

	file_count, max_height, max_width = 0, 0, 0
	for filename in file_list:
		file_count += 1
		if (file_count % 1000 == 0):
			print(f'{file_count=} processed...')

		org_image_file = f'{ORG_IMAGES_PATH}\\{filename}'

		# 이미지 열기
		org_image = Image.open(org_image_file)

		# RGBA 형식 확인
		if (org_image.mode == "RGBA"):
			print(org_image_file)

if __name__ == '__main__':

	main()