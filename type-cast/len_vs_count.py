import array
import struct


print('len() function example')
array1 = array.array('i', [123, 3423, 252, 3245, 2134, 123, 4653, 123])
print('len1 = ', len(array1))

bytes2 = struct.pack('IIIIIIII', 123, 3423, 252, 3245, 2134, 123, 4653, 123)
print('bytes = ', bytes2)
print('len2 = ', len(bytes2))

bytesarray3 = bytearray(bytes2)
print('bytesarray = ', bytesarray3)
print('len3 = ', len(bytesarray3))
bytesarray3.extend(b'{\x00\x00\x00')
print('len4 = ', len(bytesarray3))
bytes4 = bytes(bytesarray3)
print('bytes4 = ', bytes4)
# bytes4.extend(b'{\x00\x00\x00')
# AttributeError: 'bytes' object has no attribute 'extend'
""" result =>
len() function example
len1 =  8
bytes =  b'{\x00\x00\x00_\r\x00\x00\xfc\x00\x00\x00\xad\x0c\x00\x00V\x08\x00\x00{\x00\x00\x00-\x12\x00\x00{\x00\x00\x00'
len2 =  32
bytesarray =  bytearray(b'{\x00\x00\x00_\r\x00\x00\xfc\x00\x00\x00\xad\x0c\x00\x00V\x08\x00\x00{\x00\x00\x00-\x12\x00\x00{\x00\x00\x00')
len3 =  32
len4 =  36
bytes4 =  b'{\x00\x00\x00_\r\x00\x00\xfc\x00\x00\x00\xad\x0c\x00\x00V\x08\x00\x00{\x00\x00\x00-\x12\x00\x00{\x00\x00\x00{\x00\x00\x00'
"""

print('count() method example')
array1 = array.array('i', [123, 3423, 252, 3245, 2134, 123, 4653, 123])
print('count1 = ', array1.count( 123 ))

bytes2 = struct.pack('IIIIIIII', 123, 3423, 252, 3245, 2134, 123, 4653, 123)
print('bytes = ', bytes2)
print('count2 = ', bytes2.count( b'{\x00\x00\x00' ))

bytesarray3 = bytearray(bytes2)
print('bytesarray = ', bytesarray3)
print('count3 = ', bytesarray3.count( b'{\x00\x00\x00' ))
bytesarray3.extend(b'{\x00\x00\x00')
print('count4 = ', bytesarray3.count( b'{\x00\x00\x00' ))
""" result =>
count() method example
count1 =  3
bytes =  b'{\x00\x00\x00_\r\x00\x00\xfc\x00\x00\x00\xad\x0c\x00\x00V\x08\x00\x00{\x00\x00\x00-\x12\x00\x00{\x00\x00\x00'
count2 =  3
bytesarray =  bytearray(b'{\x00\x00\x00_\r\x00\x00\xfc\x00\x00\x00\xad\x0c\x00\x00V\x08\x00\x00{\x00\x00\x00-\x12\x00\x00{\x00\x00\x00')
count3 =  3
count4 =  4
"""
