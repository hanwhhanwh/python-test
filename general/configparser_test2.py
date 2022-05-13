# INI handling sample
from configparser import ConfigParser
from os import getcwd, rename, path, remove
from time import localtime, strftime


class MyOption:
	""" 설정값 관리 클래스 """

	def __init__(self, runpath = None) -> None:
		if (runpath == None):
			runpath = getcwd()
		self.__ini_file_name = f'{runpath}/option.ini'
		self.__section_name = 'OPTION'
		self.__defaults = { '_left': '150' }
		self._left = '100'
		self._top = '200'
		self._width = '640'
		self._height = '480'
		self.is_modified = False
		pass


	def load(self, ini_file_name = None) -> None:
		""" 지정한 INI 파일로부터 설정값을 읽어 옵니다.
			파일이 없거나 속성에 해당하는 설정이 없으면,
			self.__defaults에 지정된 값으로 기본값을 할당합니다.
			self.__defaults에 아무런 값도 지정되어 있지 않으면 멤버 변수들은 모두 None로 초기화됩니다.
		"""
		if (ini_file_name == None):
			ini_file_name = self.__ini_file_name

		if (not path.exists(ini_file_name)):
			return

		config = ConfigParser()
		config.read(ini_file_name, encoding = "UTF-8")

		if (not config.has_section(self.__section_name)):
			# 환경설정 파일에 섹션이 없으면 기본값으로 할당함.
			# 기본값(self.__defaults)이 설정되지 않은 경우, 모든 멤버 변수가 None로 할당됨
			for class_variable_name in self.__dict__.keys():
				try:
					_ = class_variable_name.index('__')
					continue
				except ValueError:
					pass
				if (not class_variable_name.startswith('_')):
					continue

				object.__setattr__(self, class_variable_name, self.__defaults.get(class_variable_name))
			return

		for class_variable_name in self.__dict__.keys():
			try:
				_ = class_variable_name.index('__')
				continue
			except ValueError:
				pass
			if (not class_variable_name.startswith('_')):
				continue

			# '_' 한 문자로 시작하는 멤버 변수만 환경설정 값으로 읽어 들임
			if (config.has_option(self.__section_name, class_variable_name)):
				object.__setattr__(self, class_variable_name, config.get(self.__section_name, class_variable_name))
			else:
				# 기본값(self.__defaults)이 설정되지 않은 경우, 모든 멤버 변수가 None로 할당됨
				object.__setattr__(self, class_variable_name, self.__defaults.get(class_variable_name))

		self.is_modified = False


	def save(self, ini_file_name = None, is_backup = True) -> None:
		""" 현재 설정 정보를 저장합니다.
		is_backup 설정이 되어 있으면 기존 설정 파일을 현재시각 정보로 백업합니다. """
		if (ini_file_name == None):
			ini_file_name = self.__ini_file_name
		self.is_modified = False

		if (path.exists(ini_file_name)):
			if (is_backup):
				surfix = strftime('%Y%m%d_%I%M%S', localtime())
				rename(ini_file_name, f'{ini_file_name}.{surfix}')
			else:
				remove(ini_file_name)

		config = ConfigParser()
		config.add_section(self.__section_name)
		for class_variable_name in self.__dict__.keys():
			try:
				_ = class_variable_name.index('__')
				continue
			except ValueError:
				pass
			if (not class_variable_name.startswith('_')):
				continue

			value = getattr(self, class_variable_name)
			if (isinstance(value, str)):
				config.set(self.__section_name, class_variable_name, value)

		with open(ini_file_name, 'w') as configfile:
			config.write(configfile)
			configfile.close()


config = MyOption()
print(config._left, config._top, config._width, config._height)
config.load()
print(config._left, config._top, config._width, config._height)
config._left = str(int(config._left) + 10)
config.save()

