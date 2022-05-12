# https://docs.python.org/ko/3/library/multiprocessing.html
# https://docs.python.org/ko/3/library/signal.html

from multiprocessing import Process, Queue
from os import kill

import signal
import time


_terminated = False


def new_handler(signum, frame) -> None:
	global _terminated
	print(f'Signal handler called with signal : {signum}')
	_terminated = True


def multiproc():
	signal.signal(signal.SIGILL, new_handler)
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
	kill(p.pid, signal.SIGILL)

	p.join()

