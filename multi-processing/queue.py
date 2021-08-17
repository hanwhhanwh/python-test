# https://docs.python.org/ko/3/library/multiprocessing.html#multiprocessing.Queue

from multiprocessing import Process, Queue

def f(q):
	q.put([42, None, 'hello'])

if __name__ == '__main__':
	q = Queue()
	p = Process(target=f, args=(q,))
	if not q.empty():
		print(q.get())    # print
	p.start()
	if not q.empty(): # q is empty, then no print
		print(q.get_nowait())
	p.join()
	print(q.get_nowait()) # prints [42, None, 'hello']
