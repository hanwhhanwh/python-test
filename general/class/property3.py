# reference : https://www.geeksforgeeks.org/getter-and-setter-in-python/

# Python program showing the use of
# @property

class Geeks:
	def __init__(self):
		self._age = 0
	
	# using property decorator
	# a getter function
	@property
	def age(self):
		print("getter method called")
		return self._age
	
	# a setter function
	@age.setter
	def age_setter(self, a):
		if(a < 18):
			raise ValueError("Sorry you age is below eligibility criteria")
		print("setter method called")
		self._age = a

	# a deleter function
	@age.deleter
	def age(self, a):
		del self._age

mark = Geeks()

mark.age = 19

print(mark.age)

""" Result
setter method called
getter method called
19
"""