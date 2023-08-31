# serial receiving loop demo
# date: 2022-08-09
# author: hbesthee@naver.com
#-*- coding: utf-8 -*-
# use tab char size: 4


import serial
import os, sys
import struct
import time


PKT_PREFIX					= 0x4D03
PKT_PREFIX_BYTES			= b'\x03\x4D'
PKT_HEADER_SIZE				= 8

CMD_SENSOR_INIT				= 0x0100
CMD_SENSOR_START			= 0x0110
CMD_SENSOR_PAUSE			= 0x0120
CMD_SENSOR_RESUME			= 0x0130
CMD_SENSOR_RESTART			= 0x0140

CMD_SENSING_IN_CAR			= 0x0200
CMD_SENSING_DATA			= 0x0201
CMD_SENSING_IN_CAR_DATA		= 0x0202
CMD_SENSING_OUT_CAR			= 0x0203

CMD_SENSOR_PARAM			= 0x0300
CMD_RESET_COUNT				= 0x0301


PKT_SENSOR_INIT = b'\x03\x4D\x00\x01\x00\x00\x00\x00'
#self.resetmsg = b'\3\77\1\3\5\0\0\0'

FMT_PKT_HEADER = 'HHi'


if __name__ == "__main__":
	print("start serial")

m_serial = serial.Serial(port = 'COM11', baudrate = 115200, parity = serial.PARITY_NONE
					, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS
					, timeout = 5)

m_serial.write(PKT_SENSOR_INIT)
m_serial.write(struct.pack(FMT_PKT_HEADER, PKT_PREFIX, CMD_SENSOR_INIT, 0))

m_buffer = bytes()
last_received = time.time()
while True:
	data = m_serial.read(PKT_HEADER_SIZE)
	if (data == b''):
		buffer_len = len(m_buffer)
		if (buffer_len > 0):
			# buffer clear
			print(f'remain data cleared ({buffer_len}) = {m_buffer.hex()}')
			m_buffer = bytes()
		continue

	m_buffer += data
	print(f'recv data = {data.hex()}')
	buffer_len = len(m_buffer)
	if (buffer_len >= PKT_HEADER_SIZE):
		# analyze packet header
		prefix_index = m_buffer.find(PKT_PREFIX_BYTES)
		if (prefix_index == 0):
			# found HEADER
			_, cmd_id, payload_length = struct.unpack_from(FMT_PKT_HEADER, m_buffer, 0)
			packet_length = PKT_HEADER_SIZE + payload_length
			if (buffer_len >= (packet_length)):
				print(f'   cmd_id = {cmd_id:04x}, length = {payload_length:08x}')
				pakcet = m_buffer[:packet_length]
				print(f'recevied packet = {pakcet.hex()}')
				m_buffer = m_buffer[packet_length:]
			else:
				continue
		elif (prefix_index > 0):
			# found PKT_PREFIX
			tresh_data = m_buffer[:prefix_index]
			print(f'tresh data dropped ({prefix_index}) = {tresh_data.hex()}')
			m_buffer = m_buffer[prefix_index:]
		else:
			# wrong data => clear buffer
			m_buffer = bytes()
	
	last_received = time.time()

print(m_buffer.hex())
