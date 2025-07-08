# -*- coding: utf-8 -*-
# PyTest : TlsTcp6Server, TlsTcp6Client
# made : hbesthee@naver.com
# date : 2025-07-07

# Original Packages
from asyncio import Queue
from uuid import UUID

import asyncio
import logging
import os
import ssl
import struct



# Third-party Packages
import pytest

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




### 테스트를 위한 커스텀 파서 정의
class LengthPrefixedParser(BaseParser):
	"""[4바이트 길이값][데이터] 형식의 메시지를 파싱하는 커스텀 파서"""
	def parse(self) -> list[bytes] | None:
		packets = []
		while True:
			if len(self._buf) < 4:
				break # 길이 정보를 읽을 수 없음

			msg_len = struct.unpack('!I', self._buf[:4])[0]

			if len(self._buf) < 4 + msg_len:
				break # 전체 메시지가 아직 도착하지 않음

			packet = self._buf[4 : 4 + msg_len]
			packets.append(packet)

			# 처리된 메시지를 버퍼에서 제거
			self._buf = self.self._buf[4 + msg_len:]

		return packets if packets else None



### 테스트 유틸리티 함수
async def wait_for_client_count(server: TlsTcp6Server, count: int, timeout: float = 3.0):
	"""서버의 클라이언트 수가 특정 값에 도달할 때까지 대기"""
	waited = 0
	while len(server._clients) != count:
		await asyncio.sleep(0.01)
		waited += 0.01
		if waited > timeout:
			pytest.fail(f"Timeout: 클라이언트 수가 {count}가 되지 않았습니다 (현재: {len(server._clients)})")



### 테스트 클래스

# @pytest.mark.timeout(10) # 각 테스트는 10초 내에 완료되어야 함
class TestConnectionStability:
	"""네트워크 연결 안정성 테스트"""

	@pytest.mark.asyncio
	async def test_server_startup(self, server: TlsTcp6Server):
		"""1. 서버가 정상적으로 시작되는지 검증"""
		assert server._server_task is not None
		assert server._is_server is True


	@pytest.mark.asyncio
	async def test_single_client_connect_disconnect(self, server: TlsTcp6Server, client_factory):
		"""2. 단일 클라이언트의 정상적인 연결 및 해제 검증"""
		client = await client_factory(server.port)
		await client.start()
		assert client._rx_stream is not None and client._tx_stream is not None
		await wait_for_client_count(server, 1)
		assert len(server._clients) == 1

		await client.close()
		await wait_for_client_count(server, 0)
		assert len(server._clients) == 0


	@pytest.mark.asyncio
	async def test_multiple_clients_connect(self, server: TlsTcp6Server, client_factory):
		"""3. 다중 클라이언트(3개)가 동시 접속 가능한지 검증"""
		clients = await asyncio.gather(
			client_factory(server.port),
			client_factory(server.port),
			client_factory(server.port)
		)
		await asyncio.gather(*(c.start() for c in clients))
		await wait_for_client_count(server, 3)
		assert len(server._clients) == 3


	@pytest.mark.asyncio
	async def test_data_echo(self, server: TlsTcp6Server, client_factory):
		"""4. 클라이언트가 보낸 데이터가 서버로부터 정상적으로 에코되는지 검증"""
		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)

		test_message = b"hello world"
		await client.send(test_message)
		await asyncio.sleep(0.5)

		uuid, packet = await client.packet_queue.get()
		assert isinstance(uuid, UUID)
		assert packet.encode() == test_message


	@pytest.mark.asyncio
	async def test_sequential_connect_disconnect(self, server: TlsTcp6Server, client_factory):
		"""5. 한 클라이언트가 연결-해제-재연결을 반복해도 정상 동작하는지 검증"""
		for i in range(3):
			client = await client_factory(server.port)
			await client.start()
			await wait_for_client_count(server, 1, timeout=5)
			assert len(server._clients) == 1

			await client.send(f"ping {i}".encode())
			_, packet = await client.packet_queue.get()
			assert packet == f"ping {i}"

			await client.close()
			await wait_for_client_count(server, 0, timeout=5)
			assert len(server._clients) == 0


	@pytest.mark.asyncio
	async def test_large_data_transmission(self, server: TlsTcp6Server, client_factory):
		"""6. 대용량 데이터(1MB)가 손실 없이 전송되는지 검증"""
		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)

		large_message = b'A' * (1024 * 1024) # 1MB
		await client.send(large_message)

		all_data = ''
		while True:
			try:
				_, packet = await asyncio.wait_for(client.packet_queue.get(), timeout=1)
				all_data += packet
			except Exception:
				break
		assert all_data.encode() == large_message


	@pytest.mark.asyncio
	async def test_concurrent_data_echo(self, server: TlsTcp6Server, client_factory):
		"""7. 여러 클라이언트가 동시에 데이터를 보냈을 때 각자 올바른 응답을 받는지 검증"""
		async def client_task(msg_id):
			client = await client_factory(server.port)
			await client.start()
			message = f"message from {msg_id}".encode()
			await client.send(message)
			_, packet = await client.packet_queue.get()
			assert packet.encode() == message
			await client.close()

		tasks = [asyncio.create_task(client_task(i)) for i in range(5)]
		await asyncio.gather(*tasks)
		await wait_for_client_count(server, 0)


	@pytest.mark.asyncio
	async def test_server_initiated_close(self, server: TlsTcp6Server, client_factory):
		"""8. 서버가 먼저 연결을 종료했을 때 클라이언트가 이를 감지하는지 검증"""
		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)

		# 서버에서 클라이언트 객체를 찾아 종료
		client_conn_uuid = list(server._clients.keys())[0]
		client_conn_socket = server._clients[client_conn_uuid]
		await client_conn_socket.close()

		# 클라이언트의 태스크가 정상 종료되는지 확인
		await asyncio.sleep(0.2)
		assert client._is_closing is True
		for task in client._tasks:
			assert task.done() is True


	@pytest.mark.asyncio
	async def test_tls_version_is_1_3(self, server: TlsTcp6Server, client_factory):
		"""9. 연결된 세션의 TLS 버전이 1.3인지 검증"""
		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)
		ssl_obj = client._tx_stream.get_extra_info('ssl_object')
		assert ssl_obj.version() == 'TLSv1.3'



class TestNetworkInstability:
	"""네트워크 불안정 상황에 대한 안정성 테스트"""

	@pytest.mark.asyncio
	async def test_client_handles_server_not_running(self, client_factory, unused_tcp_port):
		"""10. 서버가 실행되지 않았을 때 클라이언트가 ConnectionRefusedError를 처리하는지 검증"""
		client = await client_factory(unused_tcp_port)
		await client.start() # 연결 시도
		assert client._is_closing is True # 연결 실패 후 스스로 close 해야 함
		assert client._rx_stream is None


	@pytest.mark.asyncio
	async def test_server_handles_abrupt_client_disconnect(self, server: TlsTcp6Server, client_factory):
		"""11. 클라이언트가 비정상 종료되었을 때 서버가 리소스를 정리하는지 검증"""
		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)

		# 소켓을 강제로 닫아 비정상 종료 흉내
		client._tx_stream.close()
		await client._tx_stream.wait_closed()

		await wait_for_client_count(server, 0, timeout=5) # 서버가 연결 종료를 감지하고 정리해야 함
		assert len(server._clients) == 0


	@pytest.mark.asyncio
	@pytest.mark.parametrize("server", [{"idle_timeout": 1}], indirect=True)
	async def test_idle_timeout(self, server: TlsTcp6Server, client_factory):
		"""12. 유휴 상태의 클라이언트가 설정된 시간(1초) 후 자동으로 연결 종료되는지 검증"""
		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)

		await asyncio.sleep(2) # idle_timeout(1초)보다 길게 대기

		await wait_for_client_count(server, 0, timeout=3)
		assert len(server._clients) == 0
		assert client._is_closing is True


	@pytest.mark.asyncio
	async def test_send_to_closed_socket_by_client(self, server: TlsTcp6Server, client_factory):
		"""13. 클라이언트가 이미 닫힌 소켓에 데이터 전송 시도 시 에러 없이 처리하는지 검증"""
		client = await client_factory(server.port)
		await client.start()
		await client.close()

		# 예외가 발생하지 않아야 함
		await client.send(b'data to closed socket')
		assert client.packet_queue.qsize() == 0


	@pytest.mark.asyncio
	async def test_malformed_utf8_data(self, server: TlsTcp6Server, client_factory, caplog):
		"""14. 기본 파서가 처리할 수 없는 (잘못된 UTF-8) 데이터 수신 시 서버가 안정적인지 검증"""
		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)

		# 잘못된 바이트 시퀀스 전송
		await client.send(b'\xff\xfe\xfd')

		# 서버는 안정적으로 유지되어야 하고, 클라이언트 수는 1이어야 함
		await asyncio.sleep(0.1)
		assert len(server._clients) == 1
		assert "UTF-8 디코딩 실패" in caplog.text


	@pytest.mark.asyncio
	async def test_client_with_bad_ca_is_rejected(self, server, certs, unused_tcp_port):
		"""15. 잘못된 CA로 서명된 클라이언트 인증서 접속이 거부되는지 검증"""
		# 별도의 자체 서명된 인증서 생성 (테스트용)
		bad_cert = "conf/bad_client.crt"
		bad_key = "conf/bad_client.key"
		if not os.path.exists(bad_cert):
			pytest.skip("테스트를 위한 bad_client 인증서가 없습니다.")

		bad_client = TlsTcp6Client(
			cert_file=bad_cert,
			key_file=bad_key,
			ca_file=certs["ca"],
			host="::1",
			port=server.port,
			check_hostname=False,
		)
		with pytest.raises(ssl.SSLError):
			# SSLError가 발생해야 정상
			await asyncio.wait_for(bad_client.start(), timeout=2)



# 이 스크립트를 직접 실행하면 pytest를 통해 테스트를 실행합니다.
if (__name__ == "__main__"):
	pytest.main(["-v", __file__])
