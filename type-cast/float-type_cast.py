# 실수로 데이터 형 변환 예제 : type case to float

# float(int)
int_float = float(1234)
print(f'float(1234) = {int_float}, type(int_float) = {type(int_float)}')

# float(bool)
true_float = float(True)
false_float = float(False)
print(f'float(True) = {true_float}, float(False) = {false_float}')

# float(number str)
int_str_float = float('1234')
print(f'float("1234") = {int_str_float} ; type(int_str_float) = {type(int_str_float)}')
float_str_int = float('1234.5678')
print(f'float("1234.5678") = {float_str_int} ; type(float_str_int) = {type(float_str_int)}')

# float(not number str)
# value_error_str = float('abcdefg') # ValueError: could not convert string to float: 'abcdefg'
try:
	value_error_str = float('abcdefg')
except:
	print('int(\'abcdefg\') # ValueError')
