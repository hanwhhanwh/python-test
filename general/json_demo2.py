# JSON 데이터 다루는 예제 1
# date	2023-03-28
# author	hbesthee@naver.com


def load_json_conf(json_file_path):
	"""
		JSON 파일을 열어 dict 형태로 로딩합니다.

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
			return (json_data, None)
		except Exception as e:
			return (None, f'load_json_conf error: {e}')


if (__name__ == '__main__'):
	json_file_path = '../.vscode/settings.json'
	json_datas = load_json_conf(json_file_path)
	print(json_datas)

	json_datas = load_json_conf(json_file_path + '1')
	print(json_datas)

""" Execute Result:
({'python.pythonPath': 'C:\\Dev\\Python\\Python38\\python.exe'}, None)
(None, 'load_json_conf error: FileNotFoundError: [Errno 2] No such file')
"""