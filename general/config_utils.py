"""
@brief INI config utilities
@made hbesthee@naver.com
@date 2022-05-13
"""

from configparser import ConfigParser
from os import getcwd, rename, path, remove
from time import localtime, strftime


class IniConfigBase:
	""" 설정값 관리 기본 클래스 """

	def __init__(self, runpath = None) -> None:
		if (runpath == None):
			runpath = getcwd()
		self._ini_file_name = f'{runpath}/option.ini'
		self._section_name = 'OPTION'
		self._defaults = dict() # 기본값은 문자열로 할당하기
		self._is_modified = False # 환경설정 변경 여부
		pass


	def load(self, config) -> None:
		""" 지정한 configParser 객체로부터 설정값을 읽어 옵니다.
			속성에 해당하는 설정이 없으면,
			self.__defaults에 지정된 값으로 기본값을 할당합니다.
			self.__defaults에 아무런 값도 지정되어 있지 않으면 멤버 변수들은 모두 None로 초기화됩니다.
			@param config configParser 객체
		"""
		if (not config.has_section(self._section_name)):
			# 환경설정 파일에 섹션이 없으면 기본값으로 할당함.
			# 기본값(self.__defaults)이 설정되지 않은 경우, 모든 멤버 변수가 None로 할당됨
			for class_variable_name in self.__dict__.keys():
				if ( class_variable_name.startswith('_') or class_variable_name.startswith('__') ):
					continue # private, protected 멤버 변수는 제외함

				object.__setattr__(self, class_variable_name, self._defaults.get(class_variable_name))
			self._is_modified = False
			return

		for class_variable_name in self.__dict__.keys():
			if ( class_variable_name.startswith('_') or class_variable_name.startswith('__') ):
				continue # private, protected 멤버 변수는 제외함

			# 멤버 변수를 환경설정에서 읽어 들인 값으로 할당
			if (config.has_option(self._section_name, class_variable_name)):
				value = config.get(self._section_name, class_variable_name)
			else:
				# 기본값(self.__defaults)이 설정되지 않은 경우, 모든 멤버 변수가 None로 할당됨
				value = self._defaults.get(class_variable_name)
			object.__setattr__(self, class_variable_name, value)

		self._is_modified = False


	def load(self, ini_file_name = None) -> None:
		""" 지정한 INI 파일로부터 설정값을 읽어 옵니다.
			파일이 없거나 속성에 해당하는 설정이 없으면,
			self.__defaults에 지정된 값으로 기본값을 할당합니다.
			self.__defaults에 아무런 값도 지정되어 있지 않으면 멤버 변수들은 모두 None로 초기화됩니다.
		"""
		if (ini_file_name == None):
			ini_file_name = self._ini_file_name

		config = ConfigParser()
		config.read(ini_file_name, encoding = "UTF-8")

		self.load(config)


	def save(self, ini_file_name = None, is_backup = True) -> None:
		""" 현재 설정 정보를 저장합니다.
		is_backup 설정이 되어 있으면 기존 설정 파일을 현재시각 정보로 백업합니다. """
		if (ini_file_name == None):
			ini_file_name = self._ini_file_name
		self._is_modified = False

		if (path.exists(ini_file_name)):
			if (is_backup):
				surfix = strftime('%Y%m%d_%I%M%S', localtime())
				rename(ini_file_name, f'{ini_file_name}.{surfix}')
			else:
				remove(ini_file_name)

		config = ConfigParser()
		config.add_section(self._section_name)
		for class_variable_name in self.__dict__.keys():
			if ( class_variable_name.startswith('_') or class_variable_name.startswith('__') ):
				continue # private, protected 멤버 변수는 제외함

			value = getattr(self, class_variable_name)
			if (isinstance(value, str)):
				str_value = value
			else:
				try:
					str_value = f'{value}'
				except:
					str_value = None
			if ((str_value != None) and (value != None) ):
				config.set(self._section_name, class_variable_name, str_value)

		with open(ini_file_name, 'w') as configfile:
			config.write(configfile)
			configfile.close()


if (__name__ == '__main__'):

	class MyOption(IniConfigBase):
		def __init__(self, runpath = None) -> None:
			# IniConfigBase.__init__(None)
			self.left = '100'
			self.top = '200'
			self.width = '640'
			self.height = '480'
			super().__init__(runpath = runpath)
			print(self._ini_file_name)
			self._defaults = { 'left': '150', 'top': '150' }


	config = MyOption()
	print(config.left, config.top, config.width, config.height)
	config.load()
	print(config.left, config.top, config.width, config.height)
	config.left = str(int(config.left) + 10)
	config.save()

