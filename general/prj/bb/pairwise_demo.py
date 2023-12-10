# itertools.pairwise sample
# make hbesthee@naver.com
# date 2023-12-01

# reference: https://docs.python.org/3/library/itertools.html
from itertools import pairwise

#from itertools import tee
#def pairwise(iterable):
#	"s -> (s0,s1), (s1,s2), (s2, s3), ..."
#	a, b = tee(iterable)
#	next(b, None)
#	return zip(a, b)

class Element:
	@staticmethod
	def link_many(*args):
		'''
		@raises: Gst.LinkError
		'''
		for pair in pairwise(args):
			print(f'pairwise to link {pair[0]} and {pair[1]}')

Element.link_many(1, 2, 3, 4, 5)

""" Result ==>
pairwise to link 1 and 2
pairwise to link 2 and 3
pairwise to link 3 and 4
pairwise to link 4 and 5
"""