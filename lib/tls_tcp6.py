# -*- coding: utf-8 -*-
# IPv6 TLS TCP communication Framework
# made : hbesthee@naver.com
# date : 2025-07-02

# Original Packages
from asyncio import Queue, StreamReader, StreamWriter, Task, create_task, sleep
from asyncio import start_server, open_connection, wait_for
from ssl import SSLContext, PROTOCOL_TLS_SERVER, PROTOCOL_TLS_CLIENT
from ssl import Purpose, create_default_context
from typing import Dict, Optional, Type, Any, Callable
from uuid import uuid4, UUID
from time import time
from logging import getLogger, Logger

import asyncio
import socket




class BaseParser:
	"""
	바이트 데이터 파서 기본 클래스

	데이터 큐에서 받은 바이트 데이터를 메시지 패킷으로 분석하여
	메시지 패킷 큐에 전달하는 역할을 담당합니다.
	"""

	def __init__(self, data_queue: Queue, packet_queue: Queue):
		"""
		BaseParser 생성자

		Args:
			data_queue (Queue): 원시 데이터를 받는 큐
			packet_queue (Queue): 분석된 메시지 패킷을 전달하는 큐
		"""
		self._data_queue = data_queue
		self._packet_queue = packet_queue
		self._running = False
		self._parse_task: Optional[Task] = None

	async def parse(self) -> None:
		"""
		데이터 큐에서 바이트 데이터를 받아 메시지 패킷으로 분석하는 코루틴

		기본 동작은 바이트 데이터를 문자열로 변환하여 메시지 큐에 전달합니다.
		"""
		while self._running:
			try:
				# 데이터 큐에서 바이트 데이터 대기
				data = await wait_for(self._data_queue.get(), timeout=0.1)

				# 바이트 데이터를 문자열로 변환
				message = data.decode('utf-8', errors='ignore')

				# 메시지 패킷 큐에 전달
				await self._packet_queue.put(message)

			except asyncio.TimeoutError:
				# 타임아웃 시 계속 대기
				continue
			except Exception as e:
				# 예외 발생 시 로깅 후 계속 진행
				print(f"Parser error: {e}")
				await sleep(0.1)

	def start(self) -> None:
		"""
		파서 시작 - parse() 코루틴을 비동기 태스크로 실행
		"""
		self._running = True
		self._parse_task = create_task(self.parse())

	def stop(self) -> None:
		"""
		파서 중지 - 실행 중인 파싱 작업을 종료
		"""
		self._running = False
		if self._parse_task:
			self._parse_task.cancel()


class TlsTcp6Socket:
	"""
	TLS 1.3 기반 IPv6 TCP 소켓 통신 클래스

	서버와 클라이언트에서 공통으로 사용되는 기능을 제공합니다.
	X509 PKI 인증서를 통한 상호 인증을 지원합니다.
	"""

	def __init__(
		self,
		host: str = "::1",
		port: int = 8888,
		certfile: Optional[str] = None,
		keyfile: Optional[str] = None,
		cafile: Optional[str] = None,
		packet_queue: Optional[Queue] = None,
		logger_name: str = "tls_tcp6",
		parser_class: Type[BaseParser] = BaseParser,
		reader: Optional[StreamReader] = None,
		writer: Optional[StreamWriter] = None,
		**kwargs
	):
		"""
		TlsTcp6Socket 생성자

		Args:
			host (str): 연결할 호스트 주소 (기본값: "::1")
			port (int): 연결할 포트 번호 (기본값: 8888)
			certfile (Optional[str]): 인증서 파일 경로
			keyfile (Optional[str]): 개인키 파일 경로
			cafile (Optional[str]): CA 인증서 파일 경로
			packet_queue (Optional[Queue]): 메시지 패킷 큐
			logger_name (str): 로거 이름 (기본값: "tls_tcp6")
			parser_class (Type[BaseParser]): 파서 클래스 타입
			reader (Optional[StreamReader]): 스트림 리더 객체
			writer (Optional[StreamWriter]): 스트림 라이터 객체
			**kwargs: 추가 키워드 인수
		"""
		self._host = host
		self._port = port
		self._certfile = certfile
		self._keyfile = keyfile
		self._cafile = cafile
		self._packet_queue = packet_queue or Queue()
		self._logger: Logger = getLogger(logger_name)
		self._parser_class = parser_class
		self._uuid: UUID = uuid4()

		# 스트림 객체
		self._reader: Optional[StreamReader] = reader
		self._writer: Optional[StreamWriter] = writer

		# 시간 정보
		self._connected_time: Optional[float] = None
		self._last_received_time: Optional[float] = None

		# 내부 큐
		self._data_queue: Queue = Queue()
		self._send_queue: Queue = Queue()

		# 파서 및 핸들러
		self._parser: BaseParser = self._parser_class(self._data_queue, self._packet_queue)

		# 태스크 관리
		self._recv_task: Optional[Task] = None
		self._send_task: Optional[Task] = None
		self._packet_task: Optional[Task] = None

		# 실행 상태
		self._running = False

		# 서버 참조 (서버에서 클라이언트 연결 시 사용)
		self.server: Optional[Any] = kwargs.get('server')

	def create_ssl_context(self) -> SSLContext:
		"""
		SSL 컨텍스트 생성

		Returns:
			SSLContext: 생성된 SSL 컨텍스트
		"""
		context = create_default_context(Purpose.SERVER_AUTH)

		if self._certfile and self._keyfile:
			context.load_cert_chain(self._certfile, self._keyfile)

		if self._cafile:
			context.load_verify_locations(self._cafile)

		return context

	def process_received_data(self, data: bytes) -> bytes:
		"""
		수신 데이터 후처리 메서드

		Args:
			data (bytes): 수신된 원시 데이터

		Returns:
			bytes: 처리된 데이터 (기본값: 원본 데이터 반환)
		"""
		return data

	async def _recv_handler(self) -> None:
		"""
		데이터 수신 핸들러

		스트림에서 데이터를 수신하여 처리합니다.
		"""
		if not self._reader:
			return

		# 최초 접속 시각 기록
		self._connected_time = time()
		self._last_received_time = self._connected_time

		try:
			while self._running:
				# 데이터 수신
				data = await self._reader.read(4096)

				if not data:
					# 연결이 끊어진 경우
					break

				# 마지막 수신 시각 갱신
				self._last_received_time = time()

				# 수신 데이터 후처리
				processed_data = self.process_received_data(data)

				# 데이터 큐에 추가
				await self._data_queue.put(processed_data)

		except Exception as e:
			self._logger.error(f"수신 핸들러 오류 [{self._uuid}]: {e}")
		finally:
			await self._close_connection()

	async def _send_handler(self) -> None:
		"""
		데이터 송신 핸들러

		송신 큐에서 데이터를 순차적으로 전송합니다.
		"""
		if not self._writer:
			return

		try:
			while self._running:
				try:
					# 송신 큐에서 데이터 대기
					data = await wait_for(self._send_queue.get(), timeout=0.5)

					# 데이터 전송
					self._writer.write(data)
					await self._writer.drain()

				except asyncio.TimeoutError:
					continue
		except Exception as e:
			self._logger.error(f"송신 핸들러 오류 [{self._uuid}]: {e}")
		finally:
			await self._close_connection()

	async def _packet_handler(self) -> None:
		"""
		메시지 패킷 처리 핸들러

		메시지 패킷 큐에서 메시지를 받아 처리합니다.
		기본 동작은 메시지를 출력하고 클라이언트로 에코합니다.
		"""
		try:
			while self._running:
				try:
					# 메시지 패킷 큐에서 메시지 대기
					message = await wait_for(self._packet_queue.get(), timeout=0.1)

					# 메시지 출력
					self._logger.info(f"수신 메시지 [{self._uuid}]: {message}")

					# 메시지를 바이트로 변환하여 에코
					echo_data = message.encode('utf-8')
					await self.send(echo_data)
				except asyncio.TimeoutError:
					continue
		except Exception as e:
			self._logger.error(f"패킷 핸들러 오류 [{self._uuid}]: {e}")

	async def send(self, data: bytes) -> None:
		"""
		데이터 송신

		Args:
			data (bytes): 전송할 데이터
		"""
		await self._send_queue.put(data)

	async def start(self) -> None:
		"""
		소켓 통신 시작

		수신, 송신, 패킷 처리 핸들러를 비동기 태스크로 실행합니다.
		"""
		self._running = True

		# 파서 시작
		self._parser.start()

		# 핸들러 태스크 시작
		self._recv_task = create_task(self._recv_handler())
		self._send_task = create_task(self._send_handler())
		self._packet_task = create_task(self._packet_handler())

	async def stop(self) -> None:
		"""
		소켓 통신 중지

		모든 핸들러를 종료하고 연결을 정리합니다.
		"""
		self._running = False

		# 파서 중지
		self._parser.stop()

		# 태스크 취소
		if self._recv_task:
			self._recv_task.cancel()
		if self._send_task:
			self._send_task.cancel()
		if self._packet_task:
			self._packet_task.cancel()

		await self._close_connection()

	async def _close_connection(self) -> None:
		"""
		연결 종료 처리
		"""
		if self._writer:
			self._writer.close()
			await self._writer.wait_closed()

		self._logger.info(f"연결 종료 [{self._uuid}]")

	@property
	def uuid(self) -> UUID:
		"""소켓 UUID 반환"""
		return self._uuid

	@property
	def connected_time(self) -> Optional[float]:
		"""최초 접속 시각 반환"""
		return self._connected_time

	@property
	def last_received_time(self) -> Optional[float]:
		"""마지막 데이터 수신 시각 반환"""
		return self._last_received_time


class TlsTcp6Server:
	"""
	TLS 1.3 기반 IPv6 TCP 서버 클래스

	다중 클라이언트 연결을 처리하고 관리합니다.
	"""

	def __init__(
		self,
		*args,
		host: str = "::1",
		port: int = 8888,
		certfile: Optional[str] = None,
		keyfile: Optional[str] = None,
		cafile: Optional[str] = None,
		logger_name: str = "tls_tcp6",
		socket_class: Type[TlsTcp6Socket] = TlsTcp6Socket,
		timeout: float = 60.0,
		**kwargs
	):
		"""
		TlsTcp6Server 생성자

		Args:
			*args: 위치 인수
			host (str): 서버 바인딩 주소 (기본값: "::1")
			port (int): 서버 포트 번호 (기본값: 8888)
			certfile (Optional[str]): 인증서 파일 경로
			keyfile (Optional[str]): 개인키 파일 경로
			cafile (Optional[str]): CA 인증서 파일 경로
			logger_name (str): 로거 이름 (기본값: "tls_tcp6")
			socket_class (Type[TlsTcp6Socket]): 소켓 클래스 타입
			timeout (float): 연결 타임아웃 시간 (기본값: 60초)
			**kwargs: 추가 키워드 인수
		"""
		self._host = host
		self._port = port
		self._certfile = certfile
		self._keyfile = keyfile
		self._cafile = cafile
		self._logger: Logger = getLogger(logger_name)
		self._socket_class = socket_class
		self._timeout = timeout
		self._kwargs = kwargs

		# 클라이언트 연결 관리
		self._clients: Dict[UUID, TlsTcp6Socket] = {}

		# 서버 상태
		self._running = False
		self._server: Optional[Any] = None
		self._cleanup_task: Optional[Task] = None

	def create_ssl_context(self) -> SSLContext:
		"""
		서버용 SSL 컨텍스트 생성

		Returns:
			SSLContext: 생성된 SSL 컨텍스트
		"""
		context = SSLContext(PROTOCOL_TLS_SERVER)

		if self._certfile and self._keyfile:
			context.load_cert_chain(self._certfile, self._keyfile)

		if self._cafile:
			context.load_verify_locations(self._cafile)

		return context

	async def _handle_client(self, reader: StreamReader, writer: StreamWriter) -> None:
		"""
		클라이언트 연결 처리

		Args:
			reader (StreamReader): 스트림 리더
			writer (StreamWriter): 스트림 라이터
		"""
		# 클라이언트 소켓 생성
		client_socket = self._socket_class(
			host=self._host,
			port=self._port,
			certfile=self._certfile,
			keyfile=self._keyfile,
			cafile=self._cafile,
			packet_queue=Queue(),
			reader=reader,
			writer=writer,
			server=self,
			**self._kwargs
		)

		# 클라이언트 목록에 추가
		self._clients[client_socket.uuid] = client_socket

		self._logger.info(f"클라이언트 연결 [{client_socket.uuid}]")

		# 클라이언트 소켓 시작
		await client_socket.start()

	async def _cleanup_clients(self) -> None:
		"""
		비정상 연결 및 타임아웃 클라이언트 정리
		"""
		while self._running:
			try:
				current_time = time()
				cleanup_list = []

				for uuid, client in self._clients.items():
					# 타임아웃 검사
					if (client.last_received_time and
						current_time - client.last_received_time > self._timeout):
						cleanup_list.append(uuid)

				# 타임아웃된 클라이언트 정리
				for uuid in cleanup_list:
					client = self._clients.pop(uuid, None)
					if client:
						await client.stop()
						self._logger.info(f"타임아웃 클라이언트 정리 [{uuid}]")

				# 1초마다 정리 작업 수행
				await sleep(1.0)

			except Exception as e:
				self._logger.error(f"클라이언트 정리 오류: {e}")
				await sleep(1.0)

	async def start(self) -> None:
		"""
		서버 시작
		"""
		self._running = True

		# SSL 컨텍스트 생성
		ssl_context = self.create_ssl_context()

		# 서버 시작
		self._server = await start_server(
			self._handle_client,
			self._host,
			self._port,
			ssl=ssl_context,
			family=socket.AF_INET6
		)

		# 클라이언트 정리 태스크 시작
		self._cleanup_task = create_task(self._cleanup_clients())

		self._logger.info(f"서버 시작 [{self._host}]:{self._port}")

	async def stop(self) -> None:
		"""
		서버 중지
		"""
		self._running = False

		# 클라이언트 정리 태스크 중지
		if self._cleanup_task:
			self._cleanup_task.cancel()

		# 모든 클라이언트 연결 종료
		for client in self._clients.values():
			await client.stop()

		self._clients.clear()

		# 서버 중지
		if self._server:
			self._server.close()
			await self._server.wait_closed()

		self._logger.info("서버 중지")

	@property
	def clients(self) -> Dict[UUID, TlsTcp6Socket]:
		"""연결된 클라이언트 목록 반환"""
		return self._clients.copy()


class TlsTcp6Client:
	"""
	TLS 1.3 기반 IPv6 TCP 클라이언트 클래스
	"""

	def __init__(
		self,
		*args,
		host: str = "::1",
		port: int = 8888,
		certfile: Optional[str] = None,
		keyfile: Optional[str] = None,
		cafile: Optional[str] = None,
		logger_name: str = "tls_tcp6",
		parser_class: Type[BaseParser] = BaseParser,
		check_hostname: bool = True,
		**kwargs
	):
		"""
		TlsTcp6Client 생성자

		Args:
			*args: 위치 인수
			host (str): 서버 주소 (기본값: "::1")
			port (int): 서버 포트 번호 (기본값: 8888)
			certfile (Optional[str]): 인증서 파일 경로
			keyfile (Optional[str]): 개인키 파일 경로
			cafile (Optional[str]): CA 인증서 파일 경로
			logger_name (str): 로거 이름 (기본값: "tls_tcp6")
			parser_class (Type[BaseParser]): 파서 클래스 타입
			check_hostname (bool): 호스트네임 검증 여부 (기본값: True)
			**kwargs: 추가 키워드 인수
		"""
		self._host = host
		self._port = port
		self._certfile = certfile
		self._keyfile = keyfile
		self._cafile = cafile
		self._logger: Logger = getLogger(logger_name)
		self._parser_class = parser_class
		self.check_hostname = check_hostname
		self._kwargs = kwargs

		# 클라이언트 소켓
		self._socket: Optional[TlsTcp6Socket] = None

	def create_ssl_context(self) -> SSLContext:
		"""
		클라이언트용 SSL 컨텍스트 생성

		Returns:
			SSLContext: 생성된 SSL 컨텍스트
		"""
		context = SSLContext(PROTOCOL_TLS_CLIENT)
		context.check_hostname = self.check_hostname

		if self._certfile and self._keyfile:
			context.load_cert_chain(self._certfile, self._keyfile)

		if self._cafile:
			context.load_verify_locations(self._cafile)

		return context

	async def connect(self) -> None:
		"""
		서버에 연결
		"""
		# SSL 컨텍스트 생성
		ssl_context = self.create_ssl_context()

		# 서버 연결
		reader, writer = await open_connection(
			self._host,
			self._port,
			ssl=ssl_context,
			family=socket.AF_INET6
		)

		# 클라이언트 소켓 생성
		self._socket = TlsTcp6Socket(
			host=self._host,
			port=self._port,
			certfile=self._certfile,
			keyfile=self._keyfile,
			cafile=self._cafile,
			packet_queue=Queue(),
			parser_class=self._parser_class,
			reader=reader,
			writer=writer,
			**self._kwargs
		)

		# 소켓 시작
		await self._socket.start()

		self._logger.info(f"서버 연결 [{self._host}]:{self._port}")

	async def send(self, data: bytes) -> None:
		"""
		데이터 전송

		Args:
			data (bytes): 전송할 데이터
		"""
		if self._socket:
			await self._socket.send(data)

	async def disconnect(self) -> None:
		"""
		서버 연결 해제
		"""
		if self._socket:
			await self._socket.stop()
			self._socket = None

		self._logger.info("서버 연결 해제")

	@property
	def socket(self) -> Optional[TlsTcp6Socket]:
		"""클라이언트 소켓 반환"""
		return self._socket