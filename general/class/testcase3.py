# -*- coding: utf-8 -*-
# TestCase - guide to unit tests demo 3
# date	2025-04-10
# author	hbesthee@naver.com
from unittest import main, TestCase


def divide(a, b) -> float:
	if b == 0:
		raise ValueError("Cannot divide by zero")
	return a / b


class TestDivision(TestCase):
	
	def test_division(self) -> None:
		self.assertEqual(divide(10, 2), 5)
	
	def test_zero_division(self) -> None:
		# divide(10, 0)이 ValueError를 발생시키는지 확인합니다.
		with self.assertRaises(ValueError):
			divide(10, 0)


if (__name__ == '__main__'):
	main()