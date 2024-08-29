# LM73 TI 온도센서에서 온도값 읽어오기
# author : hbesthee@naver.com
# date : 2024-08-29

import smbus
import time

bus = smbus.SMBus(1) # I2C 버스 초기화
LM73_ADDR = 0x4C # LM73 I2C 주소

def read_temperature():
	# LM73칩의 온도 레지스터 읽기 (2바이트)
	temperatures = bus.read_i2c_block_data(LM73_ADDR, 0x00, 2)
	
	# 온도로 변환
	temp = ((temperatures[0] << 8) | temperatures[1]) >> 3
	if temp & 0x1000: # 2의 보수 처리 (음수 온도)
		temp = temp - 8192
	
	# 온도 스케일 조정 (0.0625°C 단위)
	return temp * 0.0625

try:
	while True:
		temperature = read_temperature()
		print(f"Temperature: {temperature:.2f}°C")
		time.sleep(1)

except KeyboardInterrupt:
	print("Measurement stopped by user")
except Exception as e:
	print(f"An error occurred: {e}")
finally:
	bus.close()