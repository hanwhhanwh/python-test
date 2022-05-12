# https://docs.python.org/ko/3/library/multiprocessing.html
# https://docs.python.org/ko/3/library/signal.html
# https://psutil.readthedocs.io/en/latest/
# ValueError: only SIGTERM, CTRL_C_EVENT and CTRL_BREAK_EVENT signals are supported on Windows

from multiprocessing import Process
from os import kill

import psutil
import signal
import time


_terminated = False


def new_handler(signum, frame) -> None:
	global _terminated
	print(f'Signal handler called with signal : {signum}')
	_terminated = True


def multiproc():
	signal.signal(signal.SIGBREAK, new_handler)
	index = 0
	while (not _terminated):
		time.sleep(0.5)
		index += 1
		print(f'index = {index}')
	print(f'multiproc() end...')


if __name__ == '__main__':
	print('sub-process started...')
	p = Process(target=multiproc)
	p.start()
	print('wait 3 second...')
	time.sleep(3)
	proc = psutil.Process(p.pid)
	# kill(p.pid, signal.SIGILL)
	proc.send_signal(signal.CTRL_BREAK_EVENT)

	p.join()

""" Result
sub-process started...
wait 3 second...
index = 1
index = 2
index = 3
index = 4
index = 5
index = 6
Signal handler called with signal : 21
multiproc() end...
"""