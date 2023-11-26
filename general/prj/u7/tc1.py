# test code 1
# make hbesthee@naver.com
# date 2023-11-22

from struct import unpack
from typing import Final

REQ_422_COMM_STATUS: Final				= 0x10

PKT_422_FORMAT: Final					= 'BBB'


recv_packet = bytes([0x11, 0x11, 0x03])
cmd_id, status_low, status_hi = unpack(PKT_422_FORMAT, recv_packet)
if (cmd_id == (REQ_422_COMM_STATUS + 1)):
	comm_status = (status_hi << 8) | status_low
	print(f'{comm_status=:04X}')
