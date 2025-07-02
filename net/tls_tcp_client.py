# -*- coding: utf-8 -*-
# TLS TCP6 클라이언트 예제
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
from lib.tls_tcp6 import BaseParser, TlsTcp6Client



logging.basicConfig(level=logging.INFO)



async def main() -> None:
	"""클라이언트 사용 예제"""
	# 로깅 설정
	logging.basicConfig(level=logging.INFO)

	# 클라이언트 인스턴스 생성
	client = TlsTcp6Client(check_hostname=False)

	try:
		# 서버 연결
		await client.connect(
			host="::1",
			port=8443,
			cert_file="conf/evcc_ee.crt",
			key_file="conf/evcc_ee.key",
			ca_file="conf/root.crt"
		)

		# 데이터 송신
		await client.send_data(b"Hello, Server!")

		# 파서 생성 및 시작
		parser = BaseParser(client.receive_queue)
		parser_task = asyncio.create_task(parser.start_parsing())

		# 메시지 수신 대기
		while True:
			try:
				message = await asyncio.wait_for(parser.get_message(), timeout=1.0)
				print(f"수신 메시지: {message}")
			except asyncio.TimeoutError:
				continue
			except KeyboardInterrupt:
				break

		parser.stop_parsing()
		await parser_task

	except Exception as e:
		print(f"클라이언트 오류: {e}")
	finally:
		await client.disconnect()



if (__name__ == "__main__"):
	asyncio.run(main())