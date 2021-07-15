import io
import random
import timeit

# nums = bytearray()
# for i in range(0, 10000):
# 	nums.append(random.randint(0, 255))

result = timeit.timeit("""
chars = bytes(100)
buf = io.StringIO()
for ch in chars:
	buf.write(f'{ch:02x} ')
result = buf.getvalue().encode()
""", setup='import io', number=3000)
print('case: StringIO = ', result)

result = timeit.timeit("""
import io
chars = bytes(100)
str = ''
for ch in chars:
	str = str + (f'{ch:02x} ')
""", setup='import io', number=3000)
print('case: concat = ', result)

result = timeit.timeit("""
chars = bytes(100)
buf = io.StringIO()
for ch in chars:
	buf.write(hex(ch)[::2] + ' ')
result = buf.getvalue().encode()
""", setup='import io', number=3000)
print('case: StringIO2 = ', result)

result = timeit.timeit("""
import io
chars = bytes(100)
str = ''
for ch in chars:
	str = str + hex(ch)[::2] + ' '
""", setup='import io', number=3000)
print('case: concat2 = ', result)

result = timeit.timeit("""
chars = bytes(1000)
buf = io.StringIO()
for ch in chars:
	buf.write(f'{ch:02x} ')
result = buf.getvalue().encode()
""", setup='import io', number=3000)
print('case: StringIO (1000) = ', result)

result = timeit.timeit("""
import io
chars = bytes(1000)
str = ''
for ch in chars:
	str = str + (f'{ch:02x} ')
""", setup='import io', number=3000)
print('case: concat (1000) = ', result)

result = timeit.timeit("""
chars = bytes(1000)
buf = io.StringIO()
for ch in chars:
	buf.write(hex(ch)[::2] + ' ')
result = buf.getvalue().encode()
""", setup='import io', number=3000)
print('case: StringIO2 (1000) = ', result)

result = timeit.timeit("""
import io
chars = bytes(1000)
str = ''
for ch in chars:
	str = str + hex(ch)[::2] + ' '
""", setup='import io', number=3000)
print('case: concat2 (1000) = ', result)

""" Result >>
case: StringIO =  0.11835769999999998
case: concat =  0.10875280000000001
case: concat2 =  0.07193460000000002
case: StringIO (1000) =  0.8746784
case: concat (1000) =  1.3081631
case: concat2 (1000) =  1.3454913
"""

