# JSON 데이터 다루는 예제 1
# date	2023-03-28
# author	hbesthee@naver.com

if (__name__ == '__main__'):
	from json import loads

	# Load JSON file => dict object (json_data)
	json_file_path = '../.vscode/settings.json'
	with open(json_file_path, mode = "r", encoding = 'UTF-8') as f:
		json_str = f.read()
		try:
			json_data = loads(json_str)
			print(f'json_data = {json_data}')
		except Exception as e:
			print(f'load_json_conf error: {e}')


