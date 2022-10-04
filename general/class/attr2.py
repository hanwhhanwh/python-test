
class Section:
	_section_name = ''

	def __init__(self, section_name = '') -> None:
		self._section_name = section_name


class AutoAttr:
	""" Attributes automation
		Example:
			attributes = { 'GENERAL': { 'a': 1, 'b': 2}, 'DATA': { 'aa': '1', 'bb': '2'}}
			a= AutoAttr(attributes)
	a.GENERAL.a
	a.GENERAL.aa
	"""

	def __init__(self, defaults) -> None:
		self._defaults = defaults # 기본값은 문자열로 할당하기
		self._is_modified = False # 환경설정 변경 여부

		# defaults로 받은 데이터로 클래스 멤버 변수들 구성하기
		for key, value in defaults.items():
			if (type(value) == dict): # 섹션 처리
				section = Section(key)
				for s_key, s_value in value.items(): # 섹션내 항목 처리
					object.__setattr__(section, s_key, s_value)
				object.__setattr__(self, key, section)


if __name__ == '__main__':
	attributes = { 'GENERAL': { 'a': 1, 'b': 2}, 'DATA': { 'aa': '11', 'bb': '22'} }
	print(attributes)
	a = AutoAttr(attributes)
	print(a.GENERAL.a)
	print(a.DATA.aa)
