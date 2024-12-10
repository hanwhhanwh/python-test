# -*- coding: utf-8 -*-
# 폴더내 이미지를 타일 형식으로 배치한 이미지를 만들어 주는 스크립트
# hbesthee@naver.com
# date	2024-12-10

import os
import math

import cv2
import numpy as np


def create_image_tile(input_dir: str, output_tile_image_filename: str, tile_width: int = 1000
					, cols: int = 5, tile_height: int = 200, margin = 3, background_color = (255, 255, 255)) -> bool:
	"""
	OpenCV를 사용하여 폴더 내 이미지를 타일 형태로 배치합니다.
	
	Args:
		input_folder: 이미지가 있는 폴더 경로
		output_path: 결과 타일 이미지 저장 경로
		total_width: 최종 생성될 이미지의 전체 너비
		cols: 타일 열의 수 (기본 5열)
		tile_height: 각 타일 이미지의 높이
		margin: 타일 간 여백 크기 (픽셀)
		background_color: 배경색 (B, G, R)

	Returns:
		bool: 타일 이미지 성공 여부
	"""
	# 이미지 파일 목록 가져오기
	image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
	
	# 이미지 파일이 없으면 종료
	if not image_files:
		print(f'"{input_dir}" 폴더에 이미지 파일이 없습니다.')
		return False
	
	# 각 타일의 너비 계산 (여백 제외)
	tile_width = (tile_width - (cols + 1) * margin) // cols
	
	# 이미지 로드 및 리사이즈
	processed_images = []
	for filename in image_files:
		try:
			# OpenCV로 이미지 읽기 (BGR 포맷)
			img = cv2.imread(os.path.join(input_dir, filename))
			
			# 이미지 회전 및 크기 조정
			height, width = img.shape[:2]
			aspect_ratio = width / height
			
			# 높이 고정, 가로 비율 유지하며 리사이즈
			new_height = tile_height
			new_width = int(new_height * aspect_ratio)
			
			# 이미지가 타일 너비를 초과하면 너비 기준으로 리사이즈
			if new_width > tile_width:
				new_width = tile_width
				new_height = int(new_width / aspect_ratio)
			
			# 이미지 리사이즈
			resized_img = cv2.resize(img, (new_width, new_height), interpolation = cv2.INTER_AREA)
			processed_images.append(resized_img)
		except Exception as e:
			print(f"{filename} 처리 중 오류: {e}")
			return False
	
	# 행 수 계산
	total_images = len(processed_images)
	rows = math.ceil(total_images / cols)
	
	# 최종 이미지 크기 계산 (여백 포함)
	width = tile_width
	height = rows * tile_height + (rows + 1) * margin
	
	# 배경 이미지 생성 (흰색)
	tile_image = np.full((height, width, 3), background_color, dtype=np.uint8)
	
	# 이미지 배치
	for i, img in enumerate(processed_images):
		row = i // cols
		col = i % cols
		
		# 좌표 계산 (여백 포함)
		x = col * (tile_width + margin) + margin
		y = row * (tile_height + margin) + margin
		
		# 이미지 높이와 너비 계산
		h, w = img.shape[:2]
		
		# 타일 내 중앙 정렬
		start_x = x + (tile_width - w) // 2
		start_y = y + (tile_height - h) // 2
		
		tile_image[start_y:start_y+h, start_x:start_x+w] = img # 이미지 붙이기
	
	cv2.imwrite(output_tile_image_filename, tile_image) # 타일 이미지 저장
	
	print(f'타일 이미지가 "{output_tile_image_filename}"에 저장되었습니다.')
	print(f'전체 너비: {width}, 행: {rows}, 열: {cols}, 여백: {margin}px')

	return True


# 사용 예시
if __name__ == "__main__":
	input_folder = "path/to/your/image/folder"  # 이미지가 있는 폴더 경로
	output_path = "tiled_images.jpg"  # 결과 이미지 저장 경로
	
	# 다양한 사용 방법 예시:
	# 1. 기본 설정 (전체 너비 1000px, 5열, 기본 여백)
	create_image_tile(input_folder, output_path)
	
	# 2. 사용자 지정 설정
	# create_image_tile(
	#     input_folder, 
	#     output_path, 
	#     total_width=1500,   # 전체 너비
	#     cols=4,             # 열 수
	#     tile_height=250,    # 타일 높이
	#     margin=20,          # 여백 크기
	#     background_color=(230, 230, 230)  # 배경색 (회색)
	# )