# N8975A SCPI command : get points
# date	2023-08-22
# author	hbesthee@naver.com

from pyvisa import ResourceManager
from time import sleep


_GPIB = 8
_port = 0

rm = ResourceManager(r'C:\WINDOWS\system32\visa64.dll') # visa 객체를 생성합니다.


client = rm.open_resource(f'GPIB{_port}::{_GPIB}::INSTR') # 지정한 HOST와 PORT를 사용하여 서버에 접속합니다.
print (client.query('*IDN?')) # 장비 정보 확인

point_count = client.query(f'SENS:SWE:POIN?') # 측정 포인트 개수 확인하기
print(point_count)

client.write(f'FETC:ARR:DATA:CORR:NFIG?') # 측정 포인트 가져오기
data = client.read_raw()
print(data)

""" Results >>>
Agilent Technologies, N8975A, MY45270225, A.01.12

+11

b'+9.91000E+37,+9.91000E+37,+9.91000E+37,+9.91000E+37,+9.91000E+37,+9.91000E+37,+9.91000E+37,+9.91000E+37,+9.91000E+37,+9.91000E+37,+9.91000E+37\x00\n'
"""