# -*- coding: utf-8 -*-
# IPv6 TLS TCP communication Framework
# made : hbesthee@naver.com
# date : 2025-07-02

# Original Packages
from asyncio import Queue, StreamReader, StreamWriter
from time import time
from typing import Dict, Any, Optional, Tuple, Callable

import asyncio
import logging
import socket
import ssl
import uuid




class TlsTcp6Socket:
	"""IPv6 TLS 통신을 위한 기본 소켓 클래스"""

	def __init__(self, cert_file: str, key_file: str, ca_file: Optional[str] = None,
				logger_name: str = "tls_tcp6"):
		"""
		TLS TCP IPv6 소켓 초기화

		Args:
			cert_file (str): 인증서 파일 경로
			key_file (str): 개인키 파일 경로
			ca_file (Optional[str]): CA 인증서 파일 경로 (상호 인증시 필요)
			logger_name (str): 로거 이름 (기본값: "tls_tcp6")
		"""
		self.cert_file = cert_file
		self.key_file = key_file
		self.ca_file = ca_file
		self.logger = logging.getLogger(logger_name)
		self.ssl_purpose = ssl.Purpose.SERVER_AUTH
		self.ssl_context = None
		self.receive_queue = Queue()
		self.send_queue = Queue()
		self.is_running = False

	def create_ssl_context(self) -> ssl.SSLContext:
		"""
		저장된 인증키 정보로 SSL 컨텍스트 생성

		Returns:
			ssl.SSLContext: 생성된 SSL 컨텍스트

		Raises:
			FileNotFoundError: 인증서 파일이 존재하지 않을 때
			ssl.SSLError: SSL 컨텍스트 생성 실패시
		"""
		try:
			# TLS 1.3 컨텍스트 생성
			context = ssl.create_default_context(self.ssl_purpose)
			context.minimum_version = ssl.TLSVersion.TLSv1_3
			context.maximum_version = ssl.TLSVersion.TLSv1_3

			# 인증서와 개인키 로드
			context.load_cert_chain(self.cert_file, self.key_file)

			# CA 인증서가 있으면 상호 인증 설정
			if self.ca_file:
				context.load_verify_locations(self.ca_file)
				context.verify_mode = ssl.CERT_REQUIRED

			self.ssl_context = context
			self.logger.info("SSL 컨텍스트가 성공적으로 생성되었습니다.")
			return context

		except FileNotFoundError as e:
			self.logger.error(f"인증서 파일을 찾을 수 없습니다: {e}")
			raise
		except ssl.SSLError as e:
			self.logger.error(f"SSL 컨텍스트 생성 실패: {e}")
			raise

	def process_received_data(self, data: bytes) -> bytes:
		"""
		수신된 데이터 후처리 메소드 (하위 클래스에서 재정의 가능)

		Args:
			data (bytes): 수신된 원본 데이터

		Returns:
			bytes: 후처리된 데이터
		"""
		return data

	async def _send_handler(self, writer: StreamWriter):
		"""
		송신 큐에서 데이터를 순차적으로 처리하는 내부 메소드

		Args:
			writer (StreamWriter): 데이터를 전송할 스트림 라이터
		"""
		try:
			while self.is_running:
				try:
					# 송신 큐에서 데이터 대기
					data = await asyncio.wait_for(self.send_queue.get(), timeout=1.0)
					writer.write(data)
					await writer.drain()
					self.logger.debug(f"데이터 송신 완료: {len(data)} bytes")
				except asyncio.TimeoutError:
					continue  # 타임아웃시 계속 대기
				except Exception as e:
					self.logger.error(f"데이터 송신 중 오류: {e}")
					break
		except Exception as e:
			self.logger.error(f"송신 핸들러 오류: {e}")
		self.logger.info(f"_send_handler teminated")

	async def _receive_handler(self, reader: StreamReader):
		"""
		데이터 수신을 처리하는 내부 메소드

		Args:
			reader (StreamReader): 데이터를 수신할 스트림 리더
		"""
		try:
			while self.is_running:
				try:
					data = await reader.read(4096)
					if not data:
						self.logger.info("연결이 종료되었습니다.")
						break

					# 수신 데이터 후처리
					processed_data = self.process_received_data(data)
					await self.receive_queue.put(processed_data)
					self.logger.debug(f"데이터 수신 완료: {len(data)} bytes")

				except Exception as e:
					self.logger.error(f"데이터 수신 중 오류: {e}")
					break
		except Exception as e:
			self.logger.error(f"수신 핸들러 오류: {e}")
		self.logger.info(f"_receive_handler teminated")

	async def send_data(self, data: bytes):
		"""
		외부에서 호출하는 데이터 송신 메소드

		Args:
			data (bytes): 전송할 데이터
		"""
		await self.send_queue.put(data)

	def stop(self):
		"""연결 종료"""
		self.is_running = False


class TlsTcp6Server(TlsTcp6Socket):
	"""IPv6 TLS 서버 클래스"""

	def __init__(self, host: str, port: int, cert_file: str, key_file: str,
				ca_file: Optional[str] = None, logger_name: str = "tls_tcp6",
				client_timeout: float = 60.0):
		"""
		TLS TCP IPv6 서버 초기화

		Args:
			host (str): 서버 바인딩 주소
			port (int): 서버 포트
			cert_file (str): 서버 인증서 파일 경로
			key_file (str): 서버 개인키 파일 경로
			ca_file (Optional[str]): CA 인증서 파일 경로
			logger_name (str): 로거 이름
			client_timeout (float): 클라이언트 타임아웃 시간 (초, 기본값: 60초)
		"""
		super().__init__(cert_file, key_file, ca_file, logger_name)
		self.ssl_purpose = ssl.Purpose.CLIENT_AUTH
		self.host = host
		self.port = port
		self.client_timeout = client_timeout
		self.clients: Dict[str, Dict[str, Any]] = {}
		self.server = None

	async def _handle_client(self, reader: StreamReader, writer: StreamWriter):
		"""
		클라이언트 연결을 처리하는 내부 메소드

		Args:
			reader (StreamReader): 클라이언트 스트림 리더
			writer (StreamWriter): 클라이언트 스트림 라이터
		"""
		client_id = str(uuid.uuid4())
		client_addr = writer.get_extra_info('peername')
		current_time = time()

		# 클라이언트 정보 저장
		self.clients[client_id] = {
			'reader': reader,
			'writer': writer,
			'address': client_addr,
			'connect_time': current_time,
			'last_received': current_time,
			'send_queue': Queue(),
			'is_active': True
		}

		self.logger.info(f"클라이언트 연결됨: {client_addr} (ID: {client_id})")

		try:
			# 송신 핸들러 시작
			send_task = asyncio.create_task(
				self._client_send_handler(client_id)
			)

			# 수신 핸들러 시작
			receive_task = asyncio.create_task(
				self._client_receive_handler(client_id)
			)

			# 두 태스크 중 하나라도 완료되면 종료
			await asyncio.gather(send_task, receive_task, return_exceptions=True)

		except Exception as e:
			self.logger.error(f"클라이언트 처리 중 오류 (ID: {client_id}): {e}")
		finally:
			self.logger.info(f"클라이언트 {client_id} 연결 종료 처리 중...")
			await self._cleanup_client(client_id)

	async def _client_send_handler(self, client_id: str):
		"""
		클라이언트별 송신 처리

		Args:
			client_id (str): 클라이언트 ID
		"""
		client_info = self.clients.get(client_id)
		if not client_info:
			return

		writer = client_info['writer']
		send_queue = client_info['send_queue']

		try:
			while client_info['is_active']:
				try:
					data = await asyncio.wait_for(send_queue.get(), timeout=1.0)
					writer.write(data)
					await writer.drain()
					self.logger.debug(f"클라이언트 {client_id}에 데이터 송신: {len(data)} bytes")
				except asyncio.TimeoutError:
					continue
				except Exception as e:
					self.logger.error(f"클라이언트 {client_id} 송신 오류: {e}")
					break
		except Exception as e:
			self.logger.error(f"클라이언트 송신 핸들러 오류 (ID: {client_id}): {e}")
		self.logger.info(f"_client_send_handler {client_id} terminated")

	async def _client_receive_handler(self, client_id: str):
		"""
		클라이언트별 수신 처리

		Args:
			client_id (str): 클라이언트 ID
		"""
		client_info = self.clients.get(client_id)
		if not client_info:
			return

		reader = client_info['reader']

		try:
			while client_info['is_active']:
				try:
					data = await reader.read(4096)
					if not data:
						self.logger.info(f"클라이언트 {client_id} 연결 종료")
						break

					# 마지막 수신 시간 업데이트
					client_info['last_received'] = time()

					# 수신 데이터 후처리
					processed_data = self.process_received_data(data)
					await self.receive_queue.put({
						'client_id': client_id,
						'data': processed_data,
						'timestamp': time()
					})

					self.logger.debug(f"클라이언트 {client_id}에서 데이터 수신: {len(data)} bytes")

				except Exception as e:
					self.logger.error(f"클라이언트 {client_id} 수신 오류: {e}")
					break
		except Exception as e:
			self.logger.error(f"클라이언트 수신 핸들러 오류 (ID: {client_id}): {e}")
		self.logger.info(f"_client_receive_handler {client_id} terminated")

	async def _cleanup_client(self, client_id: str):
		"""
		클라이언트 리소스 정리

		Args:
			client_id (str): 정리할 클라이언트 ID
		"""
		if client_id in self.clients:
			client_info = self.clients[client_id]
			client_info['is_active'] = False

			try:
				writer = client_info['writer']
				writer.close()
				await writer.wait_closed()
			except Exception as e:
				self.logger.warning(f"클라이언트 {client_id} 연결 종료 중 오류: {e}")

			del self.clients[client_id]
			self.logger.info(f"클라이언트 {client_id} 리소스 정리 완료")

	async def _timeout_monitor(self):
		"""클라이언트 타임아웃 모니터링"""
		while self.is_running:
			try:
				current_time = time()
				timeout_clients = []

				for client_id, client_info in self.clients.items():
					if current_time - client_info['last_received'] > self.client_timeout:
						timeout_clients.append(client_id)

				for client_id in timeout_clients:
					self.logger.info(f"클라이언트 {client_id} 타임아웃으로 연결 종료")
					await self._cleanup_client(client_id)

				await asyncio.sleep(10)  # 10초마다 체크

			except Exception as e:
				self.logger.error(f"타임아웃 모니터링 오류: {e}")
				await asyncio.sleep(1)

	async def send_to_client(self, client_id: str, data: bytes):
		"""
		특정 클라이언트에 데이터 송신

		Args:
			client_id (str): 대상 클라이언트 ID
			data (bytes): 전송할 데이터
		"""
		if client_id in self.clients:
			await self.clients[client_id]['send_queue'].put(data)
		else:
			self.logger.warning(f"존재하지 않는 클라이언트 ID: {client_id}")

	async def broadcast(self, data: bytes):
		"""
		모든 연결된 클라이언트에 데이터 브로드캐스트

		Args:
			data (bytes): 브로드캐스트할 데이터
		"""
		for client_id in list(self.clients.keys()):
			await self.send_to_client(client_id, data)

	async def start_server(self):
		"""서버 시작"""
		try:
			# SSL 컨텍스트 생성
			self.create_ssl_context()
			self.ssl_context.check_hostname = False

			self.is_running = True

			# 서버 시작
			self.server = await asyncio.start_server(
				self._handle_client,
				self.host,
				self.port,
				family=socket.AF_INET6,
				ssl=self.ssl_context
			)

			# 타임아웃 모니터 시작
			asyncio.create_task(self._timeout_monitor())

			addr = self.server.sockets[0].getsockname()
			self.logger.info(f"TLS TCP IPv6 서버가 {addr}에서 시작되었습니다.")

			async with self.server:
				await self.server.serve_forever()

		except Exception as e:
			self.logger.error(f"서버 시작 오류: {e}")
			raise

	async def stop_server(self):
		"""서버 중지"""
		self.is_running = False

		# 모든 클라이언트 연결 종료
		for client_id in list(self.clients.keys()):
			await self._cleanup_client(client_id)

		if self.server:
			self.server.close()
			await self.server.wait_closed()
			self.logger.info("서버가 중지되었습니다.")


class TlsTcp6Client(TlsTcp6Socket):
	"""IPv6 TLS 클라이언트 클래스"""

	def __init__(self, cert_file: str, key_file: str, ca_file: Optional[str] = None,
				logger_name: str = "tls_tcp6", check_hostname: bool = True):
		"""
		TLS TCP IPv6 클라이언트 초기화

		Args:
			cert_file (str): 클라이언트 인증서 파일 경로
			key_file (str): 클라이언트 개인키 파일 경로
			ca_file (Optional[str]): CA 인증서 파일 경로
			logger_name (str): 로거 이름
			check_hostname (bool): 호스트명 검증 여부 (기본값: True)
		"""
		super().__init__(cert_file, key_file, ca_file, logger_name)
		self.check_hostname = check_hostname
		self.reader = None
		self.writer = None

	async def connect(self, host: str, port: int):
		"""
		서버에 연결

		Args:
			host (str): 서버 주소
			port (int): 서버 포트

		Raises:
			ConnectionError: 연결 실패시
		"""
		try:
			# SSL 컨텍스트 생성
			context = self.create_ssl_context()
			context.check_hostname = self.check_hostname

			# 서버에 연결
			self.reader, self.writer = await asyncio.open_connection(
				host, port, ssl=context, family=socket.AF_INET6
			)

			self.is_running = True

			# 송수신 핸들러 시작
			asyncio.create_task(self._send_handler(self.writer))
			asyncio.create_task(self._receive_handler(self.reader))

			self.logger.info(f"서버 {host}:{port}에 연결되었습니다.")

		except Exception as e:
			self.logger.error(f"서버 연결 실패: {e}")
			raise ConnectionError(f"서버 연결 실패: {e}")

	async def disconnect(self):
		"""서버 연결 해제"""
		self.is_running = False

		if self.writer:
			try:
				self.writer.close()
				await self.writer.wait_closed()
				self.logger.info("서버 연결이 해제되었습니다.")
			except Exception as e:
				self.logger.warning(f"연결 해제 중 오류: {e}")


class BaseParser:
	"""수신 데이터 파싱을 위한 기본 클래스"""

	def __init__(self, receive_queue: Queue, logger_name: str = "tls_tcp6"):
		"""
		파서 초기화

		Args:
			receive_queue (Queue): 수신 데이터 큐
			logger_name (str): 로거 이름
		"""
		self.receive_queue = receive_queue
		self.logger = logging.getLogger(logger_name)
		self.buffer = b''
		self.message_queue = Queue()
		self.is_running = False

	async def start_parsing(self):
		"""파싱 시작"""
		self.is_running = True
		await self._parse_loop()

	async def _parse_loop(self):
		"""데이터 파싱 루프"""
		while self.is_running:
			try:
				# 수신 큐에서 데이터 가져오기
				data = await asyncio.wait_for(self.receive_queue.get(), timeout=1.0)

				if isinstance(data, dict):  # 서버에서 오는 데이터 형태
					raw_data = data.get('data', b'')
				else:  # 클라이언트에서 오는 데이터 형태
					raw_data = data

				# 버퍼에 추가
				self.buffer += raw_data

				# 메시지 패킷 추출
				await self._extract_messages()

			except asyncio.TimeoutError:
				continue
			except Exception as e:
				self.logger.error(f"파싱 중 오류: {e}")

	async def _extract_messages(self):
		"""
		버퍼에서 메시지 패킷 추출 (하위 클래스에서 구현)
		기본 구현: 전체 버퍼를 하나의 메시지로 처리
		"""
		if self.buffer:
			await self.message_queue.put(self.buffer)
			self.buffer = b''

	def stop(self):
		"""파싱 중지"""
		self.is_running = False


# 예제 구현
async def echo_server_example():
	"""에코 서버 예제"""
	logging.basicConfig(level=logging.INFO)

	server = TlsTcp6Server(
		host="::1",  # IPv6 localhost
		port=8443,
		cert_file="server.crt",
		key_file="server.key",
		ca_file="ca.crt"
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


async def client_example():
	"""클라이언트 예제"""
	logging.basicConfig(level=logging.INFO)

	client = TlsTcp6Client(
		cert_file="client.crt",
		key_file="client.key",
		ca_file="ca.crt",
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


if __name__ == "__main__":
	# 사용 예제
	print("TLS TCP IPv6 통신 프레임워크")
	print("1. 서버 실행: python script.py server")
	print("2. 클라이언트 실행: python script.py client")

	import sys
	if len(sys.argv) > 1:
		if sys.argv[1] == "server":
			asyncio.run(echo_server_example())
		elif sys.argv[1] == "client":
			asyncio.run(client_example())
	else:
		print("사용법: python script.py [server|client]")