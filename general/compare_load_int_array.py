# comparision load int array

import timeit

setup = """
import numpy as np
import os
import struct

# index has 18000 int32
video_file_name = 'cam-20220503_1255.mp4'

video_index_file = open(f'{video_file_name}.idx', 'rb')
video_index_file.seek(0, os.SEEK_END)
file_size = video_index_file.tell()
total_frame_count = int(file_size / 4)
"""

result1 = timeit.timeit("""
video_index_file.seek(0, 0)

frame_index_list = list()
frame_count = 0
for index in range(total_frame_count):
	frame_index_bytes = video_index_file.read(4)
	if (frame_index_bytes == None):
		break
	(frame_index, ) = struct.unpack('=i', frame_index_bytes)
	frame_index_list.append(frame_index)
	frame_count += 1
""", setup = setup, number = 3000)


result2 = timeit.timeit("""
video_index_file.seek(0, 0)
data_bytes = video_index_file.read()
frame_list = struct.unpack(f'={total_frame_count}i', data_bytes)
""", setup = setup, number = 3000)

result3 = timeit.timeit("""
video_index_file.seek(0, 0)
data_bytes = video_index_file.read()
frame_list = np.frombuffer(data_bytes, np.int32)
""", setup = setup, number = 3000)

print(f'result1 = {result1}')
print(f'result2 = {result2}')
print(f'result3 = {result3}')

""" result
result1 = 11.304136499999998
result2 = 0.5849311000000004
result3 = 0.05164079999999949
"""