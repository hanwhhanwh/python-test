# -*- coding: utf-8 -*-
# IPv6 TLS TCP communication Framework
# made : hbesthee@naver.com
# date : 2025-07-02

# Original Packages
from abc import ABC, abstractmethod
from asyncio import Queue, Task, StreamReader, StreamWriter
from logging import getLogger, Logger
from time import time
from typing import Final, Optional, Dict, Any, Set, Type, Union
from uuid import uuid4, UUID

import asyncio
import socket
import ssl
import uuid




class TlsTcp6Def:
	BUFFER_SIZE: Final			= 4096
	HOST: Final					= '::1'
	LOGGER_LEVEL: Final			= 20 # logging.INFO
	LOGGER_NAME: Final			= 'tls_tcp6'
	IDLE_TIMEOUT: Final			= 60
	PORT: Final					= 15118



class TlsTcp6Key:
	SOCKET_CLASS: Final			= 'socket_class'
	IDLE_TIMEOUT: Final			= 'idle_timeout'



class BaseParser(ABC):
	"""바이트 데이터를 메시지 패킷으로 파싱하는 기본 클래스"""

	def __init__(self, parser_uuid: uuid.UUID
				, data_queue: Queue[bytes]
				, packet_queue: Queue[Any]
				, logger_name:str=TlsTcp6Def.LOGGER_NAME):
		"""
		BaseParser 생성자

		Args:
			parser_uuid: 파서를 구별하기 위한 고유 UUID
			data_queue: 수신된 바이트 데이터를 담는 큐 (input)
			packet_queue: 파싱된 메시지 패킷을 담는 큐 (output)
		"""
		self._buf: bytearray = bytearray()
		self._running = False
		self._parse_task: Optional[Task] = None
		self.uuid = parser_uuid
		self.data_queue = data_queue
		self.packet_queue = packet_queue # 메시지 패킷 큐
		self.logger = getLogger(logger_name)

		self.logger.debug(f"BaseParser 초기화: {data_queue=}, {packet_queue=}")


	def parse(self) -> list[Any] | None:
		"""파서에서 받은 바이트 데이터들을 조합 분석하여 패킷을 생성하여 메시지 패킷 큐에 입력합니다.
			기본 동작: 바이트 데이터를 문자열로 변환하여 메시지 패킷 큐에 입력
		"""
		if (len(self._buf) == 0):
			return None
		# 바이트 데이터를 문자열로 변환하여 패킷 큐에 입력
		try:
			packet = self._buf.decode('utf-8')
			self._buf.clear()
			return [packet]
		except UnicodeDecodeError:
			self.logger.warning("UTF-8 디코딩 실패. 버퍼를 비웁니다.")
			self._buf.clear()
			return None


	async def parse_handler(self) -> None:
		""" 비동기적으로 데이터 큐에서 바이트 데이터를 읽어 메시지 패킷으로 분석/변환하여 패킷 큐에 입력
			하위 파서 클래스에서 parse() 함수 내부에서 바이트 데이터를 목적에 맞게 패킷으로 파싱하여 패킷 큐에 입력
		"""
		while self._running: # 타임아웃을 두어 주기적으로 _running 상태 확인
			try:
				# data = await asyncio.wait_for(self.data_queue.get(), timeout=1.0)
				data = await self.data_queue.get()
				try:
					if (data == None):
						break # 파싱 루틴 종료

					if isinstance(data, str):
						data = data.encode()
					if isinstance(data, bytes):
						self._buf.extend(data)
						packets = self.parse()
						if (packets):
							for packet in packets:
								await self.packet_queue.put((self.uuid, packet))
				finally:
					self.data_queue.task_done()
			# except asyncio.TimeoutError:
			# 	continue # 타임아웃은 정상 ; _running 상태 확인
			except Exception as e:
				# 파싱 중 예외 발생 시 로깅 후 계속 처리
				self.logger.error(f'parse_handler error: {e}')
				break
		self.logger.error(f'{self.__class__.__name__} 파서 종료: {self.uuid}')


	def start(self) -> None:
		"""파서 시작 - 비동기 파싱 작업 시작"""
		if not self._running:
			self._running = True
			self._parse_task = asyncio.create_task(self.parse_handler())
			self.logger.info(f'{self.__class__.__name__} 파서 시작: {self.uuid}')


	async def stop(self) -> None:
		"""파서 중지 - 비동기 파싱 작업 중지"""
		self._running = False
		# await self.data_queue.put(None)
		if (self._parse_task and (not self._parse_task.done())):
			self._parse_task.cancel()



class TlsTcp6Socket:
	"""
	TLS 기반 IPv6 TCP 통신을 위한 공통 기능을 제공하는 부모 클래스입니다.<br />
	서버와 클라이언트 클래스가 이 클래스를 상속받습니다.
	"""
	def __init__(self,
					cert_file: str,
					key_file: str,
					ca_file: str,
					host: str=TlsTcp6Def.HOST,
					port: int=TlsTcp6Def.PORT,
					logger_name: str=TlsTcp6Def.LOGGER_NAME,
					**kwargs):
		"""TlsTcp6Socket 클래스의 생성자입니다.

		Args:
			cert_file: SSL 인증서 파일 경로입니다.
			key_file: SSL 개인 키 파일 경로입니다.
			ca_file: CA 인증서 파일 경로입니다.
			host: 접속할 호스트 주소(IPv6)입니다.
			port: 접속할 포트 번호입니다.
			logger_name: 사용할 로거의 이름입니다.
			kwargs: 추가적인 키워드 인자입니다.
				- packet_queue (Queue): 외부에서 생성된 패킷 큐.
				- parser_class (Type[BaseParser]): 사용할 파서 클래스.
				- rx_stream (StreamReader): (서버용) 연결된 클라이언트의 StreamReader.
				- tx_stream (StreamWriter): (서버용) 연결된 클라이언트의 StreamWriter.
				- server (TlsTcp6Server): (서버용) 서버 객체 참조.
		"""
		self.host = host
		self.port = port
		self.cert_file = cert_file
		self.key_file = key_file
		self.ca_file = ca_file
		self.logger = getLogger(logger_name)

		# 멤버 변수 초기화
		self._is_server: bool = False
		self.uuid: UUID = uuid4()
		self.server: Optional[TlsTcp6Server] = kwargs.get('server')

		self._rx_queue: Queue = Queue()
		self._tx_queue: Queue = Queue()
		self.packet_queue: Queue = kwargs.get('packet_queue')
		self._parser_class: Type[BaseParser] = kwargs.get('parser_class', BaseParser)
		self._parser: Optional[BaseParser] = None

		self._rx_stream: Optional[StreamReader] = kwargs.get('rx_stream')
		self._tx_stream: Optional[StreamWriter] = kwargs.get('tx_stream')

		self._connected_time: float = 0.0
		self._last_received_time: float = 0.0

		self._tasks: Set[Task] = set()
		self._is_closing: bool = False

		self._init_socket()


	def _init_socket(self):
		"""소켓 관련 내부 변수를 초기화합니다."""
		self.uuid = uuid4()
		self.logger.name = f"{self.logger.name}.{self.uuid}"

		if (self.packet_queue is None):
			self.packet_queue = Queue()
			self.logger.info("패킷 큐가 내부적으로 생성되었습니다.")

		self._parser = self._parser_class(
			parser_uuid=self.uuid,
			data_queue=self._rx_queue,
			packet_queue=self.packet_queue
		)
		self.logger.info(f"'{self._parser.__class__.__name__}' 파서 객체가 생성되었습니다.")


	def _create_ssl_context(self) -> ssl.SSLContext:
		"""상호 인증을 위한 SSLContext 객체를 생성하고 반환합니다.

		Returns:
			설정이 완료된 SSLContext 객체.
		"""
		purpose = ssl.Purpose.CLIENT_AUTH if self._is_server else ssl.Purpose.SERVER_AUTH
		context = ssl.create_default_context(purpose=purpose, cafile=self.ca_file)
		context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
		context.minimum_version = ssl.TLSVersion.TLSv1_3
		context.verify_mode = ssl.CERT_REQUIRED
		self.logger.info(f"SSL Context 생성 완료 (목적: {purpose.name})")
		return context


	async def _rx_handler(self):
		"""데이터 수신을 처리하는 코루틴 핸들러입니다.<br />
		StreamReader로부터 데이터를 읽어 파서의 데이터 큐에 넣습니다.
		"""
		if not self._rx_stream:
			self.logger.error("수신 핸들러: StreamReader가 설정되지 않았습니다.")
			return

		self._connected_time = time()
		self._last_received_time = self._connected_time
		self.logger.info("수신 핸들러가 시작되었습니다. 연결 시각이 기록되었습니다.")

		while not self._is_closing:
			try:
				data = await self._rx_stream.read(TlsTcp6Def.BUFFER_SIZE)
				if not data:
					self.logger.warning("연결이 원격 호스트에 의해 종료되었습니다.")
					break

				self._last_received_time = time()
				processed_data = self.process_received_data(data)
				await self._rx_queue.put(processed_data)

			except (asyncio.IncompleteReadError, ConnectionResetError) as e:
				self.logger.warning(f"연결이 비정상적으로 끊어졌습니다: {e}")
				break
			except asyncio.CancelledError:
				self.logger.info("수신 핸들러가 취소되었습니다.")
				break
			except Exception as e:
				self.logger.error(f"수신 핸들러에서 예외 발생: {e}", exc_info=True)
				break

		await self.close()


	def process_received_data(self, data: bytes) -> bytes:
		"""수신된 데이터를 후처리하는 메소드입니다.<br />
		기본적으로는 아무 처리 없이 그대로 반환합니다.<br />
		하위 클래스에서 필요에 따라 재정의하여 사용할 수 있습니다.

		Args:
			data: 수신된 원본 bytes 데이터입니다.

		Returns:
			후처리된 bytes 데이터입니다.
		"""
		return data


	async def _tx_handler(self):
		"""데이터 송신을 처리하는 코루틴 핸들러입니다.<br />
		송신 큐(_tx_queue)에서 데이터를 가져와 StreamWriter로 전송합니다.
		"""
		if not self._tx_stream:
			self.logger.error("TX 핸들러: StreamWriter가 설정되지 않았습니다.")
			return

		self.logger.info("송신 핸들러가 시작되었습니다.")
		while not self._is_closing:
			try:
				data: bytes = await self._tx_queue.get()
				try:
					self._tx_stream.write(data)
					await self._tx_stream.drain()
				finally:
					self._tx_queue.task_done()
			except asyncio.CancelledError:
				self.logger.info("송신 핸들러가 취소되었습니다.")
				break
			except Exception as e:
				self.logger.error(f"송신 핸들러에서 예외 발생: {e}", exc_info=True)
				break

		await self.close()


	async def send(self, data: bytes):
		"""외부에서 데이터를 송신할 때 사용하는 공개 메소드입니다.<br />
		내부 송신 큐에 데이터를 추가합니다.

		Args:
			data: 송신할 bytes 데이터입니다.
		"""
		if self._is_closing:
			self.logger.warning("연결이 종료되는 중이므로 데이터를 전송할 수 없습니다.")
			return
		await self._tx_queue.put(data)


	async def _start_handlers(self):
		"""내부 핸들러 및 파서 태스크를 시작합니다."""
		if self._parser:
			self._parser.start()

		rx_task = asyncio.create_task(self._rx_handler())
		tx_task = asyncio.create_task(self._tx_handler())
		self._tasks.add(rx_task)
		self._tasks.add(tx_task)


	async def close(self):
		"""연결을 종료하고 관련 리소스를 정리합니다."""
		if self._is_closing:
			return
		self._is_closing = True

		self.logger.info(f"{self.uuid} 연결 종료를 시작합니다.")

		# 파서 종료
		if self._parser:
			await self._parser.stop()

		# 태스크 취소
		for task in self._tasks:
			if not task.done():
				task.cancel()

		# if self._tasks:
		# 	await asyncio.gather(*self._tasks, return_exceptions=True)
		self._tasks.clear()

		# 스트림 닫기
		if self._tx_stream and not self._tx_stream.is_closing():
			self._tx_stream.close()
			try:
				await self._tx_stream.wait_closed()
			except Exception as e:
				self.logger.warning(f"StreamWriter 종료 중 예외 발생: {e}")

		# 서버에 연결된 클라이언트인 경우, 서버의 클라이언트 목록에서 제거
		if (self.server and (self.uuid in self.server._clients)):
			self.server.remove_client(self.uuid)

		self.logger.info(f"{self.uuid} 연결이 완전히 종료되었습니다.")




class TlsTcp6Server(TlsTcp6Socket):
	"""TLS 기반 IPv6 TCP 서버 클래스입니다.<br />
	다중 클라이언트 접속을 비동기적으로 처리합니다.
	"""
	def __init__(self, *args, **kwargs):
		"""TlsTcp6Server 클래스의 생성자입니다.

		Args:
			args: 부모 클래스에 전달될 위치 인자입니다.
			kwargs: 부모 클래스에 전달될 키워드 인자입니다.
				- socket_class (Type[TlsTcp6Socket]): 클라이언트 연결 시 생성할 소켓 클래스.
				- idle_timeout (int): 클라이언트 유휴 상태 타임아웃 (초).
		"""
		super().__init__(*args, **kwargs)

		self._socket_class: Type[TlsTcp6Socket] = kwargs.get(TlsTcp6Key.SOCKET_CLASS, TlsTcp6Socket)
		self._idle_timeout: int = kwargs.get(TlsTcp6Key.IDLE_TIMEOUT, TlsTcp6Def.IDLE_TIMEOUT)

		self._clients: Dict[UUID, TlsTcp6Socket] = {}
		self._server_task: Optional[asyncio.Server] = None
		self._packet_handler_task: Optional[Task] = None
		self._reaper_task: Optional[Task] = None

		self.logger.info("서버가 초기화되었습니다.")


	def _init_socket(self):
		"""
		서버 소켓 관련 설정을 초기화합니다.
		"""
		super()._init_socket()
		self._is_server = True


	async def _accept_handler(self, reader: StreamReader, writer: StreamWriter):
		"""
		새로운 클라이언트가 연결되었을 때 호출되는 콜백 메소드입니다.<br />
		클라이언트 소켓 객체를 생성하고 관리 목록에 추가합니다.

		Args:
			reader: 연결된 클라이언트의 StreamReader 객체입니다.
			writer: 연결된 클라이언트의 StreamWriter 객체입니다.
		"""
		peer_info = writer.get_extra_info('peername')
		self.logger.info(f"새로운 클라이언트 연결됨: {peer_info}")

		try:
			client_socket = self._socket_class(
				cert_file=self.cert_file,
				key_file=self.key_file,
				ca_file=self.ca_file,
				host=self.host,
				port=self.port,
				logger_name=TlsTcp6Def.LOGGER_NAME,
				packet_queue=self.packet_queue,
				parser_class=self._parser_class,
				rx_stream=reader,
				tx_stream=writer,
				server=self, # 자기 자신을 서버로 참조
			)

			self._clients[client_socket.uuid] = client_socket
			await client_socket._start_handlers()
			self.logger.info(f"클라이언트 {client_socket.uuid} 핸들러 시작됨. 현재 클라이언트 수: {len(self._clients)}")

		except Exception as e:
			self.logger.error(f"클라이언트 소켓 생성 중 오류 발생: {e}", exc_info=True)
			writer.close()
			await writer.wait_closed()


	async def _packet_handler(self):
		"""메시지 패킷 큐에서 패킷을 꺼내 처리하는 기본 핸들러입니다.<br />
		받은 메시지를 로그로 출력하고 클라이언트에게 다시 전송합니다(에코).
		"""
		self.logger.info("서버 패킷 핸들러가 시작되었습니다.")
		while True:
			try:
				uuid, packet = await self.packet_queue.get()
				self.logger.info(f"패킷 수신됨 [from: {uuid}]: {packet}")

				# 에코 기능: 해당 클라이언트로 다시 전송
				if (uuid in self._clients):
					client_socket = self._clients[uuid]
					# response_data = str(packet).encode('utf-8')
					if (type(packet) is str):
						packet = packet.encode('utf-8')
					await client_socket.send(packet)
					self.logger.info(f"패킷 에코됨 [to: {uuid}]")
				else:
					self.logger.warning(f"패킷을 보낸 클라이언트({uuid})를 찾을 수 없습니다.")

				self.packet_queue.task_done()
			except asyncio.CancelledError:
				self.logger.info("서버 패킷 핸들러가 취소되었습니다.")
				break
			except Exception as e:
				self.logger.error(f"서버 패킷 핸들러에서 예외 발생: {e}", exc_info=True)
				break


	async def _reaper_handler(self):
		"""일정 시간 이상 데이터 수신이 없는 비활성 클라이언트를 정리하는 핸들러입니다."""
		self.logger.info(f"클라이언트 연결 관리자(Reaper) 시작. 유휴 제한시간: {self._idle_timeout}초")
		while True:
			await asyncio.sleep(self._idle_timeout)
			try:
				now = time()
				# To avoid "dictionary changed size during iteration"
				idle_clients = [
					client for client in self._clients.values()
					if (now - client._last_received_time) > self._idle_timeout
				]

				for client in idle_clients:
					self.logger.warning(f"클라이언트 {client.uuid}가 {self._idle_timeout}초 이상 비활성 상태이므로 연결을 종료합니다.")
					await client.close()

			except asyncio.CancelledError:
				self.logger.info("클라이언트 연결 관리자가 취소되었습니다.")
				break
			except Exception as e:
				self.logger.error(f"클라이언트 연결 관리자에서 예외 발생: {e}", exc_info=True)


	def remove_client(self, uuid: UUID):
		"""클라이언트 관리 목록에서 특정 클라이언트를 제거합니다.

		Args:
			uuid: 제거할 클라이언트의 UUID입니다.
		"""
		if uuid in self._clients:
			del self._clients[uuid]
			self.logger.info(f"클라이언트 {uuid}가 목록에서 제거되었습니다. 현재 클라이언트 수: {len(self._clients)}")


	async def start(self):
		"""서버를 시작합니다."""
		ssl_context = self._create_ssl_context()
		self._server_task = await asyncio.start_server(
			self._accept_handler,
			self.host,
			self.port,
			ssl=ssl_context,
			family=socket.AF_INET6
		)

		addr = self._server_task.sockets[0].getsockname()
		self.logger.info(f"서버가 [{addr[0]}]:{addr[1]} 에서 실행 중입니다...")

		self._packet_handler_task = asyncio.create_task(self._packet_handler())
		self._reaper_task = asyncio.create_task(self._reaper_handler())

		try:
			await self._server_task.serve_forever()
		except asyncio.CancelledError:
			self.logger.warning(f"서버가 취소되었습니다.")


	async def stop(self):
		"""서버를 중지하고 모든 리소스를 정리합니다."""
		self.logger.info("서버 종료를 시작합니다.")

		# 모든 클라이언트 연결 종료
		for client in list(self._clients.values()):
			await client.close()
		self._clients.clear()

		# 내부 태스크 종료
		if self._packet_handler_task: self._packet_handler_task.cancel()
		if self._reaper_task: self._reaper_task.cancel()

		if self._server_task:
			self._server_task.close()
			await self._server_task.wait_closed()

		self.logger.info("서버가 완전히 종료되었습니다.")




class TlsTcp6Client(TlsTcp6Socket):
	"""TLS 기반 IPv6 TCP 클라이언트 클래스입니다."""
	def __init__(self, *args, **kwargs):
		"""
		TlsTcp6Client 클래스의 생성자입니다.

		Args:
			args: 부모 클래스에 전달될 위치 인자입니다.
			kwargs: 부모 클래스에 전달될 키워드 인자입니다.
				- check_hostname (bool): 서버 호스트 이름 검증 여부.
		"""
		super().__init__(*args, **kwargs)

		self.check_hostname: bool = kwargs.get('check_hostname', True)
		self._packet_handler_task: Optional[Task] = None
		self.logger.info("클라이언트가 초기화되었습니다.")


	def _init_socket(self):
		"""클라이언트 소켓 관련 설정을 초기화합니다."""
		super()._init_socket()
		self._is_server = False


	# async def _packet_handler(self):
	# 	"""메시지 패킷 큐에서 패킷을 꺼내 처리하는 기본 핸들러입니다.<br />
	# 	받은 메시지를 로그로 출력합니다.
	# 	"""
	# 	self.logger.info("클라이언트 패킷 핸들러가 시작되었습니다.")
	# 	while not self._is_closing:
	# 		try:
	# 			uuid, packet = await self.packet_queue.get()
	# 			self.logger.info(f"서버로부터 메시지 수신: {packet}")
	# 			self.packet_queue.task_done()
	# 		except asyncio.CancelledError:
	# 			self.logger.info("클라이언트 패킷 핸들러가 취소되었습니다.")
	# 			break
	# 		except Exception as e:
	# 			self.logger.error(f"클라이언트 패킷 핸들러에서 예외 발생: {e}", exc_info=True)
	# 			break


	async def start(self):
		"""서버에 연결하고 통신을 시작합니다."""
		ssl_context = self._create_ssl_context()
		ssl_context.check_hostname = self.check_hostname

		try:
			self.logger.info(f"서버 [{self.host}]:{self.port} 에 연결을 시도합니다...")
			self._rx_stream, self._tx_stream = await asyncio.open_connection(
				self.host, self.port, ssl=ssl_context, family=socket.AF_INET6
			)
			self.logger.info("서버에 성공적으로 연결되었습니다.")

			# 핸들러 시작
			await self._start_handlers()
			# self._packet_handler_task = asyncio.create_task(self._packet_handler())
			# self._tasks.add(self._packet_handler_task)

		except ConnectionRefusedError:
			self.logger.error("연결이 거부되었습니다. 서버가 실행 중인지 확인하세요.")
			await self.close()
		except ssl.SSLError as e:
			self.logger.error(f"SSL 오류 발생: {e}. 인증서가 올바른지 확인하세요.")
			await self.close()
		except Exception as e:
			self.logger.error(f"연결 중 예외 발생: {e}", exc_info=True)
			await self.close()
