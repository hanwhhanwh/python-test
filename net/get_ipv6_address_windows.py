# -*- coding: utf-8 -*-
# IPv6 주소 얻기 Windows 예제
# made : hbesthee@naver.com
# date : 2026-03-04

# Original Packages
from subprocess import CalledProcessError, check_output, STDOUT


def get_ipv6_address_windows(interface: str) -> list[str]:
	"""
	Windows 환경에서 netsh 명령을 이용하여 IPv6 주소 목록을 반환한다.

	Args:
		interface (str): 네트워크 인터페이스 이름 (예: 'eth2', '이더넷 2')

	Returns:
		list[str]: IPv6 주소 목록 (CIDR 표기 포함, 예: 'fe80::1/64')
	"""
	try:
		output = check_output(
			["netsh", "interface", "ipv6", "show", "address", f"interface={interface}"],
			stderr=STDOUT,
			text=True,
			encoding="utf-8",
		)
	except CalledProcessError as e:
		print(f"오류 발생: {e.output.strip()}")
		return []

	addresses = []
	for line in output.splitlines():
		line = line.strip()
		# 주소 유형 키워드로 시작하는 줄에서 IPv6 주소 추출
		# 예: "주소 fe80::ea38:2e8a:a5c:cec5%10 매개 변수"
		# 예: "address fe80::200:e8ff:fe12:3456%5"
		for keyword in ("주소", "address"):
			if (line.lower().startswith(keyword.lower())):
				parts = line.split()
				if (len(parts) >= 2):
					# 인터페이스 인덱스 접미사 제거 (예: %5)
					addr = parts[1].split("%")[0]
					addresses.append(addr)
					break 
		if (len(addresses) > 0):
			break

	return addresses


def main():
	interface = "이더넷"  # Windows 인터페이스 이름
	ipv6_list = get_ipv6_address_windows(interface)

	if (ipv6_list):
		print(f"[{interface}] IPv6 주소 목록:")
		for addr in ipv6_list:
			print(f"  {addr}")
	else:
		print(f"[{interface}] IPv6 주소를 찾을 수 없습니다.")


if (__name__ == "__main__"):
	main()

"""
netsh 출력 예시

> netsh interface ipv6 show address interface="이더넷"

주소 fe80::ea38:2e88:b5c:4ec5%10 매개 변수
---------------------------------------------------------
인터페이스 LUID     : 이더넷
범위 ID             : 0.10
유효한 수명         : infinite
기본 수명           : infinite
DAD 상태            : 기본 설정
주소 유형           : 기타
원본으로 건너뛰기   : false
"""