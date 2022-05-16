# reference : https://www.geeksforgeeks.org/getter-and-setter-in-python/

# Python program showing a
# use of property() function

class Geeks:
	def __init__(self):
		self.__age = 0
	
	# function to get value of _age
	def get_age(self):
		print("getter method called")
		return self.__age
	
	# function to set value of _age
	def set_age(self, a):
		print("setter method called")
		self.__age = a

	# function to delete _age attribute
	def del_age(self):
		del self.__age
	
	age = property(get_age, set_age, del_age)

mark = Geeks()

mark.age = 10

print(mark.age)
print(mark.__dict__)
print(f'has age property : {hasattr(mark, "age")}')

""" Result
setter method called
getter method called
10
"""