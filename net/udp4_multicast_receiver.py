# -*- coding: utf-8 -*-
# IPv4 UDP Multicast 수신 서버 예제
# made : hbesthee@naver.com
# date : 2025-09-23
# reference: https://dev.to/pikotutorial/udp-multicasting-with-python-ob9

import struct
import traceback
from argparse import ArgumentParser
from socket import gethostbyname, gethostname, inet_aton, socket, \
	AF_INET, SOCK_DGRAM, IPPROTO_IP, IPPROTO_UDP, \
	IP_ADD_MEMBERSHIP, INADDR_ANY, SOL_SOCKET, SO_REUSEADDR
from struct import pack

# define command line interface
parser = ArgumentParser(description='UDP Multicast Receiver')
parser.add_argument('-mc_address', default='224.0.0.1:9999', help='Multicast address')
# parse command line options
args = parser.parse_args()
try:
	multicast_addr, multicast_port = args.mc_address.split(':')
	# create a IPv4 UDP socket
	sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
	# 여러 소켓에서 바인딩 허용 ; on the socket level, set the ability to reuse address
	sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	# bind the socket to the receiver's own address and port
	# 윈도우는 멀티캐스트 그룹이 아니라 0.0.0.0로 바인딩해야 함
	sock.bind(("0.0.0.0", int(multicast_port)))
	# sock.bind((multicast_addr, int(multicast_port)))
	# 로컬 NIC IP 주소 가져오기 (예: 192.168.0.10)
	local_ip = gethostbyname(gethostname())
	# set up the multicast group membership by converting addresses to
	multicast_req = pack("4s4s", inet_aton(multicast_addr), inet_aton(local_ip))
	# # 4sl (4 byte string and 4 byte long integer)
	# multicast_request = struct.pack("4sl", inet_aton(multicast_addr), INADDR_ANY)
	# 멀티캐스트 그룹 가입 ; join the multicast group
	sock.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, multicast_req)
	print(f'Receiver listening on {multicast_addr}:{multicast_port}')
	# receive messages (in this case, indefinitely until interrupted)
	data, sender_address = sock.recvfrom(1024)  # Buffer size 1024 bytes
	print(f'Received message from {sender_address[0]}:{sender_address[1]} : {data.decode()}')
except Exception as e:
	print(f"Error: {e}")
	traceback.print_exc()
