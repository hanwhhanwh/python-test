class SingletonClass:
	_instance = None

	def __new__(cls):
		if cls._instance is None:
			print('Creating the object')
			cls._instance = super(SingletonClass, cls).__new__(cls)
		return cls._instance

obj1 = SingletonClass()
print(obj1)

obj2 = SingletonClass()
print(obj2)

""" output
Creating the object
<__main__.SingletonClass object at 0x000001B628078FA0>
<__main__.SingletonClass object at 0x000001B628078FA0>
"""