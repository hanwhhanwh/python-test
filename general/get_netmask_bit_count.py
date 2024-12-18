# -*- coding: utf-8 -*-
# get bit counts from netmask example
# hbesthee@naver.com
# date	2024-12-18

from ipaddress import IPv4Address

def count_netmask_bits(netmask: str) -> int:
	# 점으로 구분된 IP 주소를 32비트 정수로 변환
	ip_int = int(''.join([bin(int(x)+256)[3:] for x in netmask.split('.')]), 2)
	
	# 1의 개수 세기
	return bin(ip_int).count('1')


def netmask_to_cidr(netmask: str) -> int:
	return sum(bin(int(x)).count('1') for x in netmask.split('.'))


def netmask_bits(netmask: str) -> int:
	return bin(int(IPv4Address(netmask))).count('1')

print("result =>")

# 255.255.255.0 → 24 bit
print(f"{count_netmask_bits('255.255.255.0')=}")  # count_netmask_bits('255.255.255.0')=24
print(f"{netmask_to_cidr('255.255.255.0')=}")  # netmask_to_cidr('255.255.255.0')=24
print(f"{netmask_bits('255.255.255.0')=}")  # netmask_bits('255.255.255.0')=24

# 255.255.252.0 → 22 bit
print(f"{count_netmask_bits('255.255.252.0')=}")  # count_netmask_bits('255.255.252.0')=22
print(f"{netmask_to_cidr('255.255.252.0')=}")  # netmask_to_cidr('255.255.252.0')=22
print(f"{netmask_bits('255.255.252.0')=}")  # netmask_bits('255.255.252.0')=22

# 255.255.2550.0 → error
print(f"{count_netmask_bits('255.255.2550.0')=}")  # count_netmask_bits('255.255.2550.0')=23
print(f"{netmask_to_cidr('255.255.2550.0')=}")  # netmask_to_cidr('255.255.2550.0')=24
print(f"{netmask_bits('255.255.2550.0')=}")  # Exception: ipaddress.AddressValueError: At most 3 characters permitted in '2550' in '255.255.2550.0'
