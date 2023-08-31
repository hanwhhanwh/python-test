# reference : https://stackoverflow.com/questions/25239423/
#	https://crccalc.com/

POLYNOMIAL = 0x1021
PRESET = 0xFFFF

def _initial(c):
	crc = 0
	c = c << 8
	for j in range(8):
		if (crc ^ c) & 0x8000:
			crc = (crc << 1) ^ POLYNOMIAL
		else:
			crc = crc << 1
		c = c << 1
	return crc

_tab = [ _initial(i) for i in range(256) ]

def _update_crc(crc, c):
	cc = c & 0xff

	tmp = (crc >> 8) ^ cc
	crc = (crc << 8) ^ _tab[tmp & 0xff]
	crc = crc & 0xffff
	#print (crc)

	return crc

def crc16bytes(data_bytes):
	crc = PRESET
	for byte in data_bytes:
		crc = _update_crc(crc, (byte))
	return crc

def crc16str(str):
	crc = PRESET
	for c in str:
		crc = _update_crc(crc, ord(c))
	return crc

def crc16(*data):
	crc = PRESET
	for item in data:
		crc = _update_crc(crc, (item))
	return crc

if __name__ == '__main__':
	print(hex(crc16bytes(b'123456789')))
	print(hex(crc16str('123456789')))
	print(hex(crc16(0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39)))
