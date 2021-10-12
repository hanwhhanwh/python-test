# https://docs.python.org/ko/3/library/multiprocessing.html#multiprocessing.Queue

from multiprocessing import Process, Queue
from _queue import Empty

def f(q):
	print('in subprocess')
	q.put([42, None, 'hello'])

if __name__ == '__main__':
	q = Queue()
	p = Process(target=f, args=(q,))
	if not q.empty():
		print(q.get())    # print
	p.start()
	if not q.empty(): # q is empty, then no print
		print(q.get_nowait())
	print('in main-process')
	print(q.get())
	p.join()
	try:
		print(q.get_nowait()) # prints [42, None, 'hello']
	except Exception as e:
		print(type(e)) # <class '_queue.Empty'>

	try:
		print(q.get(timeout = 1))
	except Exception as e:
		print('get() Exception :', type(e)) # <class '_queue.Empty'>
		if (isinstance(e, Empty)):
			print('get() Timeout!')
