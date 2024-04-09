# Raspberry PI GPI control demo 1
# author : hbesthee@naver.com
# date : 2023-08-29

import time
import RPi.GPIO as GPIO

LED = 3 # LED 제어용 GPIO 핀
DELAY = 0.3

# GPIO를 BCM 칩 기준으로
GPIO.setmode(GPIO.BCM)

# LED 를 위한 핀을 출력으로 설정
GPIO.setup(LED, GPIO.OUT)

try:
	while True:
		# LED 켜기
		GPIO.output(LED, GPIO.HIGH)
		time.sleep(DELAY)

		# LED 끄기
		GPIO.output(LED, GPIO.LOW)
		time.sleep(DELAY)

except KeyboardInterrupt:
	GPIO.cleanup()
