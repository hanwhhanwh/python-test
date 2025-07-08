# -*- coding: utf-8 -*-
# Library PyTest config
# made : hbesthee@naver.com
# date : 2025-07-07

# Original Packages
from typing import AsyncGenerator, Dict, Type

import asyncio
import os
import ssl



# Third-party Packages
import pytest_asyncio



# User's Package 들을 포함시키기 위한 sys.path에 프로젝트 폴더 추가하기
from os import getcwd
from sys import path as sys_path
project_folder = getcwd()
print(f'{project_folder=}')
if (not project_folder in sys_path):
	sys_path.append(str(project_folder))


# User's Package
from lib.tls_tcp6 import BaseParser, TlsTcp6Client, TlsTcp6Def, TlsTcp6Key, TlsTcp6Server




@pytest_asyncio.fixture(scope="session")
def certs() -> Dict[str, str]:
	"""테스트에 필요한 인증서 파일 경로를 제공하는 Fixture"""
	conf_path = ("./conf")
	# 테스트 실행 전 인증서 파일 존재 여부 확인
	required_files = ["server.crt", "server.key", "client.crt", "client.key", "root.crt"]
	for f in required_files:
		if (not os.path.exists(conf_path)):
			pytest.fail(f"인증서 폴더가 없습니다: '{conf_path}'. README의 생성 가이드를 참고하세요.")

	return {
		"server_cert": str(f"{conf_path}/server.crt"),
		"server_key": str(f"{conf_path}/server.key"),
		"client_cert": str(f"{conf_path}/client.crt"),
		"client_key": str(f"{conf_path}/client.key"),
		"ca": str(f"{conf_path}/root.crt"),
	}


# @pytest.fixture(scope="function")
@pytest_asyncio.fixture(scope="function")
async def server(certs: Dict[str, str], unused_tcp_port: int, request) -> AsyncGenerator[TlsTcp6Server, None]:
	"""테스트용 서버를 백그라운드에서 실행하고 테스트 종료 후 정리하는 Fixture"""

	# request.param을 통해 테스트별로 다른 파라미터(파서 등)를 받을 수 있음
	parser_class = getattr(request, "param", {}).get("parser_class", BaseParser)
	idle_timeout = getattr(request, "param", {}).get("idle_timeout", 5) # 테스트를 위해 타임아웃 단축

	server_instance = TlsTcp6Server(
		cert_file=certs["server_cert"],
		key_file=certs["server_key"],
		ca_file=certs["ca"],
		host="::1",
		port=unused_tcp_port,
		parser_class=parser_class,
		idle_timeout=idle_timeout,
	)

	server_task = asyncio.create_task(server_instance.start())
	# 서버가 완전히 시작될 때까지 잠시 대기
	await asyncio.sleep(0.1)

	yield server_instance

	# 테스트 종료 후 정리
	await server_instance.stop()
	server_task.cancel()
	try:
		await server_task
	except asyncio.CancelledError:
		pass


# @pytest.fixture(scope="function")
@pytest_asyncio.fixture(scope="function")
async def client_factory(certs: Dict[str, str]):
	"""테스트용 클라이언트 인스턴스를 생성하는 팩토리 Fixture"""
	created_clients = []

	async def _create_client(port: int, parser_class: Type[BaseParser] = BaseParser) -> TlsTcp6Client:
		client_instance = TlsTcp6Client(
			cert_file=certs["client_cert"],
			key_file=certs["client_key"],
			ca_file=certs["ca"],
			host="::1",
			port=port,
			parser_class=parser_class,
			check_hostname=False,
		)
		created_clients.append(client_instance)
		return client_instance

	yield _create_client

	# 모든 생성된 클라이언트 정리
	for client in created_clients:
		if (not client._is_closing):
			await client.close()