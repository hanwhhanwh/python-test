# -*- coding: utf-8 -*-
# network 정보 (ip, gateway, subnetmask, dns 등) 얻는 방법 예시
# made : hbesthee@naver.com
# date : 2025-02-22

import platform
import re
import socket
import subprocess


import netifaces


def get_network_info():
	info = {}

	# 운영체제 확인
	os_type = platform.system().lower()

	try:
		# IP 주소 가져오기
		hostname = socket.gethostname()
		info['IP'] = socket.gethostbyname(hostname)

		# 기본 게이트웨이 가져오기
		gws = netifaces.gateways()
		default_gateway = gws['default'][netifaces.AF_INET][0]
		info['Gateway'] = default_gateway

		# 서브넷 마스크 가져오기
		for interface in netifaces.interfaces():
			addrs = netifaces.ifaddresses(interface)
			if netifaces.AF_INET in addrs:
				for addr in addrs[netifaces.AF_INET]:
					if 'netmask' in addr:
						info['Subnetmask'] = addr['netmask']
						break
		
		# DNS 서버 정보 가져오기
		if os_type == 'windows':
			output = subprocess.check_output('ipconfig /all', shell=True).decode()
			dns_servers = re.findall(r'DNS Servers[^\n]+:\s*([^\n]+)', output)
			info['DNS'] = dns_servers if dns_servers else 'Not found'
		else:  # Linux/Mac
			with open('/etc/resolv.conf', 'r') as f:
				dns_servers = re.findall(r'nameserver\s+([^\n]+)', f.read())
				info['DNS'] = dns_servers if dns_servers else 'Not found'
		
		# DHCP 사용 여부 확인
		if os_type == 'windows':
			output = subprocess.check_output('ipconfig /all', shell=True).decode()
			dhcp_enabled = 'DHCP Enabled. . . . . . . . . . . : Yes' in output
			info['DHCP'] = 'Enabled' if dhcp_enabled else 'Disabled'
		else:  # Linux/Mac
			try:
				output = subprocess.check_output('ps aux | grep dhclient', shell=True).decode()
				info['DHCP'] = 'Enabled' if 'dhclient' in output else 'Disabled'
			except:
				info['DHCP'] = 'Unknown'
				
	except Exception as e:
		print(f"Error occurred: {str(e)}")
		return None
		
	return info

if __name__ == "__main__":
	network_info = get_network_info()
	if network_info:
		print("\n=== 네트워크 상태 정보 ===")
		for key, value in network_info.items():
			print(f"{key}: {value}")