# 문자열로 데이터 형 변환 예제 : type case to string
from io import StringIO
import numpy as np

# str(int) : 정수를 문자열로 변환
int_str = str(1234)
print(f'str(1234) = {int_str} ; type(int_str) = {type(int_str)}')

# str(float) : 실수를 문자열로 변환
float_str = str(1234.5678)
print(f'str(1234.5678) = {float_str} ; type(float_str) = {type(float_str)}')

# str(bool) : 불리언을 문자열로 변환
true_str = str(True)
print(f'str(True) = {true_str} ; type(true_str) = {type(true_str)}')
false_str = str(False)
print(f'str(False) = {false_str} ; type(false_str) = {type(false_str)}')

# str(char) : 문자를 문자열로 변환
H_str = str('H')
print(f'str("H") = {H_str} ; type(H_str) = {type(H_str)}')
h_str = str('h')
print(f'str("h") = {h_str} ; type(h_str) = {type(h_str)}')

# str(class) : 객체를 문자열로 변환
points = np.loadtxt(StringIO('158 232\n356 232\n550 232\n158 321\n356 321\n550 321\n158 409\n356 409\n550 409'))
str_points = str(points)
print(f'str(points) = {str_points} ; type(points) = {type(points)}')
