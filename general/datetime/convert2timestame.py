# 날짜 문자열을 timestamp로 변환하기 ; convert date string to timestame
# reference : https://hbesthee.tistory.com/2067

from datetime import datetime

dt = datetime.strptime('2022-11-10 11:28:07', '%Y-%m-%d %H:%M:%S')
dt = datetime(2022, 11, 10, 11, 28, 7)
print(dt)
# Console : 2022-11-10 11:28:07
# IDLE : datetime.datetime(2022, 11, 10, 11, 28, 7)
print(datetime.timestamp(dt))
# 1668047287.0

from time import mktime

print(dt.timetuple())
# time.struct_time(tm_year=2022, tm_mon=11, tm_mday=10, tm_hour=11, tm_min=28, tm_sec=7, tm_wday=3, tm_yday=314, tm_isdst=-1)
print(mktime(dt.timetuple()))
# 1668047287.0
