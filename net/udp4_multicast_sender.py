# -*- coding: utf-8 -*-
# IPv4 UDP Multicast 송신 클라이언트 예제
# made : hbesthee@naver.com
# date : 2025-09-23
# reference: https://dev.to/pikotutorial/udp-multicasting-with-python-ob9

import time
import traceback
from argparse import ArgumentParser
from socket import gethostbyname, gethostname, inet_aton, socket, \
		AF_INET, SOCK_DGRAM, IP_ADD_MEMBERSHIP, IPPROTO_IP, IPPROTO_UDP, IP_MULTICAST_IF, IP_MULTICAST_TTL
from struct import pack
# define command line interface
parser = ArgumentParser()
parser.add_argument('-sender_address', default='127.0.0.1:3003',
					help='Sender\'s source address')
parser.add_argument('-mc_address', default='224.0.0.1:9999',
					help='List of multicast addresses separated by space')
# parse command line options
args = parser.parse_args()
# create a UDP socket
multicast_ip, multicast_port = args.mc_address.split(':')
try:
	# 소켓 생성 (IPv4, UDP)
	sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
	# TTL 설정 (1: 같은 서브넷까지만 전송)
	ttl = b'\x01'
	sock.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, ttl)
	# 송신할 로컬 NIC IP (예: 192.168.0.10) 반드시 실제 IP로 지정
	local_ip = gethostbyname(gethostname())
	# local_ip = "192.168.123.137"
	print(f"{local_ip=}")
	sock.setsockopt(IPPROTO_IP, IP_MULTICAST_IF, inet_aton(local_ip))
	# assign sender specific source port
	sock.sendto(f'This message is for {multicast_ip}:{multicast_port} receivers'.encode(),
						(multicast_ip, int(multicast_port)))
except Exception as e:
	print(f"Error: {e}")
	traceback.print_exc()