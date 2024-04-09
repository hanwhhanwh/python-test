
# Jetson SPI loopback demo
# author : hbesthee@naver.com
# date : 2024-04-09

import spidev
import time

spi = spidev.SpiDev()
spi.open(0,0) #I tried both (1,0) and (0,0)
spi.bits_per_word = 8 # Set SPI bits_per_word
spi.max_speed_hz = 500000 # Set maximum SPI speed
spi.mode = 0 # Set SPI mode (0 or 3)

def BytesToHex(Bytes):
	return ''.join(["0x%02X " % x for x in Bytes]).strip()

try:
	while True:
		resp = spi.xfer2([1,7,0,2,1,69,5,6])
		print(BytesToHex(resp))
		time.sleep(1)

except KeyboardInterrupt:
	spi.close()
