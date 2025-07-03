# -*- coding: utf-8 -*-
# TLS TCP6 서버 예제
# made : whhan@cnuglobal.com
# date : 2025-07-02

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



@pytest_asyncio.fixture
async def setup_parser():
	"""
	각 테스트마다 BaseParser 인스턴스와 큐를 설정합니다.
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
async def test_parser_initialization(setup_parser):
	"""
	1. BaseParser가 성공적으로 초기화되는지 확인합니다.
	"""
	data_queue, packet_queue, parser = setup_parser
	assert isinstance(parser, BaseParser)
	assert parser.data_queue is data_queue
	assert parser.packet_queue is packet_queue
	assert parser._parse_task is not None
	assert not parser._parse_task.done()

@pytest.mark.asyncio
async def test_parser_basic_data_processing(setup_parser):
	"""
	2. 단일 bytes 데이터를 문자열로 성공적으로 파싱하는지 확인합니다.
	"""
	data_queue, packet_queue, parser = setup_parser
	test_data = b"Hello World"
	await data_queue.put(test_data)
	await data_queue.join() # data_queue의 모든 항목이 처리될 때까지 대기
	processed_message = await packet_queue.get()
	assert processed_message == "Hello World"
	assert packet_queue.empty()

@pytest.mark.asyncio
async def test_parser_multiple_data_chunks(setup_parser):
	"""
	3. 여러 개의 bytes 데이터 청크를 순서대로 파싱하는지 확인합니다.
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
async def test_parser_empty_data(setup_parser):
	"""
	4. 빈 bytes 데이터가 들어왔을 때 아무런 메시지도 생성하지 않는지 확인합니다.
	"""
	data_queue, packet_queue, parser = setup_parser
	await data_queue.put(b"")
	await data_queue.join()
	await asyncio.sleep(0.1) # 파싱 작업이 완료될 시간 주기
	assert packet_queue.empty() # 빈 데이터는 기본적으로 메시지로 처리되지 않음 (디코딩 결과가 빈 문자열이므로)

@pytest.mark.asyncio
async def test_parser_non_utf8_data(setup_parser):
	"""
	5. UTF-8로 디코딩할 수 없는 bytes 데이터가 들어왔을 때 예외 처리 및 로깅을 확인합니다.
	"""
	data_queue, packet_queue, parser = setup_parser
	invalid_data = b"\xfa\xfa\xfa" # 유효하지 않은 UTF-8 바이트 시퀀스

	# 로깅을 캡처하기 위해 mocker 사용 가능 (pytest-mock)
	# 여기서는 단순히 예외가 발생하지 않고 처리가 진행되는지 확인
	with pytest.raises(asyncio.TimeoutError): # 큐에 들어가지 않으므로 Timeout 발생 예상
		await data_queue.put(invalid_data)
		await data_queue.join()
		await asyncio.wait_for(packet_queue.get(), timeout=0.1) # 메시지가 없음을 확인

@pytest.mark.asyncio
async def test_parser_stop_method(setup_parser):
	"""
	6. stop() 메서드를 호출했을 때 파싱 Task가 성공적으로 종료되는지 확인합니다.
	"""
	data_queue, packet_queue, parser = setup_parser
	await parser.stop()
	await asyncio.sleep(0.1) # 종료 작업이 완료될 시간 주기
	assert parser._parse_task.done()

@pytest.mark.asyncio
async def test_parser_stop_after_some_data(setup_parser):
	"""
	7. 데이터 처리 중 stop()을 호출했을 때 진행 중이던 작업이 완료되고 종료되는지 확인합니다.
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
async def test_parser_data_after_stop(setup_parser):
	"""
	8. stop() 호출 후 데이터가 들어왔을 때 더 이상 처리되지 않는지 확인합니다.
	"""
	data_queue, packet_queue, parser = setup_parser
	await parser.stop()
	await asyncio.sleep(0.1) # 종료 작업 완료 대기
	await data_queue.put(b"Data after stop")
	await asyncio.sleep(0.1) # 데이터 처리 시도 시간 주기
	assert packet_queue.empty() # 아무것도 큐에 추가되지 않아야 함

@pytest.mark.asyncio
async def test_parser_restarting_after_stop(setup_parser):
	"""
	9. stop() 후 다시 start()를 호출했을 때 파서가 재시작되는지 확인합니다.
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
async def test_parser_queue_fullness(setup_parser):
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
async def test_parser_concurrent_put_get(setup_parser):
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
	assert sorted(received) == sorted(expected_messages) # 순서는 보장되지 않으므로 정렬 후 비교

@pytest.mark.asyncio
async def test_parser_custom_queue_types_not_allowed(setup_parser):
	"""
	12. BaseParser가 asyncio.Queue가 아닌 다른 타입의 큐를 받았을 때 동작을 확인 (타입 힌트 덕분에 IDE 경고는 나오나 런타임에서 막지는 않음)
		이 테스트는 사실상 실패하며, 타입 힌트가 런타임에 제약을 두지 않음을 보여줍니다.
		실제로는 이런 상황을 만들지 않도록 설계해야 합니다.
	"""
	# 이 테스트는 BaseParser의 생성자에 타입 힌트가 있어도 런타임에 강제하지 않음을 보여줍니다.
	# 올바른 큐 타입이 아닐 때 오류를 발생시키는 것은 BaseParser의 역할이 아님.
	# Python의 동적 타이핑 특성 상 런타임에 타입 에러가 바로 발생하지 않을 수 있습니다.
	pass # 이 테스트 케이스는 의미 없으므로 pass

@pytest.mark.asyncio
async def test_parser_none_data_terminates_parser(setup_parser):
	"""
	13. data_queue에 None이 들어왔을 때 파서가 종료되는지 확인합니다.
	"""
	data_queue, packet_queue, parser = setup_parser
	await data_queue.put(None)
	await asyncio.sleep(0.1) # 파서가 None을 처리하고 종료될 시간
	assert parser._parse_task.done()

@pytest.mark.asyncio
async def test_parser_multiple_none_signals(setup_parser):
	"""
	14. data_queue에 여러 개의 None이 들어왔을 때도 한 번만 파서가 종료되는지 확인합니다.
	"""
	data_queue, packet_queue, parser = setup_parser
	await data_queue.put(None)
	await data_queue.put(None) # 두 번째 None
	await asyncio.sleep(0.1)
	assert parser._parse_task.done() # 첫 번째 None으로 종료되어야 함

@pytest.mark.asyncio
async def test_parser_start_idempotency(setup_parser):
	"""
	15. start() 메서드를 여러 번 호출했을 때 중복 Task가 생성되지 않고 한 번만 실행되는지 확인합니다.
	"""
	data_queue, packet_queue, parser = setup_parser
	first_task = parser._parse_task
	parser.start() # 다시 start 호출
	await asyncio.sleep(0.05)
	second_task = parser._parse_task
	assert first_task is second_task # 동일한 Task 인스턴스여야 함
	assert not first_task.done()

@pytest.mark.asyncio
async def test_parser_parse_method_direct_call(setup_parser):
	"""
	16. parse() 메서드를 직접 호출했을 때 (Task 생성 없이) 어떻게 동작하는지 확인합니다.
		(실제 사용 권장 방법은 아니나, 내부 동작 이해를 위해)
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
async def test_parser_custom_parser_behavior():
	"""
	17. BaseParser를 상속받아 재정의된 parse 메서드가 올바르게 작동하는지 확인합니다.
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
async def test_parser_queue_join_after_stop(setup_parser):
	"""
	18. stop() 호출 후 data_queue.join()이 어떻게 동작하는지 확인합니다.
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
async def test_parser_empty_queues_after_stop(setup_parser):
	"""
	19. 파서 종료 후 큐가 완전히 비워지는지 확인합니다.
	"""
	data_queue, packet_queue, parser = setup_parser
	await parser.stop()
	await asyncio.sleep(0.1) # 종료 작업 완료 대기

	assert data_queue.empty()
	assert packet_queue.empty()

@pytest.mark.asyncio
async def test_parser_task_cancellation_during_parse(setup_parser):
	"""
	20. parse Task가 외부에서 취소되었을 때 올바르게 종료되는지 확인합니다.
	"""
	data_queue, packet_queue, parser = setup_parser
	parser_task = parser._parse_task

	await data_queue.put(b"Data that might be partially processed")
	await asyncio.sleep(0.01) # 잠시 대기

	parser_task.cancel()
	with pytest.raises(asyncio.CancelledError):
		await parser_task # 취소된 태스크가 완료될 때까지 대기

	# 처리된 메시지 패킷 모두 제거하기
	while (not packet_queue.empty()):
		await packet_queue.get()
		packet_queue.task_done()

	# 태스크가 취소되었으므로 더 이상 데이터가 처리되지 않아야 함
	await data_queue.put(b"Data after cancellation")
	await asyncio.sleep(0.1)
	assert packet_queue.empty() or packet_queue.qsize() == 0 # 이미 처리된 데이터는 있을 수 있지만, 이후 데이터는 처리되면 안됨


if (__name__ == "__main__"):
	pytest.main( [ __file__, "-v"] )
