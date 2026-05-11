# -*- coding: utf-8 -*-
# Galois LFSR (Linear Feedback Shift Register) 예시
# made : hbesthee@naver.com
# date : 2026-05-11

from typing import Final
import os





class FrameIdLfsr:
	"""Galois LFSR 기반 32비트 유사 랜덤 순열 프레임 ID 생성기.

	2^32-1 개의 완전 순열을 보장한다 (0 제외).
	탭 다항식: x^32 + x^31 + x^29 + x + 1 (0xD0000001).

	Args:
		seed: 시작 상태. 0이 아닌 32비트 정수.
	"""

	_TAP: Final[int] = 0xD0000001
	_MASK: Final[int] = 0xFFFFFFFF

	def __init__(self, seed: int = 0x90ABCDEF) -> None:
		assert (seed != 0), "LFSR seed must not be 0"
		self._state: int = seed & self._MASK
		self._start: int = self._state
		self._exhausted: bool = False

	def next(self) -> int:
		"""다음 고유 ID를 반환한다.

		Returns:
			int: 유사 랜덤 순서의 고유 32비트 정수.

		Raises:
			OverflowError: 2^32-1 주기 소진 시.
		"""
		if (self._exhausted):
			raise OverflowError("LFSR 32-bit period exhausted")
		val = self._state
		lsb = self._state & 1
		self._state = (self._state >> 1) ^ (self._TAP if lsb else 0)
		self._state &= self._MASK
		if (self._state == self._start):
			self._exhausted = True
		return val



if __name__ == "__main__":
	seed = int.from_bytes(os.urandom(4), 'big') or 0xABCD
	# frame_id_gen = FrameIdLfsr(seed=seed)
	frame_id_gen = FrameIdLfsr()
	for frame_index in range(10):
		frame_id = frame_id_gen.next()
		print(f"{frame_index + 1} : {frame_id=}")
