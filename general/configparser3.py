from configparser import ConfigParser

config = ConfigParser()
config.read('option.ini', encoding = "UTF-8")

right = config.get('OPTION', 'right', fallback = None)
if (right == None):
	print(f'"OPTION" section "right" option not found!')
else:
	print(f'right = {right}')

""" or
right = config.get('OPTION', 'right', fallback = 100) # set default value 100


Result
"OPTION" section "right" option not found!
"""
