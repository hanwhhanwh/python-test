# LPD kr 데이터셋 준비
#  8차 : 컨투어를 활용한 결과를 조합한 
# make hbesthee@naver.com
# date 2024-06-14

from logging import getLogger, Logger
from multiprocessing import cpu_count, Pool
from os import chdir, getcwd, listdir, makedirs, path, remove, rename, fstat
from random import seed, random
from shutil import copyfile
from sys import path as sys_path
from typing import Final

import cv2
import numpy as np

from lp_utils.data_utils import calculate_iou, create_folders, get_bounding_box
from lp_utils.file_logger import createLogger


TRAIN_NO: Final = 8
VALID_RATE: Final				= 0.08 # 전체 데이터셋에서 검증 데이터 비율
LOGGER_NAME: Final				= 'prepare_images'


DATASET_BASE: Final				= r'D:/Temp'
ORG_IMAGES_PATH: Final			= f'{DATASET_BASE}/org_images'
ORG_LABELS_PATH: Final			= f'{DATASET_BASE}/org_labels'

DATA_BASE: Final				= f'D:/Temp/{TRAIN_NO:02d}'
TRAIN_PATH: Final				= f'{DATA_BASE}/train'
VALID_PATH: Final				= f'{DATA_BASE}/valid'

IOU_THRESHOLD: Final			= 0.75 # IoU 값이 75% 이상인 컨투어만 적용하도록 함
DEBUG_SHOW_CONTOUR: Final		= True # 컨투어 이미지를 한장씩 확인하려할 경우 True로 변경하기



def process_dataset(filename: str) -> tuple:
	""" 주어진 파일을 가공하여 훈련 데이터셋으로 만듭니다.

	Args:
		filename (str): 데이터셋으로 가공할 파일 전체 경로 (jpg / txt)

	Returns:
		(processed, is_train, width, height)
	"""
	# 번호판이 숫자로 시작하지 않는 것은 훈련용으로 이용하지 않음
	# if (not filename[0].isdigit()):
	# 	return (False, False, 0, 0)

	filename1, _ = path.splitext(filename)
	label_file = f'{ORG_LABELS_PATH}/{filename1}.txt'
	inferenced_rect = np.array(get_bounding_box(label_file))
	if (inferenced_rect[0] == None):
		return (False, False, 0, 0)

	is_train = True
	# 원본 이미지를 읽어서 컨투어를 수행합니다.
	org_image_file = f'{ORG_IMAGES_PATH}/{filename}'
	img_color = cv2.imdecode(np.fromfile(org_image_file, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
	img_height, img_width, _ = img_color.shape
	img_extent_limit = (img_height * img_width) * 0.15
	img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
	_, img_binary = cv2.threshold(img_gray, 127, 255, 0)
	contours, _ = cv2.findContours(img_binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

	for cnt in contours:
		x, y, w, h = cv2.boundingRect(cnt)

		# 가장 크고 가운데 부분을 차지하는 바운딩 박스를 찾음
		#   규칙 : w가 h의 1.5배 이상 / 전체 면적의 20% 이상 / 중앙 점이 화면 중앙에서 10% 이내에 있어야 함
		if ( (h * 1.5) > w ): # w가 h의 1.5배 이상이 안되면 제외
			continue

		if ( (w * h) < img_extent_limit ): # 전체 면적의 20% 가 넘지 않으면 제외
			continue

		margin_t, margin_b = y, img_height - y - h
		margin_l, margin_r = x, img_width - x - w
		if (margin_t == 0 and margin_b == 0): # 상단, 바닥에 딱 붙은 것 제외
			continue
		if (margin_l == 0 and margin_r == 0): # 좌, 우측에 딱 붙은 것 제외
			continue

		inferenced_rect = inferenced_rect - 300
		if (calculate_iou(inferenced_rect, (x, y, x + w, x + h)) < IOU_THRESHOLD):
			continue

		if (random() > VALID_RATE): # 훈련/검증 비율에 맞추어 데이터셋 분리
			image_file = f'{TRAIN_PATH}/images/{filename1}.jpg'
			label_file = f'{TRAIN_PATH}/labels/{filename1}.txt'
		else:
			image_file = f'{VALID_PATH}/images/{filename1}.jpg'
			label_file = f'{TRAIN_PATH}/labels/{filename1}.txt'
			is_train = False

		# bounding box 정보 기록 ; 좌표 이동한 것을 1/2로 축소하는 것에 주의
		x2, y2, w2, h2 = round((x + 100) / 2), round((y + 100) / 2), round(w / 2), round(h / 2)
		label = f'lpd 0.00 0 0.00 {x2} {y2} {x2 + w2} {y2 + h2} 0.00 0.00 0.00 0.00 0.00 0.00 0.00'
		with open(label_file, 'wt') as f:
			f.write(label)
			f.close()

		# yolo_v4_tiny 입력 형식에 맞게 이미지 확장하여 저장
		img_new = np.full((768, 1280, 3), (127, 127, 127), dtype = np.uint8)
		img_new[100:100 + img_height, 100:100 + img_width] = img_color

		img_new = cv2.resize(img_new, (640, 384), interpolation=cv2.INTER_CUBIC)
		is_ok, encoded_buffer = cv2.imencode('.jpg', img_new, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
		if (not is_ok):
			return (False, False, 0, 0)
		with open(image_file, 'wb') as iff:
			iff.write(encoded_buffer)

		if (DEBUG_SHOW_CONTOUR):
			cv2.rectangle(img_new, (x2, y2), (x2 + w2, y2 + h2), (0, 0, 255), 2)
			cv2.imshow("result", img_new)
			cv2.waitKey(0)

		return (True, is_train, img_width, img_height) # 번호판 대상을 찾은 경우, 다른 바운딩 박스는 처리하지 않음

	return (False, False, 0, 0) # 처리할 컨투어가 없음

	filename1, _ = path.splitext(filename)
	org_image_file = f'{ORG_IMAGES_PATH}/{filename1}.jpg'
	
	if (random() > VALID_RATE): # 훈련/검증 비율에 맞추어 데이터셋 분리
		image_file = f'{TRAIN_PATH}/images/{filename1}.jpg'
		label_file = f'{TRAIN_PATH}/labels/{filename}'
		train_count += 1
	else:
		image_file = f'{VALID_PATH}/images/{filename1}.jpg'
		label_file = f'{VALID_PATH}/labels/{filename}'
		valid_count += 1

	# copyfile(org_image_file, image_file)
	img_org = cv2.imdecode(np.fromfile(org_image_file, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
	height, width, _ = img_org.shape

	if (max_width < (width)):
		max_width = (width)
	if (max_height < (height)):
		max_height = (height)

	# yolo_v4_tiny 입력 형식에 맞게 이미지 확장
	img_new = np.full((960, 1280, 3), (127, 127, 127), dtype = np.uint8)
	img_new[300:300 + height, 300:300 + width] = img_org

	img_new = cv2.resize(img_new, (640, 480), interpolation=cv2.INTER_CUBIC)
	cv2.imwrite(image_file, img_new)

	file = open(label_file, "wt")
	for index in range(15): # KITTI 형식에 맞게 출력
		if (index == 0):
			file.write(values[index])
		else:
			if (index in [4, 5, 6, 7]): # left, top, right, bottom
				file.write(f' {float(values[index]) / 2}')
			else:
				file.write(f' {values[index]}')
			# file.write(f' {values[index]}')
	file.close()


def main() -> int:
	logger: Logger = getLogger()
	logger.info(f'source images path: {ORG_IMAGES_PATH}')
	file_list = listdir(ORG_IMAGES_PATH)
	total_file_count = len(file_list)

	logger.info(f'multi processing with {cpu_count()} CPUs / {total_file_count} total files')
	# pool = Pool(cpu_count()) # 멀티 프로세싱 : CPU 개수 - 1개로 설정
	pool = Pool(1) # 멀티 프로세싱 : CPU 개수 - 1개로 설정

	file_count, total_count, train_count, valid_count = 0, 0, 0, 0
	max_height, max_width = 0, 0
	imap_unordered = pool.imap_unordered(process_dataset, file_list)
	for task_result in imap_unordered:
		file_count += 1
		if (file_count % 1000 == 0):
			logger.info(f'{file_count=} processed...')

		processed, is_train, width, height = task_result
		if (max_width < (width)):
			max_width = (width)
		if (max_height < (height)):
			max_height = (height)

		if (processed):
			total_count += 1
			if (is_train):
				train_count += 1
			else:
				valid_count += 1

	pool.close()
	pool.join()

	logger.info(f'Max Info : {max_width=} / {max_height=}')
	logger.info(f'{file_count=} / train {total_count=}({train_count=} / {valid_count=})')



if __name__ == '__main__':

	chdir(path.dirname(__file__)) # 작업 폴더를 소스가 있는 폴더로 변경
	print(f'current_folder = {getcwd()}')

	logger = createLogger(log_filename = LOGGER_NAME, log_level = 10)

	create_folders( (
		f'{TRAIN_PATH}/images', f'{TRAIN_PATH}/labels'
		, f'{VALID_PATH}/images', f'{VALID_PATH}/labels'
		, f'{DATA_BASE}/logs', f'{DATA_BASE}/runs'
	) )

	logger.info(f'prepare_images {TRAIN_NO} start.')

	main()
