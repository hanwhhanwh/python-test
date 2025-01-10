# Constant of label viewer
# make hbesthee@naver.com
# date 2024-07-31

from logging import Logger
from os.path import exists
from typing import Final



LV_WINDOW_NAME: Final				= 'label_viewer'



JKEY_LOG_LEVEL: Final				= 'log_level'
JKEY_VIEWER_HEIGHT: Final			= 'viewer_height'
JKEY_VIEWER_WIDTH: Final			= 'viewer_width'
JKEY_KEY_LEFT: Final				= 'key_left'
JKEY_KEY_RIGHT: Final				= 'key_right'



DEF_LOG_LEVEL: Final				= 10
DEF_VIEWER_HEIGHT: Final			= 768
DEF_VIEWER_WIDTH: Final				= 1280



# viewer default option
DEF_VIEWER_CONF: Final = {
	JKEY_LOG_LEVEL: DEF_LOG_LEVEL
	, JKEY_VIEWER_HEIGHT: DEF_VIEWER_HEIGHT
	, JKEY_VIEWER_WIDTH: DEF_VIEWER_WIDTH
}


FILENAME_VIEWER_CONF: Final			= 'label_viewer.conf'








def get_dict_value(target_dict, key, default_value = None):
	""" dict 객체 내에서 key에 해당하는 값을 반환합니다.
	key에 해당하는 값을 찾을 수 없을 경우에는 default_value를 반환합니다.

	Args:
		target_dict (dict): 입력 dict 객체
		key (string): key 문자열
		default_value (Any, optional): 기본값으로 반환할 값. Defaults to None.

	Returns:
		Any: dict 객체 내에서 key로 찾은 데이터 값. 없으면 default_value 값이 반환됩니다.
	"""
	if (type(target_dict) is dict):
		value = target_dict.get(key)
		if (value == None):
			return default_value
		else:
			return value
	else:
		return default_value


def hexa(input_bytes: bytes, max_row_bytes: int = 0) -> str:
	""" 입력한 bytes 데이터를 16진 문자열로 변환하여 반환합니다.

	Args:
		input_bytes (bytes): 16진 문자열로 변환할 bytes 데이터
		max_row_bytes (int, optional): 1행에 표시할 최대 byte 수. Defaults to 0. (0이면 줄바꿈 없음)

	Returns:
		str: 입력한 bytes 데이터에 대한 16진 문자열. print(hexa(b'asdf', max_row_bytes = 3))
	"""
	bytes_len, result = len(input_bytes), ''
	if (bytes_len ==  0):
		return result

	if (max_row_bytes > 0):
		for index in range(bytes_len):
			if ( (index % max_row_bytes) == 0 ):
				result += '\r\n'
			result += f'{input_bytes[index]:02X} '
	elif (max_row_bytes == 0):
		for index in range(bytes_len):
			result += f'{input_bytes[index]:02X} '

	return result


def init_conf_files(confs: tuple, logger = None) -> None:
	""" 주어진 confs 목록대로 설정 파일을 확인하고, 설정 파일이 없으면 기본 설정으로 초기화합니다.

	Args:
		confs (tuple): 설정 파일명 및 기본 설정 정보 목록 ( (파일명1, 기본설정 객체1), (파일명2, 기본설정 객체2), ... )
		logger (Logger): 설정 파일이 초기화되어 생성될 때 기록을 남길 로깅 객체
	"""
	for conf in confs:
		filename, conf_def = conf
		if (not exists(filename)):
			save_json_conf(filename, conf_def)
			if (logger):
				logger.info(f'{filename} 파일을 생성하였습니다.')


def load_json_conf(json_file_path):
	""" JSON 파일을 열어 dict 형태로 로딩합니다.

	Args:
		json_file_path (string): JSON 파일에 대한 경로 문자열 (파일명 포함)

	Returns:
		(dict, error_message): 이상이 없다면, JSON 객체를 반환하고 오류가 발생한 경우에는 error_message 항목에 오류 문자열을 반환합니다.
	"""
	from json import loads
	from os import path

	if (not path.exists(json_file_path)):
		return (None, "load_json_conf error: FileNotFoundError: [Errno 2] No such file")

	with open(json_file_path, mode = "r", encoding = 'UTF-8') as f:
		json_str = f.read()
		try:
			json_data = loads(json_str)
			return (json_data, '')
		except Exception as e:
			return (None, f'load_json_conf error: {e}')


def make_init_folders(folders: tuple) -> None:
	""" 주어진 폴더 목록이 각각 존재하는지 확인하고, 존재하지 않으면 해당 폴더를 생성합니다.

	Args:
		folders (tuple): 생성할 폴더 목록

	Returns:
		None
	"""
	from os import path, makedirs

	for folder in folders:
		if (not path.exists(folder)):
			makedirs(folder)


def save_json_conf(json_file_path: str, conf: dict) -> int:
	""" dict 형식의 설정 정보를 JSON 파일로 저장합니다.

	Args:
		json_file_path (str): 저장될 JSON 파일에 대한 경로 문자열 (파일명 포함)
		conf (dict): JSON 형식으로 저장할 설정 정보

	Returns:
		(int, error_message): 이상이 없다면 0, 오류가 발생한 경우에는 오류 코드 = 1
	"""
	from json import dumps

	try:
		with open(json_file_path, mode = "wt", encoding = 'UTF-8') as f:
			json_str = dumps(conf, indent = 4, ensure_ascii = False)
			f.write(json_str)
			return (0, '')
	except Exception as e:
		return (1, f'save_json_conf error: {e}')


def save_label_values(label_filename: str, values: list, image_scale: float = 1.0) -> int:
	""" 라벨 데이터를 주어진 이름으로 저장합니다.
	
	Args:
		label_filename (str): 라벨 파일명
		values: (list): 라벨 데이터

	Returns:
		int: 0 = 성공, else = 오류 코드
	"""
	label_file = open(label_filename, "wt")
	for value_index in range(15):
		if (value_index == 0):
			label_file.write(f'{values[value_index]}')
		else:
			label_file.write(f' {float(values[value_index]) * image_scale:.3f}')
	label_file.close()
