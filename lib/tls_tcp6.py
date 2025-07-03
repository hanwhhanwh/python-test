# -*- coding: utf-8 -*-
# IPv6 TLS TCP communication Framework
# made : hbesthee@naver.com
# date : 2025-07-02

# Original Packages
from asyncio import StreamReader, StreamWriter, Queue
from time import time
from typing import Optional, Dict, Any, Callable

import asyncio
import logging
import socket
import ssl
import uuid




class TlsTcp6Socket:
	"""IPv6 TLS TCP 소켓의 기본 클래스"""

	def __init__(self, cert_file: str, key_file: str, ca_file: Optional[str] = None,
				 logger_name: str = "tls_tcp6", **kwargs):
		"""
		TLS TCP IPv6 소켓 초기화

		Args:
			cert_file (str): 클라이언트/서버 인증서 파일 경로
			key_file (str): 개인키 파일 경로
			ca_file (Optional[str]): CA 인증서 파일 경로
			logger_name (str): 로거 이름 (기본값: "tls_tcp6")
			**kwargs: 추가 매개변수 (reader, writer 등)
		"""
		self.cert_file = cert_file
		self.key_file = key_file
		self.ca_file = ca_file
		self.logger = logging.getLogger(logger_name)

		# 서버에서 연결된 클라이언트용 StreamReader/Writer
		self._reader: Optional[StreamReader] = kwargs.get('reader')
		self._writer: Optional[StreamWriter] = kwargs.get('writer')

		# 통신 관련 큐들
		self.receive_queue: Queue = Queue()
		self._send_queue: Queue = Queue()

		# 연결 상태 관리
		self._connected = False
		self._ssl_context: Optional[ssl.SSLContext] = None

		# 비동기 태스크들
		self._receive_task: Optional[asyncio.Task] = None
		self._send_task: Optional[asyncio.Task] = None

	def create_ssl_context(self, is_server: bool = False) -> ssl.SSLContext:
		"""
		SSL Context 생성

		Args:
			is_server (bool): 서버 모드 여부 (기본값: False)

		Returns:
			ssl.SSLContext: 생성된 SSL 컨텍스트
		"""
		# TLS 1.3 사용
		context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH if is_server else ssl.Purpose.SERVER_AUTH)
		context.minimum_version = ssl.TLSVersion.TLSv1_3
		context.maximum_version = ssl.TLSVersion.TLSv1_3

		# 인증서 및 키 로드
		context.load_cert_chain(self.cert_file, self.key_file)

		# CA 인증서가 있는 경우 로드
		if self.ca_file:
			context.load_verify_locations(self.ca_file)
			context.verify_mode = ssl.CERT_REQUIRED
		else:
			context.check_hostname = False
			context.verify_mode = ssl.CERT_NONE

		self._ssl_context = context
		self.logger.info(f"SSL Context 생성 완료 (서버 모드: {is_server})")
		return context

	async def _receive_loop(self):
		"""데이터 수신 루프"""
		try:
			while self._connected and self._reader:
				try:
					# 데이터 수신 (최대 4096 바이트)
					data = await self._reader.read(4096)
					if not data:
						self.logger.info("연결이 종료되었습니다.")
						break

					# 수신 데이터 후처리
					processed_data = self.process_received_data(data)

					# 수신 큐에 데이터 추가
					await self.receive_queue.put(processed_data)
					self.logger.debug(f"데이터 수신: {len(data)} 바이트")

				except asyncio.CancelledError:
					break
				except Exception as e:
					self.logger.error(f"데이터 수신 중 오류 발생: {e}")
					break
		except Exception as e:
			self.logger.error(f"수신 루프에서 예외 발생: {e}")
		finally:
			await self._close_connection()

	async def _send_loop(self):
		"""데이터 송신 루프"""
		try:
			while self._connected and self._writer:
				try:
					# 송신 큐에서 데이터 가져오기
					data = await self._send_queue.get()
					if data is None:  # 종료 신호
						break

					# 데이터 전송
					self._writer.write(data)
					await self._writer.drain()
					self.logger.debug(f"데이터 송신: {len(data)} 바이트")

				except asyncio.CancelledError:
					break
				except Exception as e:
					self.logger.error(f"데이터 송신 중 오류 발생: {e}")
					break
		except Exception as e:
			self.logger.error(f"송신 루프에서 예외 발생: {e}")
		finally:
			await self._close_connection()

	def process_received_data(self, data: bytes) -> bytes:
		"""
		수신 데이터 후처리 메소드 (하위 클래스에서 재정의 가능)

		Args:
			data (bytes): 수신된 원시 데이터

		Returns:
			bytes: 후처리된 데이터
		"""
		return data

	async def send_data(self, data: bytes):
		"""
		데이터 송신 (외부 공개 메소드)

		Args:
			data (bytes): 송신할 데이터
		"""
		if self._connected:
			await self._send_queue.put(data)
		else:
			self.logger.warning("연결이 끊어진 상태에서 데이터 송신 시도")

	async def _close_connection(self):
		"""연결 종료 처리"""
		if not self._connected:
			return

		self._connected = False

		# 송신 태스크 종료
		if self._send_task and not self._send_task.done():
			await self._send_queue.put(None)  # 종료 신호
			self._send_task.cancel()

		# 수신 태스크 종료
		if self._receive_task and not self._receive_task.done():
			self._receive_task.cancel()

		# Writer 종료
		if self._writer:
			try:
				self._writer.close()
				await self._writer.wait_closed()
			except Exception as e:
				self.logger.error(f"Writer 종료 중 오류: {e}")

		self.logger.info("연결이 종료되었습니다.")

	def is_connected(self) -> bool:
		"""
		연결 상태 확인

		Returns:
			bool: 연결 상태
		"""
		return self._connected


class TlsTcp6Server(TlsTcp6Socket):
	"""IPv6 TLS TCP 서버 클래스"""

	def __init__(self, cert_file: str, key_file: str, ca_file: Optional[str] = None,
					logger_name: str = "tls_tcp6", timeout: int = 60):
		"""
		TLS TCP IPv6 서버 초기화

		Args:
			cert_file (str): 서버 인증서 파일 경로
			key_file (str): 개인키 파일 경로
			ca_file (Optional[str]): CA 인증서 파일 경로
			logger_name (str): 로거 이름 (기본값: "tls_tcp6")
			timeout (int): 클라이언트 타임아웃 시간 (초, 기본값: 60)
		"""
		super().__init__(cert_file, key_file, ca_file, logger_name)
		self.timeout = timeout
		self.clients: Dict[str, Dict[str, Any]] = {}
		self._server = None
		self._cleanup_task: Optional[asyncio.Task] = None

	async def start_server(self, host: str = "::", port: int = 8443):
		"""
		서버 시작

		Args:
			host (str): 바인딩할 호스트 주소 (기본값: "::" - 모든 IPv6 주소)
			port (int): 바인딩할 포트 번호 (기본값: 8443)
		"""
		ssl_context = self.create_ssl_context(is_server=True)

		self._server = await asyncio.start_server(
			self._handle_client,
			host,
			port,
			ssl=ssl_context,
			family=socket.AF_INET6
		)

		self._cleanup_task = asyncio.create_task(self._cleanup_clients())
		self.logger.info(f"서버가 [{host}]:{port}에서 시작되었습니다.")

	async def _handle_client(self, reader: StreamReader, writer: StreamWriter):
		"""
		클라이언트 연결 처리

		Args:
			reader (StreamReader): 클라이언트로부터 데이터를 읽는 스트림
			writer (StreamWriter): 클라이언트로 데이터를 쓰는 스트림
		"""
		client_id = str(uuid.uuid4())
		client_addr = writer.get_extra_info('peername')
		current_time = time()

		# 클라이언트 소켓 객체 생성
		client_socket = TlsTcp6Socket(
			self.cert_file, self.key_file, self.ca_file,
			self.logger.name, reader=reader, writer=writer
		)
		client_socket._reader = reader
		client_socket._writer = writer
		client_socket._connected = True

		# 클라이언트 정보 저장
		self.clients[client_id] = {
			'socket': client_socket,
			'address': client_addr,
			'connect_time': current_time,
			'last_received': current_time
		}

		self.logger.info(f"클라이언트 연결: {client_addr} (ID: {client_id})")

		# 수신/송신 태스크 시작
		client_socket._receive_task = asyncio.create_task(self._client_receive_loop(client_id))
		client_socket._send_task = asyncio.create_task(client_socket._send_loop())

		try:
			# 클라이언트 연결 유지
			await asyncio.gather(client_socket._receive_task, client_socket._send_task)
		except Exception as e:
			self.logger.error(f"클라이언트 {client_id} 처리 중 오류: {e}")
		finally:
			await self._remove_client(client_id)

	async def _client_receive_loop(self, client_id: str):
		"""
		클라이언트별 데이터 수신 루프

		Args:
			client_id (str): 클라이언트 ID
		"""
		client_info = self.clients.get(client_id)
		if not client_info:
			return

		client_socket = client_info['socket']

		try:
			while client_socket._connected and client_socket._reader:
				try:
					data = await client_socket._reader.read(4096)
					if not data:
						break

					# 마지막 수신 시각 갱신
					self.clients[client_id]['last_received'] = time()

					# 수신 데이터 후처리
					processed_data = client_socket.process_received_data(data)

					# 에코 기능 - 수신된 데이터를 다시 전송
					await client_socket.send_data(processed_data)

					# 수신 큐에 데이터 추가
					await client_socket.receive_queue.put(processed_data)
					self.logger.debug(f"클라이언트 {client_id}로부터 데이터 수신: {len(data)} 바이트")

				except asyncio.CancelledError:
					break
				except Exception as e:
					self.logger.error(f"클라이언트 {client_id} 데이터 수신 중 오류: {e}")
					break
		except Exception as e:
			self.logger.error(f"클라이언트 {client_id} 수신 루프에서 예외: {e}")

	async def _cleanup_clients(self):
		"""비활성 클라이언트 정리"""
		while self._server:
			try:
				current_time = time()
				clients_to_remove = []

				for client_id, client_info in self.clients.items():
					if current_time - client_info['last_received'] > self.timeout:
						clients_to_remove.append(client_id)
						self.logger.info(f"타임아웃으로 클라이언트 {client_id} 제거")

				for client_id in clients_to_remove:
					await self._remove_client(client_id)

				await asyncio.sleep(10)  # 10초마다 정리 작업 수행

			except asyncio.CancelledError:
				break
			except Exception as e:
				self.logger.error(f"클라이언트 정리 중 오류: {e}")

	async def _remove_client(self, client_id: str):
		"""
		클라이언트 제거 및 리소스 정리

		Args:
			client_id (str): 제거할 클라이언트 ID
		"""
		if client_id not in self.clients:
			return

		client_info = self.clients[client_id]
		client_socket = client_info['socket']

		# 연결 종료
		await client_socket._close_connection()

		# 클라이언트 목록에서 제거
		del self.clients[client_id]
		self.logger.info(f"클라이언트 {client_id} 제거 완료")

	async def stop_server(self):
		"""서버 종료"""
		if self._server:
			self._server.close()
			await self._server.wait_closed()

		# 정리 태스크 종료
		if self._cleanup_task:
			self._cleanup_task.cancel()

		# 모든 클라이언트 연결 종료
		for client_id in list(self.clients.keys()):
			await self._remove_client(client_id)

		self.logger.info("서버가 종료되었습니다.")

	def get_client_count(self) -> int:
		"""
		연결된 클라이언트 수 반환

		Returns:
			int: 연결된 클라이언트 수
		"""
		return len(self.clients)


class TlsTcp6Client(TlsTcp6Socket):
	"""IPv6 TLS TCP 클라이언트 클래스"""

	def __init__(self, cert_file: str, key_file: str, ca_file: Optional[str] = None,
					logger_name: str = "tls_tcp6", check_hostname: bool = False):
		"""
		TLS TCP IPv6 클라이언트 초기화

		Args:
			cert_file (str): 클라이언트 인증서 파일 경로
			key_file (str): 개인키 파일 경로
			ca_file (Optional[str]): CA 인증서 파일 경로
			logger_name (str): 로거 이름 (기본값: "tls_tcp6")
			check_hostname (bool): 호스트명 검증 여부 (기본값: False)
		"""
		super().__init__(cert_file, key_file, ca_file, logger_name)
		self.check_hostname = check_hostname

	async def connect(self, host: str, port: int):
		"""
		서버에 연결

		Args:
			host (str): 서버 호스트 주소
			port (int): 서버 포트 번호
		"""
		ssl_context = self.create_ssl_context(is_server=False)
		ssl_context.check_hostname = self.check_hostname

		try:
			self._reader, self._writer = await asyncio.open_connection(
				host, port, ssl=ssl_context, family=socket.AF_INET6
			)
			self._connected = True

			# 수신/송신 태스크 시작
			self._receive_task = asyncio.create_task(self._receive_loop())
			self._send_task = asyncio.create_task(self._send_loop())

			self.logger.info(f"서버 [{host}]:{port}에 연결되었습니다.")

		except Exception as e:
			self.logger.error(f"서버 연결 실패: {e}")
			raise

	async def disconnect(self):
		"""서버 연결 해제"""
		await self._close_connection()


class BaseParser:
	"""수신 데이터 파싱을 위한 기본 클래스"""

	def __init__(self, receive_queue: Queue, logger_name: str = "tls_tcp6"):
		"""
		파서 초기화

		Args:
			receive_queue (Queue): 수신 데이터 큐
			logger_name (str): 로거 이름 (기본값: "tls_tcp6")
		"""
		self.receive_queue = receive_queue
		self.message_queue: Queue = Queue()
		self.logger = logging.getLogger(logger_name)
		self._buffer = bytearray()
		self._running = False
		self._parse_task: Optional[asyncio.Task] = None

	async def start_parsing(self):
		"""파싱 시작"""
		self._running = True
		self._parse_task = asyncio.create_task(self._parse_loop())

	async def stop_parsing(self):
		"""파싱 중지"""
		self._running = False
		if self._parse_task:
			self._parse_task.cancel()

	async def _parse_loop(self):
		"""파싱 루프"""
		try:
			while self._running:
				try:
					# 수신 큐에서 데이터 가져오기
					data = await self.receive_queue.get()
					self._buffer.extend(data)

					# 메시지 패킷 추출
					while True:
						packet = self._extract_packet()
						if packet is None:
							break
						await self.message_queue.put(packet)

				except asyncio.CancelledError:
					break
				except Exception as e:
					self.logger.error(f"파싱 중 오류 발생: {e}")
		except Exception as e:
			self.logger.error(f"파싱 루프에서 예외 발생: {e}")

	def _extract_packet(self) -> Optional[bytes]:
		"""
		버퍼에서 메시지 패킷 추출 (하위 클래스에서 재정의 필요)

		Returns:
			Optional[bytes]: 추출된 메시지 패킷 또는 None
		"""
		# 기본 구현: 버퍼의 모든 데이터를 하나의 패킷으로 처리
		if self._buffer:
			packet = bytes(self._buffer)
			self._buffer.clear()
			return packet
		return None

	async def get_message(self) -> bytes:
		"""
		메시지 큐에서 메시지 가져오기

		Returns:
			bytes: 파싱된 메시지
		"""
		return await self.message_queue.get()


# 예제 코드

async def server_example():
	"""서버 예제"""
	logging.basicConfig(level=logging.INFO)

	# 서버 생성 (실제 사용 시에는 유효한 인증서 파일 경로 지정)
	server = TlsTcp6Server("server.crt", "server.key", "ca.crt")

	try:
		# 서버 시작
		await server.start_server(host="::", port=8443)

		# 서버 실행 유지 (실제로는 적절한 종료 조건 구현)
		while True:
			await asyncio.sleep(1)
			if server.get_client_count() > 0:
				print(f"연결된 클라이언트 수: {server.get_client_count()}")

	except KeyboardInterrupt:
		print("서버 종료 중...")
	finally:
		await server.stop_server()


async def client_example():
	"""클라이언트 예제"""
	logging.basicConfig(level=logging.INFO)

	# 클라이언트 생성 (실제 사용 시에는 유효한 인증서 파일 경로 지정)
	client = TlsTcp6Client("client.crt", "client.key", "ca.crt")

	try:
		# 서버에 연결
		await client.connect("::1", 8443)

		# 파서 생성 및 시작
		parser = BaseParser(client.receive_queue)
		await parser.start_parsing()

		# 테스트 메시지 전송
		test_message = b"Hello, TLS TCP6 Server!"
		await client.send_data(test_message)
		print(f"메시지 전송: {test_message.decode()}")

		# 에코된 메시지 수신
		received_message = await parser.get_message()
		print(f"에코 메시지 수신: {received_message.decode()}")

		# 파서 중지
		await parser.stop_parsing()

	except Exception as e:
		print(f"클라이언트 오류: {e}")
	finally:
		await client.disconnect()
