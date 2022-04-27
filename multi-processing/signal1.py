# Multi-processing and signal
# date: 2022-04-27
# make: hbesthee@naver.com

from _queue import Empty
from multiprocessing import Process, Queue
from os import getpid, kill, name, makedirs, path
from struct import calcsize, pack, unpack, unpack_from
from threading import Thread
# from typing import Final

import signal
import time


class NewProcess(Process):
	""" NewProcess calss """

	def __init__(self) ->None:
		""" constructor """

		super(NewProcess, self).__init__(name = self.__class__.__name__)

		print(f'class name = {self.__class__.__name__} / pid = {self.pid}')
		print(f'os.getpid() = {getpid()}')


	def run(self):
		count = 0
		print(count)
		while (True):
			count += 1
			print(count)
			time.sleep(1)


if (__name__ == '__main__'):
	print(f'main os.getpid() = {getpid()}')

	sub_process = NewProcess()
	print(f'sub_process pid 1 = {sub_process.pid}')
	sub_process.start()
	print(f'sub_process pid 2 = {sub_process.pid}')

	time.sleep(2)

	if (sub_process.is_alive()):
		# sub_process.kill() # kill(sub_process.pid, signal.SIGINT)
		sub_process.terminate() # Terminate process; sends SIGTERM signal or uses TerminateProcess()

	sub_process.join()

""" Result
main os.getpid() = 27432
class name = NewProcess / pid = None
os.getpid() = 27432
sub_process pid 1 = None
sub_process pid 2 = 24084
0
1
2
"""