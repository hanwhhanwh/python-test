# 정규식으로 (숫자) 형식을 찾아 제거하는 예제
# make hbesthee@naver.com
# date 2024-06-20

from re import sub as re_sub

text = "이것은 (1)예시 문장입니다. (0)다른 예시도 있습니다."
filename = 'my_testfile(0).jpg'

# 정규식 패턴
pattern = r'\([0-9]+\)'

# 정규식을 이용하여 패턴에 해당하는 부분을 빈 문자열로 대체
cleaned_text = re_sub(pattern, '', text)
cleaned_filename = re_sub(pattern, '', filename)

print(cleaned_text)
print(cleaned_filename)

"""
이것은 예시 문장입니다. 다른 예시도 있습니다.
my_testfile.jpg
"""