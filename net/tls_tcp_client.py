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



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



async def main() -> None:
	"""클라이언트 예제"""
	logging.basicConfig(level=logging.INFO)

	client = TlsTcp6Client(
		cert_file="conf/evcc_ee.crt",
		key_file="conf/evcc_ee.key",
		ca_file="conf/root.crt",
		check_hostname=False
	)

	try:
		# 서버 연결
		await client.connect("::1", 8443)

		# 파서 시작
		parser = BaseParser(client.receive_queue)
		parser_task = asyncio.create_task(parser.start_parsing())

		# 테스트 메시지 전송
		test_message = b"Hello, TLS IPv6 Server!"
		await client.send_data(test_message)
		print(f"전송: {test_message}")

		# 에코 응답 수신 대기
		echo_response = await asyncio.wait_for(parser.message_queue.get(), timeout=5.0)
		print(f"수신: {echo_response}")

		if echo_response == test_message:
			print("에코 테스트 성공!")
		else:
			print("에코 테스트 실패!")

	except Exception as e:
		print(f"클라이언트 오류: {e}")
	finally:
		await client.disconnect()



if (__name__ == "__main__"):
	asyncio.run(main())