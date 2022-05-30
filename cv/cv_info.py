# OpenCV 정보 확인 예제
import cv2

# 패키지 설치 위치 확인
print(cv2.__file__)

# 패키지 버전 확인
print(cv2.__version__)

# 쿠다를 사용할 수 있는 장치 수
print(cv2.cuda.getCudaEnabledDeviceCount())

""" Result
/opt/intel/openvino/python/python3/cv2/python-3/cv2.abi3.so
4.5.3-openvino
0
"""
