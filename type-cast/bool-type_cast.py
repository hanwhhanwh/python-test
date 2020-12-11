# 불리언으로 데이터 형 변환 예제 : type case to bool

# bool(int)
int_bool = bool(1234)
print(f'bool(1234) = {int_bool} ; type(int_bool) = {type(int_bool)}')
zero_bool = bool(0)
print(f'bool(0) = {zero_bool} ; type(zero_bool) = {type(zero_bool)}')

# bool(float)
float_bool = bool(1234.5678)
print(f'bool(1234.5678) = {float_bool} ; type(float_bool) = {type(float_bool)}')
float_zero_bool = bool(0.00)
print(f'bool(0.00) = {float_zero_bool} ; type(float_zero_bool) = {type(float_zero_bool)}')

# bool(bool)
true_bool = bool(True)
print(f'bool(True) = {true_bool} ; type(true_bool) = {type(true_bool)}')
false_bool = bool(False)
print(f'bool(False) = {false_bool} ; type(false_bool) = {type(false_bool)}')
 
# bool(str)
not_empty_str_bool = bool('not empty')
print(f'bool(\'not empty\') = {not_empty_str_bool} ; type(not_empty_str_bool) = {type(not_empty_str_bool)}')
empty_str_bool = bool('')
print(f'bool(\'\') = {empty_str_bool} ; type(empty_str_bool) = {type(empty_str_bool)}')
