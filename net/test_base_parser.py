# -*- coding: utf-8 -*-
# PyTest : BaseParser
# made : hbesthee@naver.com
# date : 2025-07-03

# Original Packages
from asyncio import Queue
from typing import Any

import asyncio



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
from lib.tls_tcp6 import BaseParser




class TestBaseParser:
	"""
	BaseParser 클래스의 다양한 동작을 검증하는 테스트 스위트입니다.
	"""

	@pytest_asyncio.fixture
	async def setup_parser(self):
		"""
		각 테스트마다 BaseParser 인스턴스와 큐를 설정하고 정리합니다.
		"""
		data_queue = Queue()
		packet_queue = Queue()
		parser = BaseParser(data_queue, packet_queue)
		parser.start()
		yield data_queue, packet_queue, parser
		# 테스트 후 정리
		await parser.stop()
		# 큐 비우기 (선택 사항, 그러나 다른 테스트에 영향 줄 수 있으므로 권장)
		while not data_queue.empty():
			await data_queue.get()
		while not packet_queue.empty():
			await packet_queue.get()

	@pytest.mark.asyncio
	async def test_01_parser_initialization(self, setup_parser):
		"""
		01. BaseParser가 성공적으로 초기화되는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		assert isinstance(parser, BaseParser)
		assert parser.data_queue is data_queue
		assert parser.packet_queue is packet_queue
		assert parser._parse_task is not None
		assert not parser._parse_task.done()

	@pytest.mark.asyncio
	async def test_02_parser_basic_data_processing(self, setup_parser):
		"""
		02. 단일 bytes 데이터를 문자열로 성공적으로 파싱하는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		test_data = b"Hello World"
		await data_queue.put(test_data)
		await data_queue.join()
		processed_message = await packet_queue.get()
		assert processed_message == "Hello World"
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_03_parser_multiple_data_chunks(self, setup_parser):
		"""
		03. 여러 개의 bytes 데이터 청크를 순서대로 파싱하는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		data_chunks = [b"First", b"Second", b"Third"]
		for chunk in data_chunks:
			await data_queue.put(chunk)
		await data_queue.join()

		for expected_msg in ["First", "Second", "Third"]:
			msg = await packet_queue.get()
			assert msg == expected_msg
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_04_parser_empty_data(self, setup_parser):
		"""
		04. 빈 bytes 데이터가 들어왔을 때 아무런 메시지도 생성하지 않는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		await data_queue.put(b"")
		await data_queue.join()
		await asyncio.sleep(0.1) # 파싱 작업이 완료될 시간 주기
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_05_parser_non_utf8_data(self, setup_parser):
		"""
		05. UTF-8로 디코딩할 수 없는 bytes 데이터가 들어왔을 때 예외 처리 및 로깅을 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		invalid_data = b"\xfa\xfa\xfa" # 유효하지 않은 UTF-8 바이트 시퀀스

		# # 로깅을 캡처하기 위해 mocker 사용 가능 (pytest-mock)
		# # 여기서는 단순히 예외가 발생하지 않고 처리가 진행되는지 확인
		# with pytest.raises(asyncio.TimeoutError): # 큐에 들어가지 않으므로 Timeout 발생 예상
		# 	await data_queue.put(invalid_data)
		# 	await data_queue.join()
		# 	await asyncio.wait_for(packet_queue.get(), timeout=0.1) # 메시지가 없음을 확인

		await data_queue.put(invalid_data)
		await data_queue.join() # 파서가 디코딩을 시도하고 예외 처리할 때까지 기다림
		await asyncio.sleep(0.1) # 로깅이 일어날 시간을 줍니다.
		# BaseParser는 UnicodeDecodeError를 로깅하고 메시지를 큐에 넣지 않습니다.
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_06_parser_stop_method(self, setup_parser):
		"""
		06. stop() 메서드를 호출했을 때 파싱 Task가 성공적으로 종료되는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		await parser.stop()
		await asyncio.sleep(0.1) # 종료 작업이 완료될 시간 주기
		assert parser._parse_task.done()

	@pytest.mark.asyncio
	async def test_07_parser_stop_after_some_data(self, setup_parser):
		"""
		07. 데이터 처리 중 stop()을 호출했을 때 진행 중이던 작업이 완료되고 종료되는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		await data_queue.put(b"Data before stop")
		await asyncio.sleep(0.05) # 데이터가 처리될 시간 주기
		await parser.stop()
		await asyncio.sleep(0.1)
		assert parser._parse_task.done()
		# "Data before stop"은 처리되어야 함
		processed_message = await packet_queue.get()
		assert processed_message == "Data before stop"
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_08_parser_data_after_stop(self, setup_parser):
		"""
		08. stop() 호출 후 데이터가 들어왔을 때 더 이상 처리되지 않는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		await parser.stop()
		await asyncio.sleep(0.1) # 종료 작업 완료 대기
		await data_queue.put(b"Data after stop")
		await asyncio.sleep(0.1) # 데이터 처리 시도 시간 주기
		assert packet_queue.empty() # 아무것도 큐에 추가되지 않아야 함

	@pytest.mark.asyncio
	async def test_09_parser_restarting_after_stop(self, setup_parser):
		"""
		09. stop() 후 다시 start()를 호출했을 때 파서가 재시작되는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		await parser.stop()
		await asyncio.sleep(0.1)
		assert parser._parse_task.done()

		parser.start()
		await asyncio.sleep(0.1)
		assert parser._parse_task is not None
		assert not parser._parse_task.done()

		test_data = b"Restarted Data"
		await data_queue.put(test_data)
		await data_queue.join()
		processed_message = await packet_queue.get()
		assert processed_message == "Restarted Data"
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_10_parser_queue_fullness(self, setup_parser):
		"""
		10. data_queue가 가득 찼을 때 put 동작이 블로킹되는지 (실제로는 무한대 큐이므로 아님)
		혹은 매우 큰 데이터를 처리할 때 문제가 없는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		# asyncio.Queue는 기본적으로 무한대 큐이므로 가득 차는 경우는 없습니다.
		# 대량의 데이터를 넣어 성능이나 메모리 문제가 없는지 간접적으로 테스트
		large_data = b"A" * (1024 * 1024) # 1MB
		await data_queue.put(large_data)
		await data_queue.join()
		processed_message = await packet_queue.get()
		assert processed_message == large_data.decode('utf-8')
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_11_parser_concurrent_put_get(self, setup_parser):
		"""
		11. 동시에 data_queue에 put하고 packet_queue에서 get할 때 데이터 무결성을 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		num_messages = 100
		expected_messages = [f"Message {i}" for i in range(num_messages)]

		async def producer():
			for msg in expected_messages:
				await data_queue.put(msg.encode('utf-8'))
			await data_queue.join()

		async def consumer():
			received_messages = []
			for _ in range(num_messages):
				received_messages.append(await packet_queue.get())
			return received_messages

		prod_task = asyncio.create_task(producer())
		cons_task = asyncio.create_task(consumer())

		await asyncio.gather(prod_task, cons_task)
		received = cons_task.result()
		# 순서는 보장되지 않으므로 정렬 후 비교
		assert sorted(received) == sorted(expected_messages)

	@pytest.mark.asyncio
	async def test_12_parser_none_data_terminates_parser(self, setup_parser):
		"""
		12. data_queue에 None이 들어왔을 때 파서가 종료되는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		await data_queue.put(None)
		await asyncio.sleep(0.1) # 파서가 None을 처리하고 종료될 시간
		assert parser._parse_task.done()

	@pytest.mark.asyncio
	async def test_13_parser_multiple_none_signals(self, setup_parser):
		"""
		13. data_queue에 여러 개의 None이 들어왔을 때도 한 번만 파서가 종료되는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		await data_queue.put(None)
		await data_queue.put(None) # 두 번째 None
		await asyncio.sleep(0.1)
		assert parser._parse_task.done() # 첫 번째 None으로 종료되어야 함

	@pytest.mark.asyncio
	async def test_14_parser_start_idempotency(self, setup_parser):
		"""
		14. start() 메서드를 여러 번 호출했을 때 중복 Task가 생성되지 않고 한 번만 실행되는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		first_task = parser._parse_task
		parser.start() # 다시 start 호출
		await asyncio.sleep(0.05)
		second_task = parser._parse_task
		assert first_task is second_task # 동일한 Task 인스턴스여야 함
		assert not first_task.done()

	@pytest.mark.asyncio
	async def test_15_parser_parse_method_direct_call(self):
		"""
		15. parse() 메서드를 직접 호출했을 때 (Task 생성 없이) 어떻게 동작하는지 확인합니다.
		"""
		# fixture의 setup_parser는 이미 start()를 호출했으므로, 새로운 인스턴스로 테스트
		data_queue = Queue()
		packet_queue = Queue()
		parser = BaseParser(data_queue, packet_queue)

		test_data = b"Direct Call"
		await data_queue.put(test_data)
		await data_queue.put(None) # 종료 신호

		# parse_handler() 코루틴을 직접 실행 (Task 없이)
		parser._running = True
		await parser.parse_handler()

		processed_message = await packet_queue.get()
		assert processed_message == "Direct Call"
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_16_parser_custom_parser_behavior(self):
		"""
		16. BaseParser를 상속받아 재정의된 parse 메서드가 올바르게 작동하는지 확인합니다.
			(이 테스트를 위해 BaseParser와 동일한 파일에 CustomParser 정의 필요)
		"""
		class TestCustomParser(BaseParser):
			def parse(self) -> Any:
				data = self._buf.decode('utf-8', errors='ignore')[::-1]
				self._buf = b"" # 버퍼 초기화
				return data

		data_queue = Queue()
		packet_queue = Queue()
		custom_parser = TestCustomParser(data_queue, packet_queue)
		custom_parser.start()

		test_data = b"Python"
		await data_queue.put(test_data)
		await data_queue.join()

		processed_message = await packet_queue.get()
		assert processed_message == "nohtyP" # 역순 확인
		assert packet_queue.empty()
		await custom_parser.stop()

	@pytest.mark.asyncio
	async def test_17_parser_queue_join_after_stop(self, setup_parser):
		"""
		17. stop() 호출 후 data_queue.join()이 어떻게 동작하는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		await data_queue.put(b"test1")
		await data_queue.put(b"test2")
		await asyncio.sleep(0.0000001)
		await parser.stop() # 파서 종료 신호 전송
		await data_queue.join() # 이 시점에 남아있는 data_queue 작업은 완료되어야 함

		# 파서가 종료되었으므로 더 이상 packet_queue에 메시지가 추가되지 않아야 함
		# 하지만 이미 put된 'test1', 'test2'는 처리되어야 합니다.
		messages = []
		messages.append(await packet_queue.get())
		packet_queue.task_done()
		messages.append(await packet_queue.get())
		packet_queue.task_done()
		await packet_queue.join() # 이 시점에 남아있는 packet_queue 작업은 완료되어야 함
		assert sorted(messages) == sorted(["test1", "test2"])
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_18_parser_empty_queues_after_stop(self, setup_parser):
		"""
		18. 파서 종료 후 큐가 완전히 비워지는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		await parser.stop()
		await asyncio.sleep(0.1) # 종료 작업 완료 대기

		assert data_queue.empty()
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_19_parser_task_cancellation_during_parse(self, setup_parser):
		"""
		19. parse Task가 외부에서 취소되었을 때 올바르게 종료되는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		parser_task = parser._parse_task

		await data_queue.put(b"Data that might be partially processed")
		await asyncio.sleep(0.01) # 잠시 대기

		parser_task.cancel()
		with pytest.raises(asyncio.CancelledError):
			await parser_task # 취소된 태스크가 완료될 때까지 대기

		# 이전에 put된 데이터는 처리되었을 수 있지만, 이후 데이터는 처리되면 안 됩니다.
		# 정확한 상태를 위해 큐에 들어간 데이터가 있다면 모두 소비
		while (not packet_queue.empty()):
			await packet_queue.get()
			packet_queue.task_done()

		# 태스크가 취소되었으므로 더 이상 데이터가 처리되지 않아야 함
		await data_queue.put(b"Data after cancellation")
		await asyncio.sleep(0.1)
		assert packet_queue.empty() or packet_queue.qsize() == 0 # 이미 처리된 데이터는 있을 수 있지만, 이후 데이터는 처리되면 안됨


	@pytest.mark.asyncio
	async def test_20_high_volume_small_messages(self, setup_parser):
		"""
		20. 많은 수의 작은 메시지를 처리할 때 파서의 성능과 큐 안정성을 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		num_messages = 1000
		expected_messages = [f"msg_{i}" for i in range(num_messages)]

		for msg in expected_messages:
			await data_queue.put(msg.encode('utf-8'))
		await data_queue.join()

		received_messages = []
		for _ in range(num_messages):
			received_messages.append(await packet_queue.get())

		assert len(received_messages) == num_messages
		assert sorted(received_messages) == sorted(expected_messages)
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_21_very_long_single_message(self, setup_parser):
		"""
		21. 매우 긴 단일 메시지를 처리할 때 파서의 메모리 및 처리 능력을 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		long_message = "A" * (1024 * 100) # 100KB 메시지
		await data_queue.put(long_message.encode('utf-8'))
		await data_queue.join()

		processed_message = await packet_queue.get()
		assert processed_message == long_message
		assert packet_queue.empty()

	@pytest.mark.asyncio
	# async def test_22_fragmented_messages_and_incomplete_line(self, setup_parser):
	async def test_22_fragmented_messages_and_incomplete_line(self):
		"""
		22. 논리적인 메시지가 여러 개의 bytes 청크로 나뉘어 들어오거나,
			불완전한 메시지 부분이 들어왔을 때 파서의 동작을 확인합니다.
			BaseParser는 무조건 에코가 되므로, '\n' 문자로 메시지 패킷을 생성하도록 새로운 파서를 정의하여 시험합니다. 
		"""
		class TestCustomParser(BaseParser):
			def parse(self) -> Any:
				lf_pos = self._buf.find(b'\n')
				if (lf_pos < 0):
					return None
				data = self._buf[:lf_pos].decode('utf-8', errors='ignore')
				self._buf = self._buf[lf_pos + 1:]
				self._buf = b"" # 버퍼 초기화
				return data

		data_queue = Queue()
		packet_queue = Queue()
		parser = TestCustomParser(data_queue, packet_queue)
		parser.start()

		# "Hello" -> " World!"
		await data_queue.put(b"Hello")
		await asyncio.sleep(0.01) # 파싱 시간 부여
		assert packet_queue.empty() # 아직 완전한 메시지가 아님

		await data_queue.put(b" World!\n")
		await data_queue.join()

		# TestCustomParser는 줄바꿈 기준으로 파싱하므로, "Hello World!" 전체가 하나의 메시지로 파싱됨
		processed_message = await packet_queue.get()
		assert processed_message == "Hello World!"
		assert packet_queue.empty()

		# 다른 예시: 메시지 중간에 끊김
		await data_queue.put(b"Part1")
		await asyncio.sleep(0.01)
		await data_queue.put(b"Part2\n")
		await data_queue.join()
		processed_message = await packet_queue.get()
		assert processed_message == "Part1Part2"
		assert packet_queue.empty()
		await parser.stop()

	@pytest.mark.asyncio
	async def test_23_mixed_valid_and_invalid_data(self):
		"""
		23. 유효한 데이터와 유효하지 않은 (non-UTF8) 데이터가 혼합되어 들어왔을 때 파서의 강건성을 확인합니다.
		"""
		class TestCustomParser(BaseParser):
			def parse(self) -> Any:
				lf_pos = self._buf.find(b'\n')
				if (lf_pos < 0):
					return None
				try:
					data = self._buf[:lf_pos].decode('utf-8')
				except UnicodeDecodeError:
					data = None
					self.logger.error(f"수신된 bytes 데이터를 UTF-8로 디코딩 실패: {self._buf[:lf_pos]!r}")
				self._buf = self._buf[lf_pos + 1:]
				self._buf = b"" # 버퍼 초기화
				return data

		data_queue = Queue()
		packet_queue = Queue()
		parser = TestCustomParser(data_queue, packet_queue)
		parser.start()

		valid_data1 = b"Valid Message One"
		invalid_data = b"Invalid\xfaBytes"
		valid_data2 = b"Valid Message Two"

		await data_queue.put(valid_data1)
		await data_queue.put(b'\n')
		await data_queue.put(invalid_data)
		await data_queue.put(b'\n')
		await data_queue.put(valid_data2)
		await data_queue.put(b'\n')
		await data_queue.join()

		msg1 = await packet_queue.get()
		assert msg1 == valid_data1.decode('utf-8')
		msg2 = await packet_queue.get()
		assert msg2 == valid_data2.decode('utf-8')

		assert packet_queue.empty() # 유효하지 않은 데이터는 파싱되지 않아야 함
		await parser.stop()

	@pytest.mark.asyncio
	async def test_24_rapid_start_stop_cycles(self, setup_parser):
		"""
		24. 파서를 빠르게 시작하고 중지하는 사이클을 반복하여 리소스 관리 및 안정성을 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser # 초기 parser는 stop()되지 않은 상태
		await parser.stop() # fixture에서 시작되었으므로 먼저 중지

		for i in range(5):
			parser.start()
			await asyncio.sleep(0.01) # 잠시 실행
			await data_queue.put(f"Cycle {i} Message".encode('utf-8'))
			await data_queue.join() # 메시지 처리 대기
			msg = await packet_queue.get()
			assert msg == f"Cycle {i} Message"
			assert packet_queue.empty()
			await parser.stop()
			await asyncio.sleep(0.01) # 중지 완료 대기
			assert parser._parse_task.done()

		assert data_queue.empty()
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_25_messages_with_whitespace_and_empty_lines(self, setup_parser):
		"""
		25. 선행/후행 공백이 있는 메시지와 빈 줄이 들어왔을 때 (`strip()` 없이) 어떻게 처리되는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser

		await data_queue.put(b"  leading_space ")
		await data_queue.put(b"trailing_space  ")
		await data_queue.put(b"  both_spaces  ")
		await data_queue.put(b"") # 빈 데이터 -> BaseParser에서는 제거됨
		await data_queue.put(b"\n") # 줄바꿈 문자 -> 디코딩 시 '\n'

		await data_queue.join()

		# BaseParser는 decode만 하므로, 공백과 줄바꿈은 그대로 유지됩니다.
		assert await packet_queue.get() == "  leading_space "
		assert await packet_queue.get() == "trailing_space  "
		assert await packet_queue.get() == "  both_spaces  "
		# BaseParser의 parse()는 `message = data.decode('utf-8')` 이후 별도 처리가 없으므로,
		# 빈 바이트열은 빈 문자열로, '\n'은 '\n'으로 들어갑니다.
		# 기존 test_04와 test_05에서 empty()를 사용했는데, 이는 test_25의 의도와 다소 다릅니다.
		# BaseParser의 `parse` 메서드 내부에서 `packet_queue.put(message)` 호출 시
		# `message`가 `\n`일 수 있음을 확인합니다.
		assert await packet_queue.get() == "\n"
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_26_messages_containing_special_utf8_characters(self, setup_parser):
		"""
		26. 다양한 특수 UTF-8 문자가 포함된 메시지의 인코딩/디코딩 무결성을 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		special_messages = [
			"안녕하세요, 세계!", # 한글
			"你好, 世界!", # 중국어
			"こんにちは、世界！", # 일본어
			"😂👍✨", # 이모지
			"Müßiggang ist aller Laster Anfang.", # 독일어 움라우트
			"€£¥₩", # 통화 기호
			"~!@#$%^&*()_+`-={}[]|\\:;\"'<>,.?/" # 특수 문자
		]

		for msg in special_messages:
			await data_queue.put(msg.encode('utf-8'))
		await data_queue.join()

		received_messages = []
		for _ in range(len(special_messages)):
			received_messages.append(await packet_queue.get())

		assert received_messages == special_messages
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_27_parser_idling_gracefully(self, setup_parser):
		"""
		27. data_queue에 데이터가 없을 때 파서가 불필요한 리소스 소비 없이 유휴 상태를 유지하는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		await asyncio.sleep(0.5) # 파서가 시작된 후 잠시 대기
		assert data_queue.empty()
		assert packet_queue.empty()
		assert not parser._parse_task.done()

		await data_queue.put(b"After Idle")
		await data_queue.join()
		assert await packet_queue.get() == "After Idle"

	@pytest.mark.asyncio
	async def test_28_immediate_stop_after_start_with_no_data(self, setup_parser):
		"""
		28. 데이터를 넣지 않고 시작하자마자 바로 `stop()`을 호출했을 때 파서가 깨끗하게 종료되는지 확인합니다.
		"""
		data_queue, packet_queue, parser = setup_parser
		await parser.stop()
		await asyncio.sleep(0.01) # 종료 완료 대기
		assert parser._parse_task.done()
		assert data_queue.empty()
		assert packet_queue.empty()

	@pytest.mark.asyncio
	async def test_29_error_handling_in_custom_parser(self):
		"""
		29. BaseParser를 상속받은 커스텀 파서의 `parse_handler` 메서드에서
			예상치 못한 일반 예외가 발생했을 때 BaseParser의 Task가 어떻게 종료되는지 확인합니다.
		"""
		class CrashingParser(BaseParser):
			def __init__(self, data_queue: Queue[bytes], packet_queue: Queue[str], crash_after: int = 1) -> None:
				super().__init__(data_queue, packet_queue)
				self._processed_count = 0
				self._crash_after = crash_after

			async def parse_handler(self) -> None:
				try:
					while True:
						data = await self.data_queue.get()
						if data is None:
							break
						try:
							self._processed_count += 1
							if self._processed_count >= self._crash_after:
								raise ValueError("Simulated crash in custom parser")
							await self.packet_queue.put(data.decode('utf-8'))
						finally:
							self.data_queue.task_done() # 예외가 발생하더라도 모든 큐는 정상적으로 처리되어야 합니다.
							pass
				except Exception as e:
					# BaseParser의 parse_handler는 Exception을 로깅하고 task가 done으로 변경되지만,
					# CrashingParser의 parse_handler는 catch하지 않으므로 exception이 전파되어 task가 실패합니다.
					# BaseParser.parse_handler()는 Exception을 catch합니다.
					# 따라서 이 테스트는 BaseParser의 Exception 처리 로직을 따릅니다.
					raise # 이 예외를 그대로 전달

		data_queue = Queue()
		packet_queue = Queue()
		crashing_parser = CrashingParser(data_queue, packet_queue, crash_after=1) # 첫 메시지 후 크래시
		crashing_parser.start()

		await data_queue.put(b"Message 1 (should cause crash)")
		await asyncio.sleep(0.1) # 메시지 처리 및 크래시 발생 대기

		# BaseParser의 parse_handler는()는 Exception을 catch하고 로깅합니다.
		# 따라서 task는 done 상태가 되지만, 'result()'에서 예외가 발생하지는 않습니다.
		# 다만, 코루틴 내부에서 예외가 발생하면 태스크는 완료된 것으로 표시되고,
		# exception() 메서드를 통해 예외를 확인할 수 있습니다.
		await data_queue.join() # 예외가 발생하더라도 모든 큐는 정상적으로 처리되어야 합니다.
		assert crashing_parser._parse_task.done()
		assert crashing_parser._parse_task.exception() is not None
		assert isinstance(crashing_parser._parse_task.exception(), ValueError)

		# 첫 번째 메시지는 큐에 들어가지 않아야 합니다 (크래시로 인해)
		assert packet_queue.empty()
		assert data_queue.empty() # data_queue.get()에서 처리되었으므로

		await crashing_parser.stop()



# 이 스크립트를 직접 실행하면 pytest를 통해 테스트를 실행합니다.
if (__name__ == "__main__"):
	pytest.main( [ __file__, "-v"] )
