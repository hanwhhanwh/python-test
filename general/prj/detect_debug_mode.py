# -*- coding: utf-8 -*-
# 디버깅 중인인지, 아닌지 확인하는 방법
# made : hbesthee@naver.com
# date : 2025-01-15

from os import environ, getenv
from sys import gettrace, modules as sys_modules

import sys


def is_debugging1():
	return (gettrace() != None)


def is_debugging2():
	# print(environ)
	return bool(getenv('DEBUGPY_RUNNING'))


def is_debugging3():
	debugger_names = ['pdb', 'ipdb', 'PyDev', 'pydevd']
	return any(name in sys_modules for name in debugger_names)


print(f'{is_debugging1()=}')
print(f'{is_debugging2()=}')
print(f'{is_debugging3()=}')