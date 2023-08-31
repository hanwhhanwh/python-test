# 파워메터 측정 데이터 가져오기
# date	2023-08-31
# author	hbesthee@naver.com
from pyvisa import ResourceManager

host, port = '192.168.0.11', 0
conn_str = f'TCPIP{port}::{host}::INSTR'

rm = ResourceManager(r'C:\WINDOWS\system32\visa64.dll') # visa 객체를 생성합니다.

print(f'PowerMeter {host}:{port} connecting...')
power_meter = rm.open_resource(conn_str)

print (power_meter.query('*IDN?'))

power_meter.write(f':SENS:FREQ 50MHz')
power_meter.write(f':SENS:SPE 20')
point = power_meter.query(f':FETC?')
print(f'{type(point)}')
print(f'{point=}')
fpoint = float(point)
print(f'{fpoint=}')

power_meter.close()
