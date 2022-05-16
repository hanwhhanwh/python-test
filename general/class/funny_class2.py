class MyClass:
	def __init__(self):
		self.__data = 5
		self.data = 1

class MySubClass(MyClass):
	def __init__(self):
		super().__init__()
		self.__data = 10

d = MySubClass()
print(f'd.__dict__ = {d.__dict__}')
print(f'd._MyClass__data = {d._MyClass__data}')
print(f'd._MySubClass__data = {d._MySubClass__data}')

"""
d.__dict__ = {'_MyClass__data': 5, 'data': 1, '_MySubClass__data': 10}
d._MyClass__data = 5
d._MySubClass__data = 10
"""
