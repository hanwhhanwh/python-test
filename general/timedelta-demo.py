# timedelta demo
# date: 2025-03-28
# author: hbesthee@naver.com
#-*- coding: utf-8 -*-
# use tab char size: 4


from datetime import datetime, timedelta

# 두 날짜 생성
date1 = datetime(2024, 3, 15, 10, 30, 0)  # 2024년 3월 15일 10:30:00
date2 = datetime(2024, 5, 20, 14, 45, 30)  # 2024년 5월 20일 14:45:30

# 날짜 차이 계산
time_difference = date2 - date1

# 차이 출력
print("\n날짜 차이:", time_difference)
print("총 일수:", time_difference.days)
print("총 초:", time_difference.total_seconds())

"""
날짜 차이: 66 days, 4:15:30
총 일수: 66
총 초: 5717730.0
"""

# 다양한 단위로 차이 계산
print("\n총 시간(시):", time_difference.total_seconds() / 3600)  # 시간으로 변환
print("총 시간(분):", time_difference.total_seconds() / 60)   # 분으로 변환

"""
총 시간(시): 1588.2583333333334
총 시간(분): 95295.5
"""


# 현재 시간 가져오기
now = datetime.strptime('2021-06-22 08:10', '%Y-%m-%d %H:%M')

# 특정 날짜와 현재 시간 차이 계산
future_date = now + timedelta(days=100)
past_date = now - timedelta(days=50)

print("\n현재로부터 100일 후:", future_date)
print("현재로부터 50일 전:", past_date)
print("100일 후까지 남은 일수:", (future_date - now).days)

"""
현재로부터 100일 후: 2025-07-06 23:19:30.074936
현재로부터 50일 전: 2025-02-06 23:19:30.074936
100일 후까지 남은 일수: 100
"""
