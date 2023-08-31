import struct
from typing import Final


class PacketHeader:
	""" 패킷 헤더 처리를 위한 클래스
	"""
	PREFIX: Final = [0x03, 0x4d]
	CMD_DATA_REQUEST: Final = 0x0600
	CMD_INIT_REQUEST: Final = 0x0601
	
	def __init__(self, cmd_id):
		self.cmd_id = cmd_id
		self.payload_size = 17
		self.checksum = 0


	def getBytesDataReq(self):
		result = struct.pack('<bbHIIIII'
				, 0x03, 0x4d			# PREFIX
				, self.cmd_id			# Command ID
				, self.payload_size		# Payload Size
				, 0x00000000			# reserved
				, 0x00000000			# reserved
				, 0x00000000			# reserved
				, 0x00000000			# reserved
			)
		for value in result:
			self.checksum += value
		#print(struct.pack('b', self.checksum & 0xff))
		return b''.join( [result, struct.pack('b', self.checksum & 0xff)] )


if __name__ == "__main__":
	req_data = PacketHeader(0x0601)
	print(req_data.getBytesDataReq().hex())
