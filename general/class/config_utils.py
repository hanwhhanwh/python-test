"""
@brief INI config utilities
@made hbesthee@naver.com
@date 2022-09-30
"""

from configparser import ConfigParser
from os import getcwd, rename, path, remove
from shutil import copyfile
from time import localtime, strftime
# from varname import nameof


class IniConfigSection:
	""" IniConfigBase 섹션을 위한 클래스 """
	_section_name = ''

	def __init__(self, section_name = '') -> None:
		self._section_name = section_name


def _load_attribute(config, section, defaults):
	""" 주어진 config 객에서 section 객체의 속성(attribute)을 읽어 옵니다. """
	for class_variable_name in section.__dict__.keys():
		if ( class_variable_name.startswith('_') or class_variable_name.startswith('__') ):
			continue # private, protected 멤버 변수는 제외함

		_attr = object.__getattribute__(section, class_variable_name)
		if (type(_attr) == IniConfigSection): # 섹션에 대한 처리
			_load_attribute(config, _attr)
		else:
			object.__setattr__(section, class_variable_name, defaults.get(class_variable_name))


class IniConfig:
	""" 환경설정값 관리 기본 클래스 
		Example:
			defaults = { 'GENERAL': { 'a': 1, 'b': 2}, 'DATA': { 'aa': '1', 'bb': '2'}}
			ini = IniConfigBase('/opt/my_config.ini', defaults)
	"""

	def __init__(self, ini_file_name, defaults = None) -> None:
		self._ini_file_name = ini_file_name
		self._is_modified = False # 환경설정 변경 여부
		self._load_from_dict(defaults) # 기본값 데이터 설정 & 멤버 변수 구성
		pass


	def _load_from_dict(self, defaults) -> None:
		""" defaults로 받은 데이터로 obj 객체 멤버 변수들 구성하기 """
		self._defaults = defaults
		for key, value in defaults.items():
			if (type(value) == dict): # 섹션 처리
				section = IniConfigSection(key)
				for s_key, s_value in value.items(): # 섹션내 항목 처리
					object.__setattr__(section, s_key, s_value)
				object.__setattr__(self, key, section)


	def _load(self, config) -> None:
		""" 지정한 configParser 객체로부터 설정값을 자동으로 읽어 옵니다. self._default_section_name = 'GENERAL' 섹션의 값들은 객체의 속성으로 읽어들입니다.
			속성에 해당하는 설정이 없으면,
			self.__defaults에 지정된 값으로 기본값을 할당합니다.
			self.__defaults에 아무런 값도 지정되어 있지 않으면 멤버 변수들은 모두 None로 초기화됩니다.
			@param config configParser 객체
		"""
		if (type(config) != ConfigParser):
			return

		for section_name, section in self.__dict__.items():
			if ( section_name.startswith('_') or section_name.startswith('__') ):
				continue # private, protected 멤버 변수는 제외함

			if (type(section) == IniConfigSection):
				for key in section.__dict__.keys():
					# 멤버 변수를 환경설정에서 읽어 들인 값으로 할당
					if (config.has_option(section_name, key)):
						value = config.get(section_name, key)
						object.__setattr__(section, key, value)

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

		self._load(config)


	def _save(self, config) -> None:
		""" 현재 설정 정보를 저장합니다.
					@param config configParser 객체
		"""
		if (type(config) != ConfigParser):
			return

		for section_name, section in self.__dict__.items():
			if ( section_name.startswith('_') or section_name.startswith('__') ):
				continue # private, protected 멤버 변수는 제외함

			if (type(section) == IniConfigSection):
				if (not config.has_section(section_name)):
					config.add_section(section_name)
				for key, value in section.__dict__.items():
					if ( key.startswith('_') or key.startswith('__') ):
						continue # private, protected 멤버 변수는 제외함
					try:
						str_value = f'{value}'
					except:
						str_value = None
					config.set(section_name, key, str_value)

		self._is_modified = False


	def save(self, ini_file_name = None, is_backup = True) -> None:
		""" 현재 설정 정보를 저장합니다.
		is_backup 설정이 되어 있으면 기존 설정 파일을 현재시각 정보로 백업합니다. """
		if (ini_file_name == None):
			ini_file_name = self._ini_file_name

		surfix = strftime('%Y%m%d_%I%M%S', localtime())
		backup_ini_file_name = f'{ini_file_name}.{surfix}'
		if (path.exists(backup_ini_file_name)):
			remove(ini_file_name)

		config = ConfigParser()
		with open(backup_ini_file_name, 'w') as configfile:
			self._save(config)
			config.write(configfile)
			configfile.close()

		if (is_backup):
			copyfile(backup_ini_file_name, ini_file_name)
		else:
			rename(backup_ini_file_name, ini_file_name)


if (__name__ == '__main__'):

	defaults = {
			'GENERAL': {'left': 100, 'top': 200, 'width': 640, 'height': 480}
			, 'RECT': {'r1':'10, 20, 30, 40'}
	}
	my_config = IniConfig('my.ini', defaults)

	my_config.load()
	print(my_config.GENERAL.left, my_config.GENERAL.top, my_config.GENERAL.width, my_config.GENERAL.height)
	my_config.GENERAL.left = str(int(my_config.GENERAL.left) + 10)
	my_config.save()
	print(type(my_config.RECT.r1), my_config.RECT.r1)
	
