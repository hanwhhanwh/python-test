# -*- coding: utf-8 -*-
# 재귀호출을 이용한 딕셔너리 비교 함수
# made : hbesthee@naver.com
# date : 2025-08-28

from typing import Any, Dict, List


def compare_dict(bigger: Dict[Any, Any], smaller: Dict[Any, Any]) -> bool:
	"""
	dict smaller의 모든 키-값 쌍이 dict bigger에 동일하게 포함되는지 비교합니다. (재귀처리)

	Args:
		bigger (Dict[Any, Any]): 기준이 되는 딕셔너리.
		smaller (Dict[Any, Any]): 비교 대상이 되는 딕셔너리.

	Returns:
		bool: dict smaller의 모든 키-값 쌍이 dict bigger에 존재하면 True, 아니면 False.
	"""

	def compare_list(bigger_list: List, smaller_list: List):
		"""
		내부에 dict를 포함할 수 있는 리스트를 재귀적으로 비교합니다.

		Args:
			bigger_list (List[Any]): 기준이 되는 리스트.
			smaller_list (List[Any]): 비교 대상이 되는 리스트.

		Returns:
			bool: smaller_list의 모든 요소가 bigger_list에 순서대로 존재하고 동일하면 True, 아니면 False.
		"""
		if (len(bigger_list) != len(smaller_list)):
			return (False)

		for i in range(len(smaller_list)):
			item_bigger = bigger_list[i]
			item_smaller = smaller_list[i]

			# 두 요소가 모두 dict인 경우 재귀 호출
			if (isinstance(item_bigger, dict) and isinstance(item_smaller, dict)):
				if (not compare_dict(item_bigger, item_smaller)):
					return False
			# 두 요소의 데이터형이 다르거나, 값이 다른 경우
			elif (item_bigger != item_smaller):
				return False
		return True

	for key, smaller_value in smaller.items():
		# dict B의 키가 dict A에 존재하지 않는 경우
		if (key not in bigger):
			return False

		bigger_value = bigger[key]
		# dict_a와 dict_b의 값이 모두 dict인 경우
		if (isinstance(bigger_value, dict) and isinstance(smaller_value, dict)):
			# 두 딕셔너리를 재귀적으로 비교
			if (not compare_dict(bigger_value, smaller_value)):
				return False
		# 두 값이 모두 list인 경우 항목별 비교 ; dict인 경우 재귀 처리
		elif (isinstance(bigger_value, list) and isinstance(smaller_value, list)):
			if (not compare_list(bigger_value, smaller_value)):
				return False
		# 값이 딕셔너리가 아니고, 값이 서로 다른 경우
		elif (bigger_value != smaller_value):
			return False

	return True



if (__name__ == "__main__"):
	dict_A = {
		'name': 'Alice',
		'projects': [
			{'id': 'P-001', 'status': 'completed'},
			{'id': 'P-002', 'status': 'in-progress', 'details': {'owner': 'Bob'}}
		],
		'address': 'Seoul'
	}

	# (dict_A에 포함되는 부분 집합)
	dict_B_1 = {
		'projects': [
			{'id': 'P-001'},
			{'id': 'P-002', 'details': {'owner': 'Bob'}}
		]
	}

	# (리스트 내 딕셔너리 값이 다름)
	dict_B_2 = {
		'projects': [
			{'id': 'P-001'},
			{'id': 'P-002', 'details': {'owner': 'Charlie'}} # owner가 다름
		]
	}

	# (리스트의 길이가 다름)
	dict_B_3 = {
		'projects': [
			{'id': 'P-001'}
		]
	}
	
	# (리스트 내 딕셔너리가 아닌 다른 타입의 값이 다름)
	dict_A_simple_list = {'items': [1, 2, 3]}
	dict_B_simple_list = {'items': [1, 2, 4]}

	print(f"dict_A: {dict_A}")
	print(f"dict_B_1: {dict_B_1}")
	print(f"dict_B_2: {dict_B_2}")
	print(f"dict_B_3: {dict_B_3}")
	print("-" * 20)
	print("중첩된 리스트 내 딕셔너리 비교 결과:")
	print(f"dict_B_1이 dict_A에 포함되는가? {compare_dict(dict_A, dict_B_1)}")  # True
	print(f"dict_B_2가 dict_A에 포함되는가? {compare_dict(dict_A, dict_B_2)}")  # False
	print(f"dict_B_3가 dict_A에 포함되는가? {compare_dict(dict_A, dict_B_3)}")  # False
	
	print("-" * 20)
	print("단순 리스트 요소 비교 결과:")
	print(f"dict_B_simple_list가 dict_A_simple_list에 포함되는가? {compare_dict(dict_A_simple_list, dict_B_simple_list)}") # False