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



# User's Package 들을 포함시키기 위한 sys.path에 프로젝트 폴더 추가하기
from os import getcwd
from sys import path as sys_path
project_folder = getcwd()
print(f'{project_folder=}')
if (not project_folder in sys_path):
	sys_path.append(str(project_folder))


# User's Package
from lib.tls_tcp6 import BaseParser, TlsTcp6Client, TlsTcp6Def, TlsTcp6Key, TlsTcp6Server, TlsTcp6Socket




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

# # @pytest.mark.timeout(10) # 각 테스트는 10초 내에 완료되어야 함
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
	async def test_data_echo(self, server: TlsTcp6Server, client_factory, caplog):
		"""4. 클라이언트가 보낸 데이터가 서버로부터 정상적으로 에코되는지 검증"""
		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)

		test_message = b"hello world"
		await client.send(test_message)

		print(caplog.text)
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



class TestResourceManagement:
	"""메모리 누수 관련 리소스 관리 테스트"""

	@pytest.mark.asyncio
	async def test_client_dict_cleanup(self, server: TlsTcp6Server, client_factory):
		"""16. 클라이언트 연결 해제 시 서버의 _clients 딕셔너리에서 완전히 제거되는지 검증"""
		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)
		client_uuid = list(server._clients.keys())[0]
		assert client_uuid in server._clients

		await client.close()
		await wait_for_client_count(server, 0)
		assert client_uuid not in server._clients


	@pytest.mark.asyncio
	async def test_task_cancellation_on_close(self, server: TlsTcp6Server, client_factory):
		"""17. 연결 종료 시 관련된 모든 태스크(_rx, _tx, _parser)가 취소되는지 검증"""
		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)

		client_in_server = list(server._clients.values())[0]

		# 태스크가 살아있는지 확인
		server_tasks = client_in_server._tasks.copy()
		client_tasks = client._tasks.copy()
		assert all(not t.done() for t in server_tasks)
		assert all(not t.done() for t in client_tasks)

		await client.close()
		await asyncio.sleep(0.2) # 정리 시간

		# 모든 태스크가 종료(취소)되었는지 확인
		assert all(t.done() for t in server_tasks)
		assert all(t.done() for t in client_tasks)


	@pytest.mark.asyncio
	async def test_many_connections_no_leak(self, server: TlsTcp6Server, client_factory):
		"""18. 다수의 클라이언트가 반복적으로 연결/해제해도 서버 리소스가 누수되지 않는지 검증"""
		initial_tasks = len(asyncio.all_tasks())

		for _ in range(10):
			clients = await asyncio.gather(*(client_factory(server.port) for _ in range(5)))
			await asyncio.gather(*(c.start() for c in clients))
			await wait_for_client_count(server, 5, timeout=5)
			await asyncio.gather(*(c.close() for c in clients))
			await wait_for_client_count(server, 0, timeout=5)

		assert len(server._clients) == 0
		# 태스크 수가 과도하게 늘어나지 않았는지 확인 (정확한 수치 비교는 어려움)
		final_tasks = len(asyncio.all_tasks())
		assert final_tasks < initial_tasks + 20 # 약간의 여유를 둠



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

			packet = self._buf[:4 + msg_len]
			packets.append(bytes(packet))

			# 처리된 메시지를 버퍼에서 제거
			del self._buf[:4 + msg_len]

		return packets if packets else None



@pytest.mark.parametrize("server", [{"parser_class": LengthPrefixedParser}], indirect=True)
class TestCustomParser:
	"""커스텀 파서(LengthPrefixedParser) 동작 검증"""

	@pytest.mark.asyncio
	async def test_custom_parser_setup(self, server: TlsTcp6Server):
		"""19. 서버와 클라이언트가 커스텀 파서로 초기화되었는지 검증"""
		assert isinstance(server._parser, LengthPrefixedParser)
		# 클라이언트 연결 시 서버의 파서 클래스를 상속받아 생성됨
		# 이 테스트는 서버 측 파서만 확인


	@pytest.mark.asyncio
	async def test_simple_packet_parsing(self, server: TlsTcp6Server, client_factory):
		"""20. 단일 패킷이 커스텀 파서로 정상 파싱되는지 검증"""
		client = await client_factory(server.port, parser_class=LengthPrefixedParser)
		await client.start()

		message = b"custom_packet"
		packet = struct.pack('!I', len(message)) + message
		await client.send(packet)

		_, received = await client.packet_queue.get()
		assert received == packet


	@pytest.mark.asyncio
	async def test_split_packet_assembly(self, server: TlsTcp6Server, client_factory):
		"""21. 나뉘어 전송된 패킷이 정상적으로 조합 및 파싱되는지 검증"""
		client = await client_factory(server.port, parser_class=LengthPrefixedParser)
		await client.start()

		message = b"reassembled_message"
		packet = struct.pack('!I', len(message)) + message

		# 패킷을 3조각으로 나눠서 전송
		await client.send(packet[:5])
		await asyncio.sleep(0.1)
		await client.send(packet[5:15])
		await asyncio.sleep(0.1)
		await client.send(packet[15:])

		_, received = await client.packet_queue.get()
		assert received == packet


	@pytest.mark.asyncio
	async def test_multiple_packets_in_one_send(self, server: TlsTcp6Server, client_factory):
		"""22. 한 번의 전송에 포함된 여러 패킷이 모두 파싱되는지 검증"""
		client = await client_factory(server.port, parser_class=LengthPrefixedParser)
		await client.start()

		msg1 = b"first"
		msg2 = b"second_long_message"
		pkt1 = struct.pack('!I', len(msg1)) + msg1
		pkt2 = struct.pack('!I', len(msg2)) + msg2

		await client.send(pkt1 + pkt2)

		_, rcv1 = await client.packet_queue.get()
		_, rcv2 = await client.packet_queue.get()

		assert {rcv1, rcv2} == {pkt1, pkt2}


	@pytest.mark.asyncio
	async def test_incomplete_packet_is_buffered(self, server: TlsTcp6Server, client_factory):
		"""23. 불완전한 패킷 수신 시, 파서가 처리를 보류하는지 검증"""
		client = await client_factory(server.port, parser_class=LengthPrefixedParser)
		await client.start()

		message = b"wait_for_it"
		packet = struct.pack('!I', len(message)) + message

		await client.send(packet[:-1]) # 마지막 1바이트를 보내지 않음

		# 큐에 데이터가 들어오면 안 됨
		with pytest.raises(asyncio.TimeoutError):
			await asyncio.wait_for(client.packet_queue.get(), timeout=0.5)

		# 나머지 데이터 전송
		await client.send(packet[-1:])
		_, received = await asyncio.wait_for(client.packet_queue.get(), timeout=0.5)
		assert received == packet


	@pytest.mark.asyncio
	async def test_invalid_length_packet(self, server: TlsTcp6Server, client_factory, caplog):
		"""24. 길이가 잘못된 패킷 수신 시 파서와 서버가 안정적으로 동작하는지 검증"""
		# 이 시나리오는 LengthPrefixedParser가 어떻게 에러를 처리하냐에 따라 달라짐
		# 현재 구현은 단순히 버퍼에 데이터가 쌓이게 되므로, 서버 안정성만 체크
		client = await client_factory(server.port, parser_class=LengthPrefixedParser)
		await client.start()
		await wait_for_client_count(server, 1)

		# 실제 길이(5)보다 긴 길이(100)를 헤더에 기록
		invalid_packet = struct.pack('!I', 100) + b'short'
		await client.send(invalid_packet)

		# 서버는 죽지 않아야 함
		await asyncio.sleep(0.2)
		assert len(server._clients) == 1
		# 큐는 비어있어야 함
		assert client.packet_queue.empty()



class TestExtraCases:
	"""다양한 엣지 케이스 및 추가 검증"""


	@pytest.mark.asyncio
	async def test_client_reconnection_after_server_restart(self, certs, client_factory, unused_tcp_port):
		"""25. 서버 재시작 후 클라이언트가 재접속 가능한지 검증"""
		# 1. 초기 서버 시작 및 클라이언트 접속
		server1 = TlsTcp6Server(cert_file=certs["server_cert"], key_file=certs["server_key"], ca_file=certs["ca"], host="::1", port=unused_tcp_port)
		s1_task = asyncio.create_task(server1.start())
		await asyncio.sleep(0.1)
		client = await client_factory(unused_tcp_port)
		await client.start()
		await wait_for_client_count(server1, 1)
		await client.close()

		# 2. 서버 종료
		await server1.stop()
		s1_task.cancel()

		# 3. 새 서버 시작
		server2 = TlsTcp6Server(cert_file=certs["server_cert"], key_file=certs["server_key"], ca_file=certs["ca"], host="::1", port=unused_tcp_port)
		s2_task = asyncio.create_task(server2.start())
		await asyncio.sleep(0.1)

		# 4. 클라이언트 재접속
		await client.start()
		await wait_for_client_count(server2, 1)
		assert len(server2._clients) == 1

		await server2.stop()
		s2_task.cancel()


	@pytest.mark.asyncio
	async def test_socket_object_inheritance(self, server, client_factory):
		"""26. 서버에서 생성된 클라이언트 연결 객체가 지정된 클래스의 인스턴스인지 검증"""
		class CustomSocket(TlsTcp6Socket):
			pass

		server._socket_class = CustomSocket
		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)

		client_conn = list(server._clients.values())[0]
		assert isinstance(client_conn, CustomSocket)


	@pytest.mark.asyncio
	async def test_packet_queue_sharing(self, server: TlsTcp6Server, client_factory):
		"""27. 여러 클라이언트가 하나의 패킷 큐를 정상적으로 공유하는지 검증"""
		clients = await asyncio.gather(*(client_factory(server.port) for _ in range(3)))
		await asyncio.gather(*(c.start() for c in clients))
		await wait_for_client_count(server, 3)

		for i, c in enumerate(clients):
			await c.send(f"msg_{i}".encode())

		received_msgs = set()
		# for _ in range(3):
		# 	uuid, packet = await server.packet_queue.get()
		# 	received_msgs.add(packet)
		for _, c in enumerate(clients):
			uuid, packet = await c.packet_queue.get()
			received_msgs.add(packet)

		assert received_msgs == {"msg_0", "msg_1", "msg_2"}


	@pytest.mark.asyncio
	async def test_server_ref_in_client_socket(self, server: TlsTcp6Server, client_factory):
		"""28. 서버에서 생성된 클라이언트 소켓이 서버 객체를 제대로 참조하는지 검증"""
		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)

		client_conn = list(server._clients.values())[0]
		assert client_conn.server is server


	@pytest.mark.asyncio
	async def test_process_received_data_override(self, server: TlsTcp6Server, client_factory):
		"""29. TlsTcp6Socket의 process_received_data 메소드 오버라이드가 동작하는지 검증"""
		class EncryptingSocket(TlsTcp6Socket):
			def process_received_data(self, data: bytes) -> bytes:
				# 간단한 XOR '암호화'
				return bytes([b ^ 0x42 for b in data])

		server._socket_class = EncryptingSocket

		client = await client_factory(server.port)
		await client.start()
		await wait_for_client_count(server, 1)

		original_msg = b'secret'
		# 서버가 수신 시 XOR 처리하므로, 클라이언트는 미리 XOR 처리된 데이터를 보내야 함
		encrypted_msg = bytes([b ^ 0x42 for b in original_msg])
		await client.send(encrypted_msg)

		# 서버의 기본 파서는 UTF-8 변환 후 큐에 넣음
		_, received = await client.packet_queue.get()
		assert received == original_msg.decode('utf-8')



# 이 스크립트를 직접 실행하면 pytest를 통해 테스트를 실행합니다.
if (__name__ == "__main__"):
	pytest.main(["-v", "-s", __file__])
	# pytest.main(["-s", __file__])
