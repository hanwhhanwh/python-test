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



logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s - %(lineno)d - %(levelname)s - %(message)s')

async def main():
	client = TlsTcp6Client(
		cert_file="conf/client.crt",
		key_file="conf/client.key",
		ca_file="conf/root.crt",
		check_hostname=False
	)
	
	try:
		# 서버 연결
		await client.start()
		
		# 메시지 송신
		await client.send(b"Hello Server!")
		# await asyncio.sleep(0.5)
		uuid, packet = await client.packet_queue.get()
		print(f"{packet=}")
		client.packet_queue.task_done()
		
		await client.send(b"How are you?")
		# await asyncio.sleep(0.5)
		uuid, packet = await client.packet_queue.get()
		print(f"{packet=}")
		client.packet_queue.task_done()
		
		# 연결 유지
		await asyncio.sleep(3)
		
	except Exception as e:
		print(f"Client error: {e}")
	finally:
		# 연결 해제
		await client.close()



asyncio.run(main())
