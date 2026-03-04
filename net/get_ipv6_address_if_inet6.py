# -*- coding: utf-8 -*-
# IPv6 주소 얻기 Windows 예제
# made : hbesthee@naver.com
# date : 2026-03-04

# Original Packages
from subprocess import CalledProcessError, check_output, STDOUT


def get_ipv6_address_ip(interface: str) -> list[str]:
	"""
	Linux 환경에서 ip 명령을 이용하여 IPv6 주소 목록을 반환한다.

	Args:
		interface (str): 네트워크 인터페이스 이름 (예: 'eth2')

	Returns:
		list[str]: IPv6 주소 목록 (CIDR 표기 포함, 예: 'fe80::1/64')
	"""
	try:
		output = check_output(
			["ip", "-6", "addr", "show", "dev", interface],
			stderr=STDOUT,
			text=True,
		)
	except CalledProcessError as e:
		print(f"오류 발생: {e.output.strip()}")
		return []

	addresses = []
	for line in output.splitlines():
		line = line.strip()
		if (line.startswith("inet6")):
			parts = line.split()
			addresses.append(parts[1])  # CIDR 표기 (예: fe80::1/64)

	return addresses


def get_ipv6_address_from_proc(interface: str) -> list[str]:
	"""
	/proc/net/if_inet6 파일을 파싱하여 IPv6 주소 목록을 반환한다.

	Args:
		interface (str): 네트워크 인터페이스 이름 (예: 'eth2')

	Returns:
		list[str]: IPv6 주소 목록 (CIDR 표기 포함, 예: 'fe80::1/64')
	"""
	PROC_IF_INET6 = "/proc/net/if_inet6"

	try:
		with open(PROC_IF_INET6, "r") as f:
			lines = f.readlines()
	except OSError as e:
		print(f"파일 읽기 오류: {e}")
		return []

	addresses = []
	for line in lines:
		parts = line.split()
		# 형식: <주소(hex)> <인터페이스인덱스> <프리픽스길이> <스코프> <플래그> <인터페이스명>
		if (len(parts) != 6 or parts[5] != interface):
			continue

		hex_addr = parts[0]  # 예: fe800000000000000200e8fffe123456
		prefix_len = int(parts[2], 16)  # 16진수 프리픽스 길이

		# 32자리 hex → IPv6 주소 형식으로 변환
		ipv6 = ":".join(hex_addr[i:i+4] for i in range(0, 32, 4))

		addresses.append(f"{ipv6}/{prefix_len}")

	return addresses


def main():
	interface = "eth2"  # 인터페이스 이름
	ipv6_addr = get_ipv6_address_ip(interface)
	if (ipv6_addr):
		print(f"[{interface}] IPv6 주소 : {ipv6_addr}")
	else:
		print(f"[{interface}] IPv6 주소를 찾을 수 없습니다.")

	ipv6_addr2 = get_ipv6_address_from_proc(interface)
	if (ipv6_addr2):
		print(f"[{interface}] IPv6 주소 : {ipv6_addr2}")
	else:
		print(f"[{interface}] IPv6 주소를 찾을 수 없습니다.")


if (__name__ == "__main__"):
	main()

"""
ip 명령 출력 예시

$ ip -6 addr show dev eth2
4: eth2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qlen 100
    inet6 fe80::2b0:52ff:fe83:21a1/64 scope link
       valid_lft forever preferred_lft forever


/proc/net/if_inet6 파일 출력 예시

$ cat /proc/net/if_inet6
00000000000000000000000000000001 01 80 10 80       lo
fe8000000000000002b052fffe8321a1 04 40 20 80     eth2
fe80000000000000dc939bfffe5c3190 03 40 20 80     eth1
"""