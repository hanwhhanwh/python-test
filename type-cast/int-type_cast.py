# 정수로 데이터 형 변환 예제 : type case to int

# int(float)
float_int = int(1234.5678)
print(f'int(1234.5678) = {float_int} ; type(float_int) = {type(float_int)}')

# int(bool)
true_int = int(True)
false_int = int(False)
print(f'int(True) = {true_int}, int(False) = {false_int}')

# int(number str)
str_int = int('1234')
print(f'int("1234") = {str_int} ; type(str_int) = {type(str_int)}')

# int(not number str)
# str_int = int('1234.5678') # ValueError: invalid literal for int() with base 10: '1234.5678'
# value_error_str = int('abcdefg') # ValueError: invalid literal for int() with base 10: 'abcdefg'
try:
	value_error_str = int('abcdefg')
except:
	print('int(\'abcdefg\') # ValueError')
