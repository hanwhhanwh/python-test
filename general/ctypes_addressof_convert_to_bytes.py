# -*- coding: utf-8 -*-
# ctypes.addressof()를 이용한 메모리 주소에서 특정 길이만큼 bytes로 읽기
# made : hbesthee@naver.com
# date : 2025-06-20

# Original Packages
import ctypes


# 예시: 배열 생성
arr = (ctypes.c_int * 5)(1, 2, 3, 4, 5)
addr = ctypes.addressof(arr)
length = ctypes.sizeof(arr)  # 또는 원하는 길이

# 1. ctypes.string_at() 사용 (권장)
data = ctypes.string_at(addr, length)
print(type(data))  # <class 'bytes'>
print(data.hex())  # 0100000002000000030000000400000005000000


# 2. ctypes.cast()와 POINTER 사용
char_ptr = ctypes.cast(addr, ctypes.POINTER(ctypes.c_char * length))
data = bytes(char_ptr.contents)
print(data.hex())  # 0100000002000000030000000400000005000000

# 3. from_address() 사용
char_array = (ctypes.c_char * length).from_address(addr)
data = bytes(char_array)
print(data.hex())  # 0100000002000000030000000400000005000000