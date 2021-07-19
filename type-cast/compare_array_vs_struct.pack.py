import timeit

result = timeit.timeit("""
buf = []
buf.append(3)
buf.append(0x4d)
buf.append(0x01)
buf.append(0x60)

buf.append(0x11)
buf.append(0x00)
buf.append(0x00)
buf.append(0x00)

buf.append(0x00)
buf.append(0x00)
buf.append(0x00)
buf.append(0x00)

buf.append(0x00)
buf.append(0x00)
buf.append(0x00)
buf.append(0x00)

buf.append(0x00)
buf.append(0x00)
buf.append(0x00)
buf.append(0x00)

buf.append(0x00)
buf.append(0x00)
buf.append(0x00)
buf.append(0x00)

buf.append(0x00)
bytes1 = bytes(buf)
""", number=3000000)
print('case: array = ', result)

result = timeit.timeit("""
bytes2 = struct.pack("IIIIIIb", 0x01604d03, 0x00000011
		, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00)
""", setup='import struct', number=3000000)
print('case: struct.pack() = ', result)

""" result =>
case: array =  3.9553350999999997
case: struct.pack() =  0.4339967000000007
"""
