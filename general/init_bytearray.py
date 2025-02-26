# -*- coding: utf-8 -*-
# bytearray 초기화하는 방법
# made : hbesthee@naver.com
# date : 2025-02-22


# 예: 임의의 값으로 bytearray 생성
b = bytearray([1, 2, 3, 4, 5])
print(f'원래 bytearray = {b}')

# 모든 요소를 0으로 설정 ; 슬라이싱
b[:] = bytes([0] * len(b))
print(f'슬라이싱 = {b}')

b = bytearray([1, 2, 3, 4, 5])
# 모든 요소를 0으로 설정 ; 반복문
for i in range(len(b)):
    b[i] = 0
print(f'반 복 문 = {b}')
