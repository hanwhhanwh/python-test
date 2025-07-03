# -*- coding: utf-8 -*-
# IPv6 TLS TCP communication Framework
# made : hbesthee@naver.com
# date : 2025-07-02

# Original Packages
from asyncio import Queue, Task, StreamReader, StreamWriter
from time import time
from typing import Optional, Type, Dict, Any

import asyncio
import logging
import socket
import ssl
import uuid



class BaseParser:
	"""
	bytes 데이터 파서 기본 클래스
	큐를 통해 받은 데이터를 내부에서 버퍼링하고 메시지 패킷으로 분석
	"""

	def __init__(self, data_queue: Queue, logger_name: str = "tls_tcp6"):
		"""
		파서 초기화

		Args:
			data_queue (Queue): 수신된 데이터를 받을 큐
			logger_name (str): 로거 이름
		"""
		self.data_queue = data_queue
		self.packet_queue = Queue()
		self.logger = logging.getLogger(logger_name)
		self._running = False
		self._parse_task: Optional[Task] = None
		self._buffer = b""

	async def parse(self):
		"""
		비동기적으로 큐의 데이터를 메시지 패킷으로 분석하여 내부 메시지 패킷 큐에 입력
		"""
		self._running = True
		self.logger.info("Parser 시작")

		try:
			while self._running:
				try:
					# 타임아웃을 설정하여 주기적으로 체크
					data = await asyncio.wait_for(self.data_queue.get(), timeout=1.0)
					self._buffer += data

					# 기본적인 데이터 처리: bytes 데이터를 문자열로 변환
					if self._buffer:
						try:
							message = self._buffer.decode('utf-8')
							await self.packet_queue.put(message)
							self._buffer = b""
							self.logger.debug(f"패킷 파싱 완료: {len(message)} 문자")
						except UnicodeDecodeError:
							self.logger.warning("UTF-8 디코딩 실패, 더 많은 데이터 대기")

				except asyncio.TimeoutError:
					# 타임아웃은 정상적인 동작
					continue
				except Exception as e:
					self.logger.error(f"파싱 중 오류 발생: {e}")
					break

		except Exception as e:
			self.logger.error(f"Parser 실행 중 오류: {e}")
		finally:
			self.logger.info("Parser 종료")

	def start(self):
		"""
		파서 시작 - parse() 코루틴에 대한 Task 생성
		"""
		if not self._parse_task or self._parse_task.done():
			self._parse_task = asyncio.create_task(self.parse())
			self.logger.info("Parser Task 생성 완료")

	def stop(self):
		"""
		파서 종료
		"""
		self._running = False
		if self._parse_task and not self._parse_task.done():
			self._parse_task.cancel()
			self.logger.info("Parser Task 취소 완료")


class TlsTcp6Socket:
	"""
	TLS 1.3 기반 IPv6 TCP 소켓 기본 클래스
	서버와 클라이언트에서 공통되는 부분을 구현
	"""

	def __init__(self, host: str = "::1", port: int = 8888,
					cert_file: Optional[str] = None, key_file: Optional[str] = None,
					ca_file: Optional[str] = None, logger_name: str = "tls_tcp6",
					parser_class: Type[BaseParser] = BaseParser, **kwargs):
		"""
		TLS TCP 소켓 초기화

		Args:
			host (str): 연결할 호스트 주소
			port (int): 연결할 포트 번호
			cert_file (str): 인증서 파일 경로
			key_file (str): 개인키 파일 경로
			ca_file (str): CA 인증서 파일 경로
			logger_name (str): 로거 이름
			parser_class (Type[BaseParser]): 파서 클래스 타입
			**kwargs: 추가 매개변수 (reader, writer 등)
		"""
		self.host = host
		self.port = port
		self.cert_file = cert_file
		self.key_file = key_file
		self.ca_file = ca_file
		self.logger = logging.getLogger(logger_name)
		self.parser_class = parser_class

		# 서버에서 연결된 클라이언트 소켓을 위한 StreamReader, StreamWriter
		self._reader: Optional[StreamReader] = kwargs.get('reader')
		self._writer: Optional[StreamWriter] = kwargs.get('writer')

		# 시간 관리
		self._connected_time: Optional[float] = None
		self._last_received_time: Optional[float] = None

		# 큐 및 파서
		self.receive_queue = Queue()
		self.send_queue = Queue()
		self.parser: Optional[BaseParser] = None

		# 태스크 관리
		self._receive_task: Optional[Task] = None
		self._send_task: Optional[Task] = None
		self._running = False

		# 서버 참조 (클라이언트 연결에서 사용)
		self.server: Optional['TlsTcp6Server'] = kwargs.get('server')
		self.client_id: Optional[str] = kwargs.get('client_id')

	def create_ssl_context(self, server_side: bool = False) -> ssl.SSLContext:
		"""
		SSLContext 생성

		Args:
			server_side (bool): 서버 측 컨텍스트 여부

		Returns:
			ssl.SSLContext: 생성된 SSL 컨텍스트
		"""
		context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH if not server_side else ssl.Purpose.CLIENT_AUTH)
		context.minimum_version = ssl.TLSVersion.TLSv1_3
		context.maximum_version = ssl.TLSVersion.TLSv1_3

		if server_side:
			context.load_cert_chain(self.cert_file, self.key_file)
			context.verify_mode = ssl.CERT_REQUIRED
		else:
			context.check_hostname = getattr(self, 'check_hostname', True)
			context.verify_mode = ssl.CERT_REQUIRED

		if self.ca_file:
			context.load_verify_locations(self.ca_file)

		self.logger.info(f"SSL 컨텍스트 생성 완료 (server_side={server_side})")
		return context

	def process_received_data(self, data: bytes) -> bytes:
		"""
		수신 데이터 후처리 메소드

		Args:
			data (bytes): 수신된 원본 데이터

		Returns:
			bytes: 처리된 데이터
		"""
		# 기본 구현: 수신 데이터를 그대로 반환
		return data

	async def _receive_data(self):
		"""
		데이터 수신 처리
		"""
		self._connected_time = time()
		self._last_received_time = self._connected_time
		self.logger.info(f"데이터 수신 시작 (연결 시각: {self._connected_time})")

		try:
			while self._running:
				if not self._reader:
					await asyncio.sleep(0.1)
					continue

				try:
					data = await self._reader.read(8192)
					if not data:
						self.logger.info("연결이 종료되었습니다")
						break

					self._last_received_time = time()
					processed_data = self.process_received_data(data)
					await self.receive_queue.put(processed_data)

					self.logger.debug(f"데이터 수신 완료: {len(data)} bytes")

				except Exception as e:
					self.logger.error(f"데이터 수신 중 오류: {e}")
					break

		except Exception as e:
			self.logger.error(f"수신 태스크 실행 중 오류: {e}")
		finally:
			await self._cleanup()

	async def _send_data(self):
		"""
		데이터 송신 처리
		"""
		self.logger.info("데이터 송신 시작")

		try:
			while self._running:
				if not self._writer:
					await asyncio.sleep(0.1)
					continue

				try:
					data = await asyncio.wait_for(self.send_queue.get(), timeout=1.0)
					if isinstance(data, str):
						data = data.encode('utf-8')

					self._writer.write(data)
					await self._writer.drain()

					self.logger.debug(f"데이터 송신 완료: {len(data)} bytes")

				except asyncio.TimeoutError:
					continue
				except Exception as e:
					self.logger.error(f"데이터 송신 중 오류: {e}")
					break

		except Exception as e:
			self.logger.error(f"송신 태스크 실행 중 오류: {e}")

	async def send(self, data: bytes | str):
		"""
		외부 공개 송신 함수

		Args:
			data (bytes | str): 송신할 데이터
		"""
		await self.send_queue.put(data)

	async def start_communication(self):
		"""
		통신 시작
		"""
		self._running = True

		# 파서 생성 및 시작
		self.parser = self.parser_class(self.receive_queue, self.logger.name)
		self.parser.start()

		# 수신/송신 태스크 시작
		self._receive_task = asyncio.create_task(self._receive_data())
		self._send_task = asyncio.create_task(self._send_data())

		self.logger.info("통신 시작 완료")

	async def stop_communication(self):
		"""
		통신 종료
		"""
		self._running = False

		# 파서 종료
		if self.parser:
			self.parser.stop()

		# 태스크 취소
		if self._receive_task and not self._receive_task.done():
			self._receive_task.cancel()
		if self._send_task and not self._send_task.done():
			self._send_task.cancel()

		await self._cleanup()

	async def _cleanup(self):
		"""
		리소스 정리
		"""
		if self._writer:
			self._writer.close()
			await self._writer.wait_closed()

		self.logger.info("리소스 정리 완료")

	def is_timeout(self, timeout_seconds: int = 60) -> bool:
		"""
		타임아웃 확인

		Args:
			timeout_seconds (int): 타임아웃 시간 (초)

		Returns:
			bool: 타임아웃 여부
		"""
		if self._last_received_time is None:
			return False

		return (time() - self._last_received_time) > timeout_seconds


class TlsTcp6Server:
	"""
	TLS 1.3 기반 IPv6 TCP 서버
	다중 클라이언트 연결 처리
	"""

	def __init__(self, host: str = "::1", port: int = 8888,
				 cert_file: Optional[str] = None, key_file: Optional[str] = None,
				 ca_file: Optional[str] = None, logger_name: str = "tls_tcp6",
				 socket_class: Type[TlsTcp6Socket] = TlsTcp6Socket, **kwargs):
		"""
		TLS TCP 서버 초기화

		Args:
			host (str): 서버 바인딩 주소
			port (int): 서버 포트
			cert_file (str): 인증서 파일 경로
			key_file (str): 개인키 파일 경로
			ca_file (str): CA 인증서 파일 경로
			logger_name (str): 로거 이름
			socket_class (Type[TlsTcp6Socket]): 소켓 클래스 타입
			**kwargs: 추가 매개변수
		"""
		self.host = host
		self.port = port
		self.cert_file = cert_file
		self.key_file = key_file
		self.ca_file = ca_file
		self.logger = logging.getLogger(logger_name)
		self.socket_class = socket_class

		# 연결된 클라이언트 관리
		self.clients: Dict[str, TlsTcp6Socket] = {}

		# 서버 실행 상태
		self._running = False
		self._server: Optional[asyncio.Server] = None
		self._cleanup_task: Optional[Task] = None

	async def _handle_client(self, reader: StreamReader, writer: StreamWriter):
		"""
		클라이언트 연결 처리

		Args:
			reader (StreamReader): 클라이언트 StreamReader
			writer (StreamWriter): 클라이언트 StreamWriter
		"""
		client_id = str(uuid.uuid4())
		client_addr = writer.get_extra_info('peername')

		self.logger.info(f"클라이언트 연결: {client_addr} (ID: {client_id})")

		try:
			# 클라이언트 소켓 객체 생성
			client_socket = self.socket_class(
				host=self.host,
				port=self.port,
				cert_file=self.cert_file,
				key_file=self.key_file,
				ca_file=self.ca_file,
				logger_name=self.logger.name,
				reader=reader,
				writer=writer,
				server=self,
				client_id=client_id
			)

			# 클라이언트 등록
			self.clients[client_id] = client_socket

			# 통신 시작
			await client_socket.start_communication()

			# 에코 서버 동작: 수신된 데이터를 다시 전송
			while client_socket._running:
				try:
					if client_socket.parser and not client_socket.parser.packet_queue.empty():
						message = await client_socket.parser.packet_queue.get()
						await client_socket.send(message)
						self.logger.debug(f"에코 응답 전송: {message}")

					await asyncio.sleep(0.1)

				except Exception as e:
					self.logger.error(f"에코 처리 중 오류: {e}")
					break

		except Exception as e:
			self.logger.error(f"클라이언트 처리 중 오류: {e}")
		finally:
			# 클라이언트 정리
			if client_id in self.clients:
				await self.clients[client_id].stop_communication()
				del self.clients[client_id]

			self.logger.info(f"클라이언트 연결 종료: {client_addr} (ID: {client_id})")

	async def _cleanup_clients(self):
		"""
		타임아웃된 클라이언트 정리
		"""
		while self._running:
			try:
				timeout_clients = []

				for client_id, client_socket in self.clients.items():
					if client_socket.is_timeout():
						timeout_clients.append(client_id)

				for client_id in timeout_clients:
					self.logger.info(f"타임아웃 클라이언트 정리: {client_id}")
					await self.clients[client_id].stop_communication()
					del self.clients[client_id]

				await asyncio.sleep(30)  # 30초마다 정리 작업 수행

			except Exception as e:
				self.logger.error(f"클라이언트 정리 중 오류: {e}")

	async def start(self):
		"""
		서버 시작
		"""
		try:
			# SSL 컨텍스트 생성
			ssl_context = None
			if self.cert_file and self.key_file:
				temp_socket = self.socket_class(
					cert_file=self.cert_file,
					key_file=self.key_file,
					ca_file=self.ca_file
				)
				ssl_context = temp_socket.create_ssl_context(server_side=True)

			# 서버 시작
			self._server = await asyncio.start_server(
				self._handle_client,
				self.host,
				self.port,
				ssl=ssl_context,
				family=socket.AF_INET6 if ':' in self.host else socket.AF_INET
			)

			self._running = True

			# 정리 태스크 시작
			self._cleanup_task = asyncio.create_task(self._cleanup_clients())

			self.logger.info(f"서버 시작: {self.host}:{self.port}")

		except Exception as e:
			self.logger.error(f"서버 시작 실패: {e}")
			raise

	async def serve_forever(self):
		"""
		서버 실행 유지
		"""
		if self._server:
			await self._server.serve_forever()

	async def stop(self):
		"""
		서버 종료
		"""
		self._running = False

		# 모든 클라이언트 연결 종료
		for client_id in list(self.clients.keys()):
			await self.clients[client_id].stop_communication()
			del self.clients[client_id]

		# 정리 태스크 종료
		if self._cleanup_task and not self._cleanup_task.done():
			self._cleanup_task.cancel()

		# 서버 종료
		if self._server:
			self._server.close()
			await self._server.wait_closed()

		self.logger.info("서버 종료 완료")


class TlsTcp6Client(TlsTcp6Socket):
	"""
	TLS 1.3 기반 IPv6 TCP 클라이언트
	"""

	def __init__(self, host: str = "::1", port: int = 8888,
				 cert_file: Optional[str] = None, key_file: Optional[str] = None,
				 ca_file: Optional[str] = None, logger_name: str = "tls_tcp6",
				 check_hostname: bool = True, parser_class: Type[BaseParser] = BaseParser,
				 **kwargs):
		"""
		TLS TCP 클라이언트 초기화

		Args:
			host (str): 서버 주소
			port (int): 서버 포트
			cert_file (str): 클라이언트 인증서 파일 경로
			key_file (str): 클라이언트 개인키 파일 경로
			ca_file (str): CA 인증서 파일 경로
			logger_name (str): 로거 이름
			check_hostname (bool): 호스트명 검증 여부
			parser_class (Type[BaseParser]): 파서 클래스 타입
			**kwargs: 추가 매개변수
		"""
		super().__init__(host, port, cert_file, key_file, ca_file, logger_name, parser_class, **kwargs)
		self.check_hostname = check_hostname

	async def connect(self):
		"""
		서버에 연결
		"""
		try:
			# SSL 컨텍스트 생성
			ssl_context = self.create_ssl_context(server_side=False)
			ssl_context.check_hostname = self.check_hostname

			# 서버 연결
			self._reader, self._writer = await asyncio.open_connection(
				self.host,
				self.port,
				ssl=ssl_context,
				family=socket.AF_INET6 if ':' in self.host else socket.AF_INET
			)

			self.logger.info(f"서버 연결 성공: {self.host}:{self.port}")

			# 통신 시작
			await self.start_communication()

		except Exception as e:
			self.logger.error(f"서버 연결 실패: {e}")
			raise

	async def disconnect(self):
		"""
		서버 연결 종료
		"""
		await self.stop_communication()
		self.logger.info("서버 연결 종료")
