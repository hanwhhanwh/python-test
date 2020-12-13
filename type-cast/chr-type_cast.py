# 문자로 데이터 형 변환 예제 : type case to chr

# chr(int)
A_chr = chr(65)
print(f'chr(65) = {A_chr} ; type(a) = {type(A_chr)}')
B_chr = chr(66)
print(f'chr(66) = {B_chr} ; type(b) = {type(B_chr)}')

# chr(bool) : same int 1 (True), int 0 (False)
true_chr = chr(True)
int1_chr = chr(1)
if true_chr == int1_chr:
    print('chr(True) == chr(1)')
false_chr = chr(False)
int0_chr = chr(0)
if false_chr == int0_chr:
    print('chr(False) == chr(0)')

# chr(float) # occured TypeError
# float_chr = chr(1234.5678) # TypeError: integer argument expected, got float
# chr(str) # occured TypeError
# str_chr = chr('abcdefg') # TypeError: an integer is required (got type str)
