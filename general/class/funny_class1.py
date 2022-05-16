class MyClass:
	def __init__(self):
		self.data = 5

b = MyClass()
print(f'isinstance(b, MyClass) is {isinstance(b, MyClass)}')
print(b.__dict__)
b.data2 = 100
print(b.__dict__)
print(f'isinstance(b, MyClass) is {isinstance(b, MyClass)}')

"""
isinstance(b, MyClass) is True
{'data': 5}
{'data': 5, 'data2': 100}
isinstance(b, MyClass) is True
"""