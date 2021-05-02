# 날짜 변환에 대한 예제

import datetime as dt

# value_error = dt.datetime.strptime('02-4-23', '%y-%m-%D')
# ValueError: 'D' is a bad directive in format '%y-%m-%D'

converted_day = dt.datetime.strptime('02-4-23', '%y-%M-%d')
print(converted_day)
# OK : 2002-01-23 00:04:00 ; %M은 분으로, 형식 지정이 잘못되어 논리적 오류임

converted_day = dt.datetime.strptime('02-4-23', '%y-%m-%d')
print(converted_day)
# OK : 2002-04-23 00:00:00

# value_error = dt.datetime.strptime('102-4-23', '%y-%m-%d')
# ValueError: time data '102-4-23' does not match format '%y-%m-%d'

# value_error = dt.datetime.strptime('124-4-23', '%Y-%m-%d')
# ValueError: time data '124-4-23' does not match format '%Y-%m-%d'

converted_day = dt.datetime.strptime('0124-4-23', '%Y-%m-%d')
print(converted_day)
# OK : 0124-04-23 00:00:00

# converted_day = dt.datetime.strptime('0124-14-23', '%Y-%m-%d')
# ValueError: time data '0124-14-23' does not match format '%Y-%m-%d'
