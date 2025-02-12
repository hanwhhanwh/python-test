


def get_cidr_bit_count_for_netmask_old(netmask: str) -> int:
	""" netmask 문자열을 받아서 CIDR 형식으로 1 비트 개수를 반환합니다.

	Returns:
		int: netmask의 1 비트의 개수
	"""
	octets = netmask.split(".")
	cidr = 0
	for octet in octets:
		# 10진수로 변환 후 이진수로 변환하여 1의 개수를 세기
		cidr += bin(int(octet)).count("1")
	return cidr



def get_cidr_bit_count_for_netmask(netmask: str) -> int:
	""" netmask 문자열을 받아서 CIDR 형식으로 1 비트 개수를 반환합니다.

	Returns:
		int: netmask의 1 비트의 개수
	"""
	return sum(bin(int(x)).count('1') for x in netmask.split('.'))


netmask = "255.255.255.0"
cidr = get_cidr_bit_count_for_netmask_old(netmask)
print(f'1. "{netmask}" CIDR bit count= {cidr}')

cidr = get_cidr_bit_count_for_netmask(netmask)
print(f'2. "{netmask}" CIDR bit count = {cidr}')
