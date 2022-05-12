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
	signal.signal(signal.SIGINT, new_handler)
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
	proc.send_signal(signal.CTRL_C_EVENT)

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
Signal handler called with signal : 2
multiproc() end...
Traceback (most recent call last):
  File "d:\Dev\Python\python-test\multi-processing\win-signal-SIGINT.py", line 43, in <module>
    p.join()
  File "C:\Dev\Python\Python39\lib\multiprocessing\process.py", line 149, in join 
    res = self._popen.wait(timeout)
  File "C:\Dev\Python\Python39\lib\multiprocessing\popen_spawn_win32.py", line 108, in wait
    res = _winapi.WaitForSingleObject(int(self._handle), msecs)
KeyboardInterrupt
"""