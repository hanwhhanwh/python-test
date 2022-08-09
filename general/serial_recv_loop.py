# serial receiving loop demo
# date: 2022-08-09
# author: hbesthee@naver.com
#-*- coding: utf-8 -*-
# use tab char size: 4


import serial
import os, sys
import struct
import threading
import time
from typing import Final

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

PKT_SENSOR_INIT = b'\x03\x4D\x00\x01\x00\x00\x00\x00'
#self.resetmsg = b'\3\77\1\3\5\0\0\0'


if __name__ == "__main__":
	print("start serial")

m_serial = serial.Serial(port = 'COM11', baudrate = 115200, parity = serial.PARITY_NONE,
					stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS)

m_serial.write(PKT_SENSOR_INIT)

m_buffer = bytes()
last_received = time.time()
while True:
	data = m_serial.read()
	m_buffer += data
	if (data == b'\x02'):
		break
	last_received = time.time()

print(m_buffer.hex())
