# -*- coding: utf-8 -*-
# TLS TCP6 서버 예제
# made : whhan@cnuglobal.com
# date : 2025-07-02

# Original Packages
import asyncio
import logging



# User's Package 들을 포함시키기 위한 sys.path에 프로젝트 폴더 추가하기
from os import getcwd
from sys import path as sys_path
project_folder = getcwd()
print(f'{project_folder=}')
if (not project_folder in sys_path):
	sys_path.append(str(project_folder))


# User's Package
from lib.tls_tcp6 import BaseParser, TlsTcp6Server



logging.basicConfig(level=logging.INFO)



async def main() -> None:
	"""서버 사용 예제"""
	# 로깅 설정
	logging.basicConfig(level=logging.INFO)

	# 서버 인스턴스 생성
	server = TlsTcp6Server(host="::", port=8443)

	try:
		# 서버 시작
		await server.start_server(
			cert_file="conf/secc_ee.crt",
			key_file="conf/secc_ee.key",
			ca_file="conf/root.crt"
		)
	except KeyboardInterrupt:
		print("서버 종료 중...")
	finally:
		await server.stop_server()



if (__name__ == "__main__"):
	asyncio.run(main())