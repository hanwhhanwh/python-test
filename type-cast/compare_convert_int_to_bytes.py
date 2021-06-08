import timeit

result = timeit.timeit('struct.pack("<H", 25525)', setup='import struct', number=3000000)
print('case 1', result)
result = timeit.timeit('(25525).to_bytes(2, byteorder="little")', number=3000000)
print('case 2', result)
result = timeit.timeit('struct.pack("<I", 25525)', setup='import struct', number=3000000)
print('case 3', result)
result = timeit.timeit('(25525).to_bytes(4, byteorder="little")', number=3000000)
print('case 4', result)
result = timeit.timeit('struct.pack("<Q", 255252552525525)', setup='import struct', number=3000000)
print('case 5', result)
result = timeit.timeit('(255252552525525).to_bytes(8, byteorder="little")', number=3000000)
print('case 6', result)

""" result ===>>>
case 1 0.24562080000000003
case 2 0.29117760000000004
case 3 0.2068852
case 4 0.33815569999999995
case 5 0.29757940000000005
case 6 0.34646350000000004
"""