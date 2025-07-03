# -*- coding: utf-8 -*-
# IPv6 TLS TCP communication Framework
# made : hbesthee@naver.com
# date : 2025-07-02

# Original Packages
from abc import ABC, abstractmethod
from asyncio import Queue, Task, StreamReader, StreamWriter
from logging import getLogger, Logger
from time import time
from typing import Final, Optional, Dict, Any, Type, Union
from uuid import uuid4, UUID

import asyncio
import ssl




class TlsTcp6Key:
	LOGGER_LEVEL: Final		= 20 # logging.INFO
	LOGGER_NAME: Final		= 'tls_tcp6'



class BaseParser(ABC):
	"""바이트 데이터를 메시지 패킷으로 파싱하는 기본 클래스"""

	def __init__(self, data_queue: Queue[bytes], packet_queue: Queue[Any], logger_name:str = TlsTcp6Key.LOGGER_NAME):
		"""
		BaseParser 생성자

		Args:
			data_queue: 수신된 바이트 데이터를 담는 큐 (input)
			packet_queue: 파싱된 메시지 패킷을 담는 큐 (output)
		"""
		self.data_queue = data_queue
		self.packet_queue = packet_queue # 메시지 패킷 큐
		self._running = False
		self._parse_task: Optional[Task] = None
		self.logger = getLogger(logger_name)

		self.logger.debug(f"BaseParser 초기화: {data_queue=}, {packet_queue=}")


	def parse(self) -> Any:
		"""파서에서 받은 바이트 데이터들을 조합 분석하여 패킷을 생성하여 메시지 패킷 큐에 입력합니다.
			기본 동작: 바이트 데이터를 문자열로 변환하여 메시지 패킷 큐에 입력
		"""
		# 바이트 데이터를 문자열로 변환하여 패킷 큐에 입력
		data = self._buf.decode('utf-8', errors='ignore')
		self._buf = b"" # 버퍼 초기화
		return data


	async def parse_handler(self) -> None:
		""" 비동기적으로 데이터 큐에서 바이트 데이터를 읽어 메시지 패킷으로 분석/변환하여 패킷 큐에 입력
			하위 파서 클래스에서 parse() 함수 내부에서 바이트 데이터를 목적에 맞게 패킷으로 파싱하여 패킷 큐에 입력
		"""
		self._buf = b"" # 내부 버퍼
		while self._running: # 타임아웃을 두어 주기적으로 _running 상태 확인
			try:
				data = await asyncio.wait_for(self.data_queue.get(), timeout=1.0)
				if (data == None):
					break # 파싱 루틴 종료

				if isinstance(data, str):
					data = data.encode()
				if isinstance(data, bytes):
					self._buf += data
					packet = self.parse()
					if (packet):
						await self.packet_queue.put(packet)
				self.data_queue.task_done()
			except asyncio.TimeoutError:
				continue # 타임아웃은 정상 ; _running 상태 확인
			except Exception as e:
				# 파싱 중 예외 발생 시 로깅 후 계속 처리
				self.logger.error(f'parse_handler error: {e}')
				continue
		self.logger.error(f'parse_handler terminated.')


	def start(self) -> None:
		"""파서 시작 - 비동기 파싱 작업 시작"""
		if not self._running:
			self._running = True
			self._parse_task = asyncio.create_task(self.parse_handler())


	async def stop(self) -> None:
		"""파서 중지 - 비동기 파싱 작업 중지"""
		self._running = False
		# await self.data_queue.put(None)
		if self._parse_task and not self._parse_task.done():
			self._parse_task.cancel()


class TlsTcp6Socket:
	"""IPv6 TCP TLS 소켓 통신을 위한 기본 클래스"""

	def __init__(self, host: str = "::1", port: int = 8888,
					cert_file: Optional[str] = None, key_file: Optional[str] = None,
					ca_file: Optional[str] = None, packet_queue: Optional[Queue] = None,
					logger_name: str = "tls_tcp6", parser_class: Type[BaseParser] = BaseParser,
					reader: Optional[StreamReader] = None, writer: Optional[StreamWriter] = None,
					**kwargs):
		"""
		TlsTcp6Socket 생성자

		Args:
			host: 연결할 호스트 주소 (기본값: "::1")
			port: 연결할 포트 번호 (기본값: 8888)
			cert_file: 인증서 파일 경로
			key_file: 개인키 파일 경로
			ca_file: CA 인증서 파일 경로
			packet_queue: 메시지 패킷 큐
			logger_name: 로거 이름 (기본값: "tls_tcp6")
			parser_class: 파서 클래스 타입 (기본값: BaseParser)
			reader: StreamReader 객체 (서버에서 클라이언트 연결 시 사용)
			writer: StreamWriter 객체 (서버에서 클라이언트 연결 시 사용)
			**kwargs: 추가 키워드 인자
		"""
		self.host = host
		self.port = port
		self.cert_file = cert_file
		self.key_file = key_file
		self.ca_file = ca_file
		self.packet_queue: Optional[Queue] = packet_queue
		self.parser_class = parser_class
		self.reader = reader
		self.writer = writer
		self.logger: Logger = getLogger(logger_name)
		self.uuid: UUID = uuid4() # 소켓 고유번호

		# 시간 정보 초기화
		self._connected_time: float = 0.0
		self._last_received_time: float = 0.0

		# 큐 초기화
		self._data_queue = Queue() # 내부용 수신용 큐
		self._send_queue = Queue() # 내부용 송신용 큐

		# 파서 초기화
		self.parser: BaseParser = None
		if (self.packet_queue != None):
			self.parser = self.parser_class(self._data_queue, self.packet_queue)

		# 작업 관리
		self._running = False
		self._tasks: list[Task] = []

		# 서버 참조 (클라이언트 연결에서 사용)
		self.server: Optional['TlsTcp6Server'] = kwargs.get('server')


	def create_ssl_context(self) -> ssl.SSLContext:
		"""
		TLS 연결을 위한 SSL 컨텍스트 생성

		Returns:
			생성된 SSL 컨텍스트
		"""
		context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
		context.minimum_version = ssl.TLSVersion.TLSv1_3

		if self.cert_file and self.key_file:
			context.load_cert_chain(self.cert_file, self.key_file)

		if self.ca_file:
			context.load_verify_locations(self.ca_file)
			context.verify_mode = ssl.CERT_REQUIRED

		return context

	def process_received_data(self, data: bytes) -> bytes:
		"""
		수신된 데이터 후처리 메소드

		Args:
			data: 수신된 바이트 데이터

		Returns:
			후처리된 바이트 데이터
		"""
		return data

	async def _recv_handler(self) -> None:
		"""데이터 수신 핸들러"""
		if not self.reader:
			return

		# 최초 접속 시각 설정
		self._connected_time = time()
		self._last_received_time = self._connected_time

		try:
			while self._running:
				data = await self.reader.read(4096)
				if not data:
					break

				# 마지막 데이터 수신 시각 갱신
				self._last_received_time = time()

				# 수신 데이터 후처리
				processed_data = self.process_received_data(data)

				# 데이터 큐에 입력
				await self._data_queue.put(processed_data)

		except Exception as e:
			self.logger.error(f"수신 핸들러 오류 [{self.uuid}]: {e}")
		finally:
			await self._cleanup()

	async def _send_handler(self) -> None:
		"""데이터 송신 핸들러"""
		if not self.writer:
			return

		try:
			while self._running:
				try:
					# 타임아웃을 두어 주기적으로 _running 상태 확인
					data = await asyncio.wait_for(self._send_queue.get(), timeout=1.0)
					if isinstance(data, (str, bytes)):
						if isinstance(data, str):
							data = data.encode('utf-8')

						self.writer.write(data)
						await self.writer.drain()
						self._send_queue.task_done()
				except asyncio.TimeoutError:
					continue

		except Exception as e:
			self.logger.error(f"송신 핸들러 오류 [{self.uuid}]: {e}")
		finally:
			await self._cleanup()

	async def _packet_handler(self) -> None:
		"""메시지 패킷 처리 핸들러"""
		try:
			while self._running:
				try:
					# 타임아웃을 두어 주기적으로 _running 상태 확인
					packet = await asyncio.wait_for(self._packet_queue.get(), timeout=1.0)
					self.logger.info(f"수신 패킷 [{self.uuid}]: {packet}")

					# 받은 메시지를 그대로 전송
					await self.send(packet)
					self._packet_queue.task_done()
				except asyncio.TimeoutError:
					continue

		except Exception as e:
			self.logger.error(f"패킷 핸들러 오류 [{self.uuid}]: {e}")

	async def send(self, data: Union[str, bytes]) -> None:
		"""
		데이터 송신 (외부 인터페이스)

		Args:
			data: 송신할 데이터 (문자열 또는 바이트)
		"""
		if self._running:
			await self._send_queue.put(data)

	async def start(self) -> None:
		"""소켓 통신 시작"""
		if self._running:
			return

		self._running = True

		# 파서 시작
		self.parser.start()

		# 핸들러 작업 시작
		self._tasks = [
			asyncio.create_task(self._recv_handler()),
			asyncio.create_task(self._send_handler()),
			asyncio.create_task(self._packet_handler())
		]

		self.logger.info(f"소켓 통신 시작 [{self.uuid}]")

	async def stop(self) -> None:
		"""소켓 통신 중지"""
		if not self._running:
			return

		self._running = False

		# 파서 중지
		self.parser.stop()

		# 작업 취소
		for task in self._tasks:
			if not task.done():
				task.cancel()

		# 작업 완료 대기
		if self._tasks:
			await asyncio.gather(*self._tasks, return_exceptions=True)

		await self._cleanup()

		self.logger.info(f"소켓 통신 중지 [{self.uuid}]")

	async def _cleanup(self) -> None:
		"""리소스 정리"""
		if self.writer:
			try:
				self.writer.close()
				await self.writer.wait_closed()
			except Exception as e:
				self.logger.error(f"Writer 정리 오류 [{self.uuid}]: {e}")

		self.reader = None
		self.writer = None

	def is_timeout(self, timeout_seconds: float = 60.0) -> bool:
		"""
		연결 타임아웃 확인

		Args:
			timeout_seconds: 타임아웃 시간 (초, 기본값: 60초)

		Returns:
			타임아웃 여부
		"""
		if not self._last_received_time:
			return False

		return (time() - self._last_received_time) > timeout_seconds


class TlsTcp6Server(TlsTcp6Socket):
	"""IPv6 TCP TLS 서버 클래스"""

	def __init__(self, *args, socket_class: Type[TlsTcp6Socket] = TlsTcp6Socket, **kwargs):
		"""
		TlsTcp6Server 생성자

		Args:
			*args: 위치 인자
			socket_class: 클라이언트 연결에 사용할 소켓 클래스
			**kwargs: 키워드 인자
		"""
		super().__init__(*args, **kwargs)
		self.socket_class = socket_class
		self.clients: Dict[UUID, TlsTcp6Socket] = {}
		self._server: Optional[asyncio.Server] = None
		self._cleanup_task: Optional[Task] = None

	async def _handle_client(self, reader: StreamReader, writer: StreamWriter) -> None:
		"""
		클라이언트 연결 처리

		Args:
			reader: 클라이언트 StreamReader
			writer: 클라이언트 StreamWriter
		"""
		client_socket = self.socket_class(
			host=self.host,
			port=self.port,
			cert_file=self.cert_file,
			key_file=self.key_file,
			ca_file=self.ca_file,
			packet_queue=Queue(),
			logger_name=self.logger.name,
			parser_class=self.parser_class,
			reader=reader,
			writer=writer,
			server=self
		)

		# 클라이언트 목록에 추가
		self.clients[client_socket.uuid] = client_socket

		client_addr = writer.get_extra_info('peername')
		self.logger.info(f"클라이언트 연결 [{client_socket.uuid}]: {client_addr}")

		try:
			await client_socket.start()

			# 클라이언트 연결 유지
			while client_socket._running:
				await asyncio.sleep(1.0)

		except Exception as e:
			self.logger.error(f"클라이언트 처리 오류 [{client_socket.uuid}]: {e}")
		finally:
			# 클라이언트 정리
			await client_socket.stop()
			if client_socket.uuid in self.clients:
				del self.clients[client_socket.uuid]

			self.logger.info(f"클라이언트 연결 종료 [{client_socket.uuid}]")

	async def _cleanup_clients(self) -> None:
		"""타임아웃된 클라이언트 정리"""
		while self._running:
			try:
				await asyncio.sleep(10.0)  # 10초마다 확인

				timeout_clients = []
				for client_uuid, client in self.clients.items():
					if client.is_timeout():
						timeout_clients.append(client_uuid)

				for client_uuid in timeout_clients:
					client = self.clients.get(client_uuid)
					if client:
						self.logger.info(f"타임아웃 클라이언트 정리 [{client_uuid}]")
						await client.stop()

			except Exception as e:
				self.logger.error(f"클라이언트 정리 오류: {e}")

	async def start(self) -> None:
		"""서버 시작"""
		if self._running:
			return

		self._running = True

		# SSL 컨텍스트 생성
		ssl_context = self.create_ssl_context()

		# 서버 시작
		self._server = await asyncio.start_server(
			self._handle_client,
			self.host,
			self.port,
			ssl=ssl_context,
			family=asyncio.socket.AF_INET6
		)

		# 클라이언트 정리 작업 시작
		self._cleanup_task = asyncio.create_task(self._cleanup_clients())

		self.logger.info(f"서버 시작: {self.host}:{self.port}")

		# 서버 실행
		await self._server.serve_forever()

	async def stop(self) -> None:
		"""서버 중지"""
		if not self._running:
			return

		self._running = False

		# 서버 중지
		if self._server:
			self._server.close()
			await self._server.wait_closed()

		# 클라이언트 정리 작업 중지
		if self._cleanup_task and not self._cleanup_task.done():
			self._cleanup_task.cancel()

		# 모든 클라이언트 연결 종료
		for client in list(self.clients.values()):
			await client.stop()

		self.clients.clear()

		self.logger.info("서버 중지")


class TlsTcp6Client(TlsTcp6Socket):
	"""IPv6 TCP TLS 클라이언트 클래스"""

	def __init__(self, *args, check_hostname: bool = True, **kwargs):
		"""
		TlsTcp6Client 생성자

		Args:
			*args: 위치 인자
			check_hostname: 호스트명 검증 여부 (기본값: True)
			**kwargs: 키워드 인자
		"""
		super().__init__(*args, **kwargs)
		self.check_hostname = check_hostname

	def create_ssl_context(self) -> ssl.SSLContext:
		"""
		클라이언트용 SSL 컨텍스트 생성

		Returns:
			생성된 SSL 컨텍스트
		"""
		context = super().create_ssl_context()
		context.check_hostname = self.check_hostname
		return context

	async def connect(self) -> None:
		"""서버에 연결"""
		if self._running:
			return

		# SSL 컨텍스트 생성
		ssl_context = self.create_ssl_context()

		try:
			# 서버에 연결
			self._reader, self._writer = await asyncio.open_connection(
				self.host,
				self.port,
				ssl=ssl_context,
				family=asyncio.socket.AF_INET6
			)

			self.logger.info(f"서버 연결 성공: {self.host}:{self.port}")

			# 소켓 통신 시작
			await self.start()

		except Exception as e:
			self.logger.error(f"서버 연결 실패: {e}")
			raise

	async def disconnect(self) -> None:
		"""서버 연결 해제"""
		await self.stop()
		self.logger.info("서버 연결 해제")
