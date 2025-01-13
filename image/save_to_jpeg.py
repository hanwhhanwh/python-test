# -*- coding: utf-8 -*-
# 품질을 설정하여 이미지를 JPEG 파일로 저장하는 여러 방법
# made : hbesthee@naver.com
# date : 2025-01-02

from PIL import Image

import cv2


# 이미지 열기
img_pil = Image.open('resize.png')

if (img_pil.mode in ['RGBA', 'P']): # 알파 채널이 있는 경우 RGB로 변환
	img_pil = img_pil.convert('RGB')
img_pil.convert('RGB').save('output.jpg', format = 'JPEG', quality = 85) # 품질 설정하여 저장 (1 ~ 100)

img = cv2.imread('output.jpg')
cv2.imshow('JPEG - PIL', img)
cv2.waitKey()

img_cv2 = Image.open('resize.png')
# img_cv2 = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB)
cv2.imwrite('output.jpg', img_cv2, [cv2.IMWRITE_JPEG_QUALITY, 85])

img = cv2.imread('output.jpg')
cv2.imshow('JPEG - cv2', img)
cv2.waitKey()
