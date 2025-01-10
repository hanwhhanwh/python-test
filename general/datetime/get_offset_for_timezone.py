# -*- coding: utf-8 -*-
# 기본 패키지를 활용하여, UTC 시간 대비, 현재 시간대의 OFFSET 시간을 구하는 방법
# made : hbesthee@naver.com
# date : 2025-01-02


from datetime import datetime
from zoneinfo import ZoneInfo # Python 3.9+ 에서 zoneinfo 사용
import time

# 현재 로컬 타임존의 UTC offset 구하기
# time.timezone은 초 단위로 제공됨
utc_offset_seconds = -time.timezone if time.localtime().tm_isdst == 0 else -time.altzone
utc_offset_hours = utc_offset_seconds / 3600

print(f"UTC Offset: {utc_offset_hours:+.1f} hours")

# datetime을 사용한 더 자세한 방법
local_now = datetime.now()
utc_now = datetime.utcnow()
# utc_now = datetime.now(datetime.tzinfo.)
offset = local_now - utc_now

print(f"UTC Offset (상세): {offset} / {offset.seconds / 3600:+.1f} hours")
print(f"local_now timezone name = {datetime.tzname(local_now)}")
print(f"current timezone name = {time.tzname[0]}")

local_tz = datetime.now().astimezone().tzinfo
print(f"상세 timezone 정보: {local_tz}")