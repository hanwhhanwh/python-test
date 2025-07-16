# BaseParser 클래스 모듈
# date : 2025-07-02
# author: hbesthee@naver.com
#-*- coding: utf-8 -*-
# use tab char size: 4

# Original Packages
from abc import ABC
from asyncio import Queue, Task
from logging import getLogger
from typing import Any, Optional
from uuid import UUID

import asyncio




class BaseParser(ABC):
	"""바이트 데이터를 메시지 패킷으로 파싱하는 기본 클래스"""

	def __init__(self, parser_uuid: UUID
				, data_queue: Queue[bytes]
				, packet_queue: Queue[Any]
				, logger_name:str='base_parser'):
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
