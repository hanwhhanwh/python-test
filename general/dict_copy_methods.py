# dict 객체 복사의 세 가지 방법 : 참조 복사, 얕은 복사, 깊은 복사 비교 예제
# make hbesthee@naver.com
# date 2024-12-03

print("\n1. 일반 복사 (참조 복사)")
original_dict = {'a': 1, 'b': [1, 2, 3]}
ref_copy = original_dict

# 값 변경 시 원본도 함께 변경됨
ref_copy['a'] = 10
print(original_dict)  # {'a': 10, 'b': [1, 2, 3]}

print("원본 딕셔너리 ID:", id(original_dict))
print("참조 복사 딕셔너리 ID:", id(ref_copy))
print("딕셔너리 동일 여부:", original_dict is ref_copy)  # True


print("\n2. 얕은 복사 (Shallow Copy)")
import copy

original_dict = {'a': 1, 'b': [1, 2, 3]}
shallow_copy = copy.copy(original_dict)

# 1차 레벨 값 변경 시 원본에 영향 없음
shallow_copy['a'] = 10
print(original_dict)  # {'a': 1, 'b': [1, 2, 3]}

# 중첩된 리스트 변경 시 원본도 함께 변경됨
shallow_copy['b'][0] = 100
print(original_dict)  # {'a': 1, 'b': [100, 2, 3]}

print("원본 딕셔너리 ID:", id(original_dict))
print("얕은 복사 딕셔너리 ID:", id(shallow_copy))
print("딕셔너리 동일 여부:", original_dict is shallow_copy)  # False
print("내부 리스트 ID 비교:")
print("원본 리스트 ID:", id(original_dict['b']))
print("얕은 복사 리스트 ID:", id(shallow_copy['b']))  # 같은 ID


print("\n3. 깊은 복사 (Deep Copy)")
original_dict = {'a': 1, 'b': [1, 2, 3]}
deep_copy = copy.deepcopy(original_dict)

# 모든 중첩된 객체까지 완전히 독립적으로 복사
deep_copy['a'] = 10
deep_copy['b'][0] = 100

print(original_dict)  # {'a': 1, 'b': [1, 2, 3]}
print(deep_copy)      # {'a': 10, 'b': [100, 2, 3]}

print("원본 딕셔너리 ID:", id(original_dict))
print("깊은 복사 딕셔너리 ID:", id(deep_copy))
print("딕셔너리 동일 여부:", original_dict is deep_copy)  # False
print("내부 리스트 ID 비교:")
print("원본 리스트 ID:", id(original_dict['b']))
print("깊은 복사 리스트 ID:", id(deep_copy['b']))  # 다른 ID
