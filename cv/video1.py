import cv2
import numpy as np

v = cv2.VideoCapture('D:\\temp\\1654.mp4')

# 초당 프레임 수
print(v.get(cv2.CAP_PROP_FPS)) # 9.884579186220412
# 비디오 파일에서 현재 위치(밀리초 단위)
print(v.get(cv2.CAP_PROP_POS_MSEC)) # 0.0
# 현재 프레임 위치(0-기반)
print(v.get(cv2.CAP_PROP_POS_FRAMES)) # 0.0
# 비디오 파일의 전체 프레임 수
print(v.get(cv2.CAP_PROP_FRAME_COUNT)) # 16356.0
print('[0,1]구간으로 표현한 동영상 프레임의 상대적 위치(0: 시작, 0이 아닌 값 (1 등): 끝)')
print(v.set(cv2.CAP_PROP_POS_AVI_RATIO, 0)) # True
print(v.get(cv2.CAP_PROP_POS_FRAMES)) # 0
print(v.get(cv2.CAP_PROP_POS_MSEC)) # 0.0

print(v.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)) # True ; 끝으로 이동
print(v.get(cv2.CAP_PROP_POS_MSEC)) # 0.011111111111111112 ; 코덱에 따라 정확하지 않음
sec = v.get(cv2.CAP_PROP_POS_FRAMES) / v.get(cv2.CAP_PROP_FPS)
hour = int(sec / 3600)
min = int(sec / 60) - hour * 60
e_sec = int(sec) % 60
msec = int((sec - int(sec) + 0.0005) * 1000)
print(f'{sec} duration = {hour:02}:{min:02}:{e_sec:02}.{msec:03}')
# 1654.6986666666665881756503016766 / 60
