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
from lib.tls_tcp6 import BaseParser, TlsTcp6Def, TlsTcp6Server


logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s - %(funcName)s:%(lineno)d - %(levelname)s - %(message)s')



async def main():
	server = TlsTcp6Server(
		cert_file="conf/server.crt",
		key_file="conf/server.key",
		ca_file="conf/root.crt",
	)

	try:
		# 서버 시작
		await server.start()

	except Exception as e:
		print(f"Server interrupted: {e}")
	finally:
		# 서버 중지
		# await server.stop()
		print(f"Server stopped.")


import tracemalloc

tracemalloc.start()
try:
	asyncio.run(main())
except Exception as e:
	print(f'error: {e}')

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)