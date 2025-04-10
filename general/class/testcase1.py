# TestCase - guide to unit tests demo 1
# date	2025-04-10
# author	hbesthee@naver.com
from unittest import main, TestCase


class TestStringMethods(TestCase):
	
	def test_upper(self) -> None:
		self.assertEqual('hello'.upper(), 'HELLO')
	
	def test_isupper(self) -> None:
		self.assertTrue('HELLO'.isupper())
		self.assertFalse('Hello'.isupper())
	
	def test_split(self) -> None:
		s = 'hello world'
		self.assertEqual(s.split(), ['hello', 'world'])
		# split 시 separator를 지정하는 경우
		self.assertEqual(s.split('o'), ['hell', ' w', 'rld'])


if (__name__ == '__main__'):
	main()