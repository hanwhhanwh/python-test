# INI handling sample
import configparser

config = configparser.ConfigParser()
config.read('python-test.ini', encoding="UTF-8")
sections = config.sections()
print(sections)

pt3 = config.get('RECT', 'pt3', fallback = '855,774') # don't care : 'RECT' section or 'pt3' option not exists, default value = '855,774'
print(pt3)

if 'RECT' in config: # check 'RECT' section
	secRECT = config['RECT']
	pt1 = secRECT['pt1']
	print(pt1)
	pt2 = secRECT['pt2']
	print(pt2)
	#pt3 = secRECT['pt3']
else:
	print('RECT section not exists, then by default value')
	pt1 = '468,203'
	pt2 = '1011,398'
	config.add_section('RECT')
	config['RECT']['pt1'] = pt1
	config['RECT']['pt2'] = pt2
	try:
		config.write(open('python-test.ini', 'w'))
	except:
		print('WARNING: config write fail!')
