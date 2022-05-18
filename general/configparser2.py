from configparser import ConfigParser

config = ConfigParser()
config.read('option.ini', encoding = "UTF-8")

if (config.has_option('OPTION', 'right')):
	right = config.get('OPTION', 'right')
	print(f'right = {right}')
else:
	print(f'"OPTION" section "right" option not found!')

"""
Result
"OPTION" section "right" option not found!
"""
