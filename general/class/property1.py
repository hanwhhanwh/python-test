# reference : https://www.geeksforgeeks.org/getter-and-setter-in-python/

# Python program showing a use
# of get() and set() method in
# normal function

class Geek:
	def __init__(self, age = 0):
		self.__age = age
	
	# getter method
	def get_age(self):
		return self.__age
	
	# setter method
	def set_age(self, x):
		self.__age = x

raj = Geek()

# setting the age using setter
raj.set_age(21)

# retrieving age using getter
print(raj.get_age())

print(raj._Geek__age)
""" Result
21
21
"""