# -*- coding: utf-8 -*-
# 재귀호출을 이용한 딕셔너리 비교 함수
# made : hbesthee@naver.com
# date : 2025-08-28

from typing import Dict, Any

def compare_dict(bigger: Dict[Any, Any], smaller: Dict[Any, Any]) -> bool:
	"""
	dict smaller의 모든 키-값 쌍이 dict bigger에 동일하게 포함되는지 비교합니다. (재귀처리)

	Args:
		bigger (Dict[Any, Any]): 기준이 되는 딕셔너리.
		smaller (Dict[Any, Any]): 비교 대상이 되는 딕셔너리.

	Returns:
		bool: dict smaller의 모든 키-값 쌍이 dict bigger에 존재하면 True, 아니면 False.
	"""
	for key, value in smaller.items():
		# dict B의 키가 dict A에 존재하지 않는 경우
		if (key not in bigger):
			return False

		# dict_a와 dict_b의 값이 모두 dict인 경우
		if (isinstance(bigger[key], dict) and isinstance(value, dict)):
			# 두 딕셔너리를 재귀적으로 비교
			if (not compare_dict(bigger[key], value)):
				return False
		# 값이 딕셔너리가 아니고, 값이 서로 다른 경우
		elif (bigger[key] != value):
			return False

	return True



if (__name__ == "__main__"):
	dict_A = {
		'name': 'Alice',
		'age': 30,
		'contact': {'email': 'alice@example.com', 'phone': '123-4567'},
		'city': 'Seoul'
	}

	dict_B_1 = {
		'contact': {'email': 'alice@example.com'}
	}

	dict_B_2 = {
		'contact': {'phone': '999-9999'} # phone number is different
	}

	dict_B_3 = {
		'contact': {'fax': '555-5555'} # new key 'fax' is not in dict_A
	}
	
	print(f"dict_A: {dict_A}")
	print(f"dict_B_1: {dict_B_1}")
	print(f"dict_B_2: {dict_B_2}")
	print(f"dict_B_3: {dict_B_3}")
	print("-" * 20)

	print(f"dict_B_1이 dict_A에 포함되는가? {compare_dict(dict_A, dict_B_1)}")  # True
	print(f"dict_B_2가 dict_A에 포함되는가? {compare_dict(dict_A, dict_B_2)}")  # False
	print(f"dict_B_3가 dict_A에 포함되는가? {compare_dict(dict_A, dict_B_3)}")  # False