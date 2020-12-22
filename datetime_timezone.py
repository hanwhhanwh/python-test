# datetime & timezone example
import datetime as dt

kst_timezone = dt.timezone(dt.timedelta(hours=9), 'KST')
now_utc = dt.datetime.now(dt.timezone.utc)
now_kst = dt.datetime.now(kst_timezone)
now_none = dt.datetime.now()

print(now_utc)
print(now_utc.tzinfo)

print(now_kst)
print(now_kst.tzinfo)
print('to UTC = ', now_kst.astimezone(dt.timezone.utc))

print(now_none)
print(now_none.tzinfo)
print('to UTC = ', now_none.astimezone(dt.timezone.utc))
print('to KST = ', now_none.astimezone(kst_timezone))
