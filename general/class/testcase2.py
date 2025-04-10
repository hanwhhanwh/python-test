# -*- coding: utf-8 -*-
# TestCase - guide to unit tests demo 2
# date	2025-04-10
# author	hbesthee@naver.com
from unittest import main, TestCase


def create_database_connection() -> Connection:
	# 데이터베이스 연결 만들기
	# ...
	pass


class TestDatabase(TestCase):
	
	def setUp(self) -> None:
		# 각 테스트 메소드 실행 전에 호출됩니다.
		self._connection = create_database_connection()
	
	def tearDown(self) -> None:
		# 각 테스트 메소드 실행 후에 호출됩니다.
		self._connection.close()
	
	def test_database_query(self) -> None:
		result = self._connection.execute("SELECT * FROM users")
		self.assertIsNotNone(result)


if (__name__ == '__main__'):
	main()