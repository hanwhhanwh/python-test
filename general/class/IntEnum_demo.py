# -*- coding: utf-8 -*-
# IntEnum 사용 예제
# made : hbesthee@naver.com
# date : 2025-12-03

# Original Packages
from enum import IntEnum
from typing import Final, List, Optional



class MeterCmdEnum(IntEnum):
	"""
	프로토콜 Command (Cmd) 정의 클래스
	"""
	# Meter -> CPU (Push) 명령
	METER_DATA_TRANSMISSION: Final[int] = 0x80  # 계측 데이터 전송 [cite: 4]
	LEAKAGE_CURRENT_OCCURRENCE: Final[int] = 0xA0  # 누설전류 발생 [cite: 4]
	OVERCURRENT_OCCURRENCE: Final[int] = 0xB0  # 과전류 발생 [cite: 4]
	POWER_FAILURE_OCCURRENCE: Final[int] = 0xC0  # 정전 발생 [cite: 4]

	# 설정/조회 명령
	FIRMWARE_VERSION_INFO: Final[int] = 0xC3  # 펌웨어 버전 정보 [cite: 4]
	TIME_READ_WRITE: Final[int] = 0xC5  # 시간 쓰기/읽기 [cite: 4]
	PARAMETER_SET_INQUIRY: Final[int] = 0xC8  # 파라미터 설정/조회 [cite: 4]

	# 펌웨어 업데이트 명령
	FW_IMAGE_TRANSFER: Final[int] = 0xE0  # Fw Image 전송 (Transfer & Activate 포함) [cite: 4, 9, 12]
	FW_IMAGE_TRANSFER_RESPONSE: Final[int] = 0xF0  # Fw Image 전송 응답 [cite: 4, 14]


	@staticmethod
	def is_valid_cmd(cmd_value: int) -> bool:
		"""
		MeterCmd 열거형의 정의된 프로토콜 명령중 하나인지 확인합니다.
		새롤운 명령이 추가되어도 코드를 수정할 필요가 없습니다.

		Args:
			cmd_value: 유효성을 검사할 1 byte 명령값 (int).

		Returns:
			유효한 명령값이면 True, 아니면 False를 반환합니다.
		"""
		# Enum 클래스는 멤버의 값으로 멤버를 조회할 수 있습니다.
		# 존재하지 않는 값으로 조회 시 ValueError가 발생합니다.
		try:
			_ = MeterCmdEnum(cmd_value)
			return True
		except ValueError:
			return False


	@staticmethod
	def get_cmd_name(cmd_value: int) -> Optional[str]:
		"""
		명령값에 해당하는 명령의 이름 (Enum 멤버 이름)을 반환합니다.
		명령 이름이 필요한 경우에 유용하며, 내부적으로 유효성 검사 역할도 수행합니다.

		Args:
			cmd_value: 명령값 (int).

		Returns:
			명령의 이름 (str) 또는 유효하지 않으면 None을 반환합니다.

		"""
		try:
			return MeterCmdEnum(cmd_value).name
		except ValueError:
			return None



def main():
	"""
	MeterCmdEnum 열거형 클래스의 사용 예시입니다.
	"""
	# 테스트 명령값
	valid_cmd: int = MeterCmdEnum.METER_DATA_TRANSMISSION.value  # 0x80
	invalid_cmd: int = 0xFF  # 정의되지 않은 명령

	# Enum 멤버 조회를 통한 확인
	print(f"## 리스트를 통한 확인 (is_valid_cmd)")
	print(f"명령 0x{valid_cmd:02X} 유효성: {MeterCmdEnum.is_valid_cmd(valid_cmd)}")
	print(f"명령 0x{invalid_cmd:02X} 유효성: {MeterCmdEnum.is_valid_cmd(invalid_cmd)}\n")

	# 명령 이름 가져오기
	print(f"## 명령 이름 가져오기 (get_cmd_name)")
	print(f"명령 0x{valid_cmd:02X} 이름: {MeterCmdEnum.get_cmd_name(valid_cmd)}")
	print(f"명령 0x{invalid_cmd:02X} 이름: {MeterCmdEnum.get_cmd_name(invalid_cmd)}")


if (__name__ == "__main__"):
	main()


"""Result>>
## 리스트를 통한 확인 (is_valid_cmd)
명령 0x80 유효성: True
명령 0xFF 유효성: False

## 명령 이름 가져오기 (get_cmd_name)
명령 0x80 이름: METER_DATA_TRANSMISSION
명령 0xFF 이름: None
"""