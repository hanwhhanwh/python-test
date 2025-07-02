# -*- coding: utf-8 -*-
# IPv6 TLS TCP communication Framework
# made : hbesthee@naver.com
# date : 2025-07-02
# 기본 출처 : PyKakao.Message

import asyncio
import ssl
import socket
import logging
import uuid
from typing import Dict, Optional, Callable, Any
from asyncio import Queue, StreamReader, StreamWriter
from pathlib import Path


class TlsTcp6Socket:
	"""IPv6 TLS TCP 통신을 위한 최상위 부모 클래스"""

	def __init__(self, logger_name: str = "tls_tcp6"):
		"""
		TlsTcp6Socket 초기화

		Args:
			logger_name (str): 로거 이름 (기본값: "tls_tcp6")
		"""
		self.logger = logging.getLogger(logger_name)
		self.ssl_context = None
		self.receive_queue = Queue()
		self.send_queue = Queue()
		self.is_running = False

	def create_ssl_context(self, cert_file: str, key_file: str, ca_file: str,
						is_server: bool = True) -> ssl.SSLContext:
		"""
		SSL 컨텍스트를 생성하는 메소드

		Args:
			cert_file (str): 인증서 파일 경로
			key_file (str): 개인키 파일 경로
			ca_file (str): CA 인증서 파일 경로
			is_server (bool): 서버 모드 여부 (기본값: True)

		Returns:
			ssl.SSLContext: 생성된 SSL 컨텍스트
		"""
		if is_server:
			context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
			context.minimum_version = ssl.TLSVersion.TLSv1_3
		else:
			context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
			context.minimum_version = ssl.TLSVersion.TLSv1_3

		# 인증서 및 개인키 로드
		context.load_cert_chain(cert_file, key_file)

		# CA 인증서 로드
		context.load_verify_locations(ca_file)

		# 상호 인증 설정
		context.verify_mode = ssl.CERT_REQUIRED

		self.ssl_context = context
		self.logger.info(f"SSL 컨텍스트 생성 완료 (서버 모드: {is_server})")

		return context

	def _process_received_data(self, data: bytes) -> bytes:
		"""
		수신 데이터 후처리 메소드 (하위 클래스에서 재정의 가능)

		Args:
			data (bytes): 수신된 원본 데이터

		Returns:
			bytes: 후처리된 데이터
		"""
		return data

	async def _handle_receive(self, reader: StreamReader):
		"""
		데이터 수신 처리 메소드

		Args:
			reader (StreamReader): 스트림 리더 객체
		"""
		while self.is_running:
			try:
				data = await reader.read(4096)
				if not data:
					break

				# 수신 데이터 후처리
				processed_data = self._process_received_data(data)

				# 수신 큐에 데이터 추가
				await self.receive_queue.put(processed_data)

				self.logger.debug(f"데이터 수신: {len(data)} 바이트")

			except Exception as e:
				self.logger.error(f"데이터 수신 중 오류 발생: {e}")
				break

	async def _handle_send(self, writer: StreamWriter):
		"""
		데이터 송신 처리 메소드

		Args:
			writer (StreamWriter): 스트림 라이터 객체
		"""
		while self.is_running:
			try:
				# 송신 큐에서 데이터 가져오기
				data = await self.send_queue.get()

				writer.write(data)
				await writer.drain()

				self.logger.debug(f"데이터 송신: {len(data)} 바이트")

			except Exception as e:
				self.logger.error(f"데이터 송신 중 오류 발생: {e}")
				break

	async def send_data(self, data: bytes):
		"""
		외부에서 호출하는 데이터 송신 메소드

		Args:
			data (bytes): 송신할 데이터
		"""
		await self.send_queue.put(data)

	def stop(self):
		"""연결 종료 메소드"""
		self.is_running = False
		self.logger.info("연결 종료")


class TlsTcp6Server(TlsTcp6Socket):
	"""IPv6 TLS TCP 서버 클래스"""

	def __init__(self, host: str = "::", port: int = 8443, logger_name: str = "tls_tcp6"):
		"""
		TlsTcp6Server 초기화

		Args:
			host (str): 서버 호스트 주소 (기본값: "::")
			port (int): 서버 포트 번호 (기본값: 8443)
			logger_name (str): 로거 이름 (기본값: "tls_tcp6")
		"""
		super().__init__(logger_name)
		self.host = host
		self.port = port
		self.clients: Dict[str, Dict[str, Any]] = {}
		self.server = None

	async def _handle_client(self, reader: StreamReader, writer: StreamWriter):
		"""
		클라이언트 연결 처리 메소드

		Args:
			reader (StreamReader): 클라이언트 스트림 리더
			writer (StreamWriter): 클라이언트 스트림 라이터
		"""
		client_id = str(uuid.uuid4())
		client_addr = writer.get_extra_info('peername')

		self.clients[client_id] = {
			'reader': reader,
			'writer': writer,
			'address': client_addr,
			'receive_queue': Queue(),
			'send_queue': Queue()
		}

		self.logger.info(f"클라이언트 연결: {client_addr} (ID: {client_id})")

		try:
			# 클라이언트별 송수신 태스크 생성
			receive_task = asyncio.create_task(
				self._handle_client_receive(client_id, reader)
			)
			send_task = asyncio.create_task(
				self._handle_client_send(client_id, writer)
			)

			# 태스크 완료 대기
			await asyncio.gather(receive_task, send_task, return_exceptions=True)

		except Exception as e:
			self.logger.error(f"클라이언트 처리 중 오류 발생: {e}")
		finally:
			# 클라이언트 정리
			await self._cleanup_client(client_id)

	async def _handle_client_receive(self, client_id: str, reader: StreamReader):
		"""
		클라이언트 데이터 수신 처리

		Args:
			client_id (str): 클라이언트 ID
			reader (StreamReader): 스트림 리더 객체
		"""
		while self.is_running and client_id in self.clients:
			try:
				data = await reader.read(4096)
				if not data:
					break

				# 수신 데이터 후처리
				processed_data = self._process_received_data(data)

				# 클라이언트별 수신 큐에 데이터 추가
				await self.clients[client_id]['receive_queue'].put(processed_data)

				self.logger.debug(f"클라이언트 {client_id} 데이터 수신: {len(data)} 바이트")

			except Exception as e:
				self.logger.error(f"클라이언트 {client_id} 수신 중 오류: {e}")
				break

	async def _handle_client_send(self, client_id: str, writer: StreamWriter):
		"""
		클라이언트 데이터 송신 처리

		Args:
			client_id (str): 클라이언트 ID
			writer (StreamWriter): 스트림 라이터 객체
		"""
		while self.is_running and client_id in self.clients:
			try:
				# 클라이언트별 송신 큐에서 데이터 가져오기
				data = await self.clients[client_id]['send_queue'].get()

				writer.write(data)
				await writer.drain()

				self.logger.debug(f"클라이언트 {client_id} 데이터 송신: {len(data)} 바이트")

			except Exception as e:
				self.logger.error(f"클라이언트 {client_id} 송신 중 오류: {e}")
				break

	async def _cleanup_client(self, client_id: str):
		"""
		클라이언트 리소스 정리

		Args:
			client_id (str): 정리할 클라이언트 ID
		"""
		if client_id in self.clients:
			client_info = self.clients[client_id]

			try:
				client_info['writer'].close()
				await client_info['writer'].wait_closed()
			except Exception as e:
				self.logger.error(f"클라이언트 {client_id} 연결 종료 중 오류: {e}")

			del self.clients[client_id]
			self.logger.info(f"클라이언트 {client_id} 리소스 정리 완료")

	async def send_to_client(self, client_id: str, data: bytes):
		"""
		특정 클라이언트에게 데이터 송신

		Args:
			client_id (str): 대상 클라이언트 ID
			data (bytes): 송신할 데이터
		"""
		if client_id in self.clients:
			await self.clients[client_id]['send_queue'].put(data)

	async def broadcast(self, data: bytes):
		"""
		모든 클라이언트에게 데이터 브로드캐스트

		Args:
			data (bytes): 브로드캐스트할 데이터
		"""
		for client_id in self.clients:
			await self.send_to_client(client_id, data)

	async def start_server(self, cert_file: str, key_file: str, ca_file: str):
		"""
		서버 시작

		Args:
			cert_file (str): 인증서 파일 경로
			key_file (str): 개인키 파일 경로
			ca_file (str): CA 인증서 파일 경로
		"""
		# SSL 컨텍스트 생성
		self.create_ssl_context(cert_file, key_file, ca_file, is_server=True)

		# 서버 시작
		self.server = await asyncio.start_server(
			self._handle_client,
			self.host,
			self.port,
			family=socket.AF_INET6,
			ssl=self.ssl_context
		)

		self.is_running = True
		self.logger.info(f"서버 시작: [{self.host}]:{self.port}")

		async with self.server:
			await self.server.serve_forever()

	async def stop_server(self):
		"""서버 중지"""
		self.is_running = False

		# 모든 클라이언트 연결 종료
		for client_id in list(self.clients.keys()):
			await self._cleanup_client(client_id)

		# 서버 종료
		if self.server:
			self.server.close()
			await self.server.wait_closed()

		self.logger.info("서버 중지 완료")


class TlsTcp6Client(TlsTcp6Socket):
	"""IPv6 TLS TCP 클라이언트 클래스"""

	def __init__(self, logger_name: str = "tls_tcp6", check_hostname: bool = True):
		"""
		TlsTcp6Client 초기화

		Args:
			logger_name (str): 로거 이름 (기본값: "tls_tcp6")
			check_hostname (bool): 호스트명 검증 여부 (기본값: True)
		"""
		super().__init__(logger_name)
		self.check_hostname = check_hostname
		self.reader = None
		self.writer = None

	async def connect(self, host: str, port: int, cert_file: str, key_file: str, ca_file: str):
		"""
		서버에 연결

		Args:
			host (str): 서버 호스트 주소
			port (int): 서버 포트 번호
			cert_file (str): 클라이언트 인증서 파일 경로
			key_file (str): 클라이언트 개인키 파일 경로
			ca_file (str): CA 인증서 파일 경로
		"""
		# SSL 컨텍스트 생성
		self.create_ssl_context(cert_file, key_file, ca_file, is_server=False)

		# check_hostname 설정 반영
		self.ssl_context.check_hostname = self.check_hostname

		try:
			# 서버 연결
			self.reader, self.writer = await asyncio.open_connection(
				host, port, ssl=self.ssl_context, family=socket.AF_INET6
			)

			self.is_running = True
			self.logger.info(f"서버 연결 성공: [{host}]:{port}")

			# 송수신 태스크 시작
			receive_task = asyncio.create_task(self._handle_receive(self.reader))
			send_task = asyncio.create_task(self._handle_send(self.writer))

			await asyncio.gather(receive_task, send_task, return_exceptions=True)

		except Exception as e:
			self.logger.error(f"서버 연결 실패: {e}")
			raise

	async def disconnect(self):
		"""서버 연결 종료"""
		self.is_running = False

		if self.writer:
			self.writer.close()
			await self.writer.wait_closed()

		self.logger.info("서버 연결 종료")


class BaseParser:
	"""수신 데이터 파싱을 위한 기본 클래스"""

	def __init__(self, receive_queue: Queue, logger_name: str = "tls_tcp6"):
		"""
		BaseParser 초기화

		Args:
			receive_queue (Queue): 수신 데이터 큐
			logger_name (str): 로거 이름 (기본값: "tls_tcp6")
		"""
		self.receive_queue = receive_queue
		self.logger = logging.getLogger(logger_name)
		self.buffer = b""
		self.message_queue = Queue()
		self.is_running = False

	async def start_parsing(self):
		"""파싱 시작"""
		self.is_running = True
		self.logger.info("데이터 파싱 시작")

		while self.is_running:
			try:
				# 수신 큐에서 데이터 가져오기
				data = await self.receive_queue.get()

				# 버퍼에 데이터 추가
				self.buffer += data

				# 메시지 패킷 분석
				await self._parse_buffer()

			except Exception as e:
				self.logger.error(f"데이터 파싱 중 오류: {e}")

	async def _parse_buffer(self):
		"""
		버퍼 데이터를 메시지 패킷으로 분석 (하위 클래스에서 재정의 필요)
		"""
		# 기본 구현: 전체 버퍼를 하나의 메시지로 처리
		if self.buffer:
			await self.message_queue.put(self.buffer)
			self.buffer = b""

	async def get_message(self) -> bytes:
		"""
		파싱된 메시지 패킷 가져오기

		Returns:
			bytes: 파싱된 메시지 패킷
		"""
		return await self.message_queue.get()

	def stop_parsing(self):
		"""파싱 중지"""
		self.is_running = False
		self.logger.info("데이터 파싱 중지")


# 사용 예제
async def server_example():
	"""서버 사용 예제"""
	# 로깅 설정
	logging.basicConfig(level=logging.INFO)

	# 서버 인스턴스 생성
	server = TlsTcp6Server(host="::", port=8443)

	try:
		# 서버 시작
		await server.start_server(
			cert_file="server.crt",
			key_file="server.key",
			ca_file="ca.crt"
		)
	except KeyboardInterrupt:
		print("서버 종료 중...")
	finally:
		await server.stop_server()


async def client_example():
	"""클라이언트 사용 예제"""
	# 로깅 설정
	logging.basicConfig(level=logging.INFO)

	# 클라이언트 인스턴스 생성
	client = TlsTcp6Client(check_hostname=False)

	try:
		# 서버 연결
		await client.connect(
			host="::1",
			port=8443,
			cert_file="client.crt",
			key_file="client.key",
			ca_file="ca.crt"
		)

		# 데이터 송신
		await client.send_data(b"Hello, Server!")

		# 파서 생성 및 시작
		parser = BaseParser(client.receive_queue)
		parser_task = asyncio.create_task(parser.start_parsing())

		# 메시지 수신 대기
		while True:
			try:
				message = await asyncio.wait_for(parser.get_message(), timeout=1.0)
				print(f"수신 메시지: {message}")
			except asyncio.TimeoutError:
				continue
			except KeyboardInterrupt:
				break

		parser.stop_parsing()
		await parser_task

	except Exception as e:
		print(f"클라이언트 오류: {e}")
	finally:
		await client.disconnect()


async def monitor_messages_example():
	"""메시지 모니터링 예제"""
	# 로깅 설정
	logging.basicConfig(level=logging.INFO)

	# 클라이언트 생성
	client = TlsTcp6Client()

	# 파서 생성
	parser = BaseParser(client.receive_queue)

	# 파싱 태스크 시작
	parser_task = asyncio.create_task(parser.start_parsing())

	# 메시지 모니터링 태스크
	async def message_monitor():
		while True:
			try:
				message = await parser.get_message()
				print(f"새 메시지 수신: {message.decode('utf-8', errors='ignore')}")
			except Exception as e:
				print(f"메시지 처리 오류: {e}")
				break

	# 모니터링 시작
	monitor_task = asyncio.create_task(message_monitor())

	try:
		# 서버 연결
		await client.connect(
			host="::1",
			port=8443,
			cert_file="client.crt",
			key_file="client.key",
			ca_file="ca.crt"
		)

		# 모니터링 대기
		await monitor_task

	except KeyboardInterrupt:
		print("모니터링 종료")
	finally:
		parser.stop_parsing()
		await parser_task
		await client.disconnect()


if (__name__ == "__main__"):
	import sys

	if len(sys.argv) > 1:
		if sys.argv[1] == "server":
			asyncio.run(server_example())
		elif sys.argv[1] == "client":
			asyncio.run(client_example())
		elif sys.argv[1] == "monitor":
			asyncio.run(monitor_messages_example())
	else:
		print("사용법: python script.py [server|client|monitor]")