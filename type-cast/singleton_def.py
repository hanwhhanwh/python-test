from threading import Thread

class MetaSingleton(type):
	
	_instance = {}
	
	def __call__( cls, *args, **kwargs):
		if cls not in cls._instance:
			cls._instance[cls] = super( MetaSingleton, cls).__call__( *args, **kwargs)
			
		return cls._instance[cls]


class Box( Thread, metaclass = MetaSingleton):    
	
	__box = {}

	def __init__(self):
		super(Box, self).__init__()
		print('start Box')
	
	def add(self, key, value):
		self.__box[key] = value

	def get(self, key):
		return self.__box[key]
	
	def remove(self, key):
		self.__box.pop(key)
		
	def show(self):
		for d in self.__box:
			print( d)
