# -*- coding: utf-8 -*-
# weekday를 언어별 문자열 출력 예시
# made : hbesthee@naver.com
# date : 2025-06-19

# Original Packages
from datetime import datetime
from locale import LC_TIME, setlocale

dt = datetime(2025, 6, 18)

# 영어(미국)
setlocale(LC_TIME, 'en_US.UTF-8')
print(dt.strftime('%A'))  # Wednesday

# 일본어
setlocale(LC_TIME, 'ja_JP.UTF-8')
print(dt.strftime('%A'))  # 水曜日

# 독일어
setlocale(LC_TIME, 'de_DE.UTF-8')
print(dt.strftime('%A'))  # Mittwoch

# 한국어(지원 OS 한정)
setlocale(LC_TIME, 'ko_KR.UTF-8')
print(dt.strftime('%A'))  # 수요일