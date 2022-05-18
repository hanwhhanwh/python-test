from configparser import ConfigParser

config = ConfigParser()
config.read('option.ini', encoding = "UTF-8")

config.has_section
right = config.get('OPTION', 'right')
print(f'right = {right}')


right = config.get('section', 'right')
print(f'right = {right}')
