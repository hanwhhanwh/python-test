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



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



async def main() -> None:
	"""에코 서버 예제"""
	logging.basicConfig(level=logging.INFO)

	server = TlsTcp6Server(
		host="::1",  # IPv6 localhost
		port=8443,
		cert_file="conf/secc_ee.crt",
		key_file="conf/secc_ee.key",
		ca_file="conf/root.crt"
	)

	# 파서 시작
	parser = BaseParser(server.receive_queue)
	parser_task = asyncio.create_task(parser.start_parsing())

	# 서버 시작
	server_task = asyncio.create_task(server.start_server())

	# 에코 처리 루프
	async def echo_handler():
		while True:
			try:
				message = await asyncio.wait_for(parser.message_queue.get(), timeout=1.0)
				# 수신된 데이터를 모든 클라이언트에게 에코
				await server.broadcast(message)
				print(f"에코: {message}")
			except asyncio.TimeoutError:
				continue
			except Exception as e:
				print(f"에코 처리 오류: {e}")

	echo_task = asyncio.create_task(echo_handler())

	try:
		await asyncio.gather(server_task, parser_task, echo_task)
	except KeyboardInterrupt:
		print("서버 종료 중...")
		parser.stop()
		await server.stop_server()



if (__name__ == "__main__"):
	asyncio.run(main())