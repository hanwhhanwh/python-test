# 간단한 labeling된 이미지에 대한 뷰어
# make hbesthee@naver.com
# date 2024-07-30

from logging import getLogger, Logger
from multiprocessing import cpu_count, Pool
from os import chdir, getcwd, listdir, makedirs, path, remove, rename, fstat, symlink
from random import seed, random
from shutil import copyfile
from sys import argv, path as sys_path
from typing import Final

import cv2
import numpy as np


def main() -> int:
	""" 메인 실행부 """
	print(f'viewer path: {argv[1]}')
	file_list = listdir(f'{argv[1]}/images')
	total_file_count = len(file_list)

	file_index = 0
	while (True):
		image_filename = file_list[file_index]
		full_image_filename = f'{argv[1]}/images/{image_filename}'
		full_label_filename = f'{argv[1]}/labels/{image_filename}'.replace('.jpg', '.txt')

		if (path.exists(full_label_filename)):
			file = open(full_label_filename, "r")
			bbox_line = file.readline()
			file.close()
			values = bbox_line.split(' ')

			try:
				left, top, right, bottom = round(float(values[4])), round(float(values[5])), round(float(values[6])), round(float(values[7]))
				# plate_width = right - left
				# plate_height = bottom - top
			except Exception as e:
				print(f'bbox convert error({full_label_filename}\n\t{bbox_line})\n\t{e}')
				continue

			img_org = cv2.imdecode(np.fromfile(full_image_filename, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
			# height, width = img_org.shape[:2]
			cv2.rectangle(img_org, (left, top), (right, bottom), (0, 0, 255), 1)
		else:
			continue

		cv2.imshow("result", img_org)
		cv2.waitKey(0)
		file_index += 1



if __name__ == '__main__':

	main()
