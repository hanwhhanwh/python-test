# -*- coding: utf-8 -*-
# serial_asyncio() demo - open_serial_connection
# made : whhan@cnuglobal.com
# date : 2025-10-16

# Original Packages
from asyncio import get_running_loop, run, sleep, wait_for, \
					AbstractEventLoop, Protocol, Queue, StreamReader, StreamWriter
from io import BytesIO
from time import time
from typing import Any, Coroutine, Final, Generator, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch



# Third-party Packages
import pytest




from serial_demo2 import main_serial, SERIAL_BAUDRATE, SERIAL_PORT



class MockStreamReader:
	"""AsyncMock 기반 StreamReader 모의 클래스"""

	def __init__(self, initial_data: Optional[bytes] = None) -> None:
		"""
		Args:
			initial_data (Optional[bytes]): 초기 버퍼 데이터
		"""
		self._queue = Queue()
		self._buffer = BytesIO(initial_data if initial_data else b"")
		# read 메서드를 AsyncMock으로 정의
		self.read = AsyncMock(side_effect=self._read_impl)


	async def _read_impl(self, n: int = -1) -> bytes:
		"""
		내부 BytesIO에서 실제로 읽기 동작을 수행하는 함수
		AsyncMock이 side_effect로 호출
		"""
		data = self._buffer.read(n)
		if (data == b''):
			data = await self._queue.get()
			self._buffer.write(data)
			data = self._buffer.read(n)
		return data


	def inject(self, data: bytes) -> None:
		"""
		외부에서 데이터를 주입하는 함수

		Args:
			data (bytes): 주입할 데이터
		"""
		self._queue.put_nowait(data)


	def inject_with_flush(self, data: bytes) -> None:
		"""
		외부에서 데이터를 주입하는 함수. 기존 읽은 데이터는 모두 제거함

		Args:
			data (bytes): 주입할 데이터
		"""
		remaining = self._buffer.read()
		self._buffer = BytesIO(data + remaining)



class MockStreamWriter:
	"""
	asyncio.StreamWriter의 write() 메서드를 모의 클래스.
	"""
	def __init__(self: 'MockStreamWriter') -> None:
		"""MockStreamWriter 객체를 초기화합니다."""
		super().__init__()
		# write와 close 메서드가 호출된 기록을 남기도록 설정
		self.write = MagicMock() # 동기
		self.close = AsyncMock() # 비동기


# Mock 객체 인스턴스를 저장할 전역 변수
mock_reader_instance: MockStreamReader
mock_writer_instance: MockStreamWriter


# serial_asyncio.open_serial_connection 함수를 모킹하는 함수
async def mock_open_serial_connection(
	url: str,
	baudrate: int,
	loop: Optional[AbstractEventLoop] = None
) -> Tuple[MockStreamReader, MockStreamWriter]:
	"""
	open_serial_connection의 모킹 함수.

	Args:
		url: 시리얼 포트 URL.
		baudrate: 통신 속도.
		loop: asyncio 이벤트 루프.

	Returns:
		Tuple[MockStreamReader, MockStreamWriter]: 모킹된 reader와 writer 객체.
	"""
	global mock_reader_instance
	global mock_writer_instance

	# 테스트를 위한 초기 데이터를 BytesIO에 저장
	initial_data: bytes = b'first data packet\n'
	mock_reader_instance = MockStreamReader(initial_data=initial_data)
	mock_writer_instance = MockStreamWriter()

	print(f"모의 연결 생성: {url} @ {baudrate}")

	# URL과 Baudrate가 일치하는지 확인하는 단언문 (선택 사항)
	assert (url == SERIAL_PORT)
	assert (baudrate == SERIAL_BAUDRATE)

	return mock_reader_instance, mock_writer_instance


# === pytest fixture 정의 ===

@pytest.fixture
def mock_serial_connection() -> Generator[Any, Any, None]:
	"""
	serial_asyncio.open_serial_connection을 모킹하는 픽스처.
	"""
	# serial_asyncio 모듈 내의 open_serial_connection 함수를 모킹합니다.
	with patch(
		'serial_demo2.open_serial_connection',
		new=mock_open_serial_connection
	) as mock:
		yield mock




@pytest.mark.asyncio
async def test_main_serail_echo_logic(
	mock_serial_connection: Generator[Any, Any, None],
	capfd: pytest.CaptureFixture
) -> None:
	"""
	main_serail 함수가 데이터를 읽고(TimeoutError 없이),
	이후 타임아웃 시 'hello\n'를 쓰는(TimeoutError 발생 시) 로직을 시험합니다.

	Args:
		mock_serial_connection: open_serial_connection을 모킹하는 픽스처.
		capfd: 표준 출력(print)을 캡처하는 pytest 픽스처.
	"""
	print("\n--- 테스트 시작: main_serail_echo_logic ---")

	# 1. main_serail 실행
	# 실행 결과는 reader가 첫 번째 read에서 데이터를 반환하고,
	# 두 번째 read에서 1초 타임아웃에 걸려 writer.write(b'hello\n')를 호출해야 합니다.

	# 테스트 시간 단축을 위해, 전체 실행 시간이 너무 길어지지 않도록 wait_for()를 사용합니다.
	# 두 번의 read() 시도 (첫 번째 성공, 두 번째 실패/타임아웃 유도) 후 종료합니다.
	try:
		# main_serail 내부에서 2번의 루프(read 성공, read 타임아웃)가 실행되도록 합니다.
		# 타임아웃이 1초이므로, 총 2초 + 실행 시간 정도가 소요될 수 있습니다.
		await wait_for(main_serial(), timeout=1.5)
	except TimeoutError:
		# 정상적으로 루프가 2번 실행된 후 wait_for에서 타임아웃이 발생하는 것은 예상된 결과입니다.
		print("테스트 루프 종료 (wait_for 타임아웃).")
		pass
	except Exception as e:
		pytest.fail(f"예상치 못한 예외 발생: {e}")

	# 2. 검증

	# Mock 객체가 생성되었는지 확인
	assert (mock_reader_instance is not None)
	assert (mock_writer_instance is not None)

	# 2-1. 데이터 읽기 및 표준 출력 검증
	mock_reader_instance.read.assert_awaited() # 최소 1회 await 되었나?
	# reader.read()는 2번 호출되어야 합니다. (최초 데이터가 있는 BytesIO를 전달하였음)
	assert mock_reader_instance.read.call_count == 2 # 2회 호출되었는가?
	mock_reader_instance.read.assert_awaited_with(1024) # 마지막 호출 값 확인

	# 캡처된 표준 출력(print) 내용 검증
	out, err = capfd.readouterr()
	expected_output = 'first data packet' # decode() 후 print된 값
	assert (expected_output in out)
	print(f"표준 출력 확인: '{expected_output}' 포함됨.")

	# 2-2. 데이터 쓰기 검증 (TimeoutError 발생 시)
	# writer.write(b'hello\n')는 타임아웃(두 번째 루프) 시 1번 호출되어야 합니다.
	# AsyncMock의 call_args_list를 사용하여 호출 기록을 확인합니다.
	expected_call = (b'hello\n',)

	# writer.write가 정확히 1번 호출되었는지 확인
	mock_writer_instance.write.assert_called_with(expected_call[0])

	# 호출된 인수가 정확한지 확인 (write()는 튜플 형태의 인수를 받습니다)
	assert (mock_writer_instance.write.call_args_list[0].args == expected_call)
	print(f"writer.write() 호출 확인: {expected_call} 로 1회 호출됨.")

	print("--- 테스트 종료 ---")



if (__name__ == "__main__"):
	pytest.main(["-v", __file__])
	# pytest.main(["-v", "-s", __file__])
	# pytest.main(["-s", __file__])
