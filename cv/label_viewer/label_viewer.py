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


import label_viewer_const as const


_conf: dict = None

def main() -> int:
	""" 메인 실행부 """

	global _conf

	cv2.namedWindow(const.LV_WINDOW_NAME, cv2.WINDOW_GUI_EXPANDED)
	cv2.moveWindow(const.LV_WINDOW_NAME, 0, 0)

	print(f'viewer path: {argv[1]}')
	file_list = listdir(f'{argv[1]}/images')
	total_file_count = len(file_list)

	target_width = const.get_dict_value(_conf, const.JKEY_VIEWER_WIDTH, const.DEF_VIEWER_WIDTH)
	target_height = const.get_dict_value(_conf, const.JKEY_VIEWER_HEIGHT, const.DEF_VIEWER_HEIGHT)

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
		else:
			continue

		bb_modified = False
		img_org = cv2.imdecode(np.fromfile(full_image_filename, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
		img_height, img_width = img_org.shape[:2]
		cv2.setWindowTitle(const.LV_WINDOW_NAME, f'{image_filename} - {img_width} X {img_height}')

		scale_height, scale_width = (img_height / target_height), (img_width / target_width)
		img_scale = min(scale_height, scale_width)
		# 원본 이미지를 설정에 맞게 축소
		scaled_img = cv2.resize(img_org, (round(img_width * img_scale), round(img_height * img_scale)), interpolation = cv2.INTER_CUBIC)
		scaled_left, scaled_top, scaled_right, scaled_bottom = round(float(values[4]) * img_scale), round(float(values[5]) * img_scale), round(float(values[6]) * img_scale), round(float(values[7]) * img_scale)
		while (True):
			img_new = np.full((target_height, target_width, 3), (127, 127, 127), dtype = np.uint8)
			img_new[0:scaled_img.shape[0], 0:scaled_img.shape[1]] = scaled_img
			cv2.rectangle(img_new, (scaled_left, scaled_top), (scaled_right, scaled_bottom), (0, 0, 255), 1)
			cv2.imshow(const.LV_WINDOW_NAME, img_new)

			key = cv2.waitKey(0)
			capital_key = (key & 0xDF)
			if (capital_key in (ord('L'), ord('T'), ord('R'), ord('B'))): # BB 변경

				bb_modified = True
				capital = -1 if ( (key & 0x20) == 0 ) else 1
				if (capital_key == ord('L')):
					scaled_left -= 1 * capital
				if (capital_key == ord('T')):
					scaled_top -= 1 * capital
				if (capital_key == ord('R')):
					scaled_right += 1 * capital
				if (capital_key == ord('B')):
					scaled_bottom += 1 * capital
				continue
			if ( bb_modified and ((key & 0xDF) == ord('S')) ): # 변경된 BB 저장하기
				values[4] = f'{(scaled_left / img_scale):.3f}'
				values[5] = f'{(scaled_top / img_scale):.3f}'
				values[6] = f'{(scaled_right / img_scale):.3f}'
				values[7] = f'{(scaled_bottom / img_scale):.3f}'
				const.save_label_values(full_label_filename, values)
				continue

			break

		# print(f'{key:04X}')
		file_index += 1

		if (cv2.getWindowProperty(const.LV_WINDOW_NAME, cv2.WND_PROP_VISIBLE ) < 1):
			break




if __name__ == '__main__':
	if (not path.exists(const.FILENAME_VIEWER_CONF)):
		_conf = const.DEF_VIEWER_CONF
		const.save_json_conf(const.FILENAME_VIEWER_CONF, _conf)
	else:
		_conf, err_msg = const.load_json_conf(const.FILENAME_VIEWER_CONF)
		if (err_msg != ''):
			print(f'config load error: {err_msg}')
			exit(-1)

	main()
	exit(0)
