# example: get file size
# reference : https://codippa.com/how-to-check-file-size-in-python-3-ways-to-find-out-size-of-file-in-python/

from os import path, stat, SEEK_END

file_name = './file_size3.py'

# 1) use os.path.getsize()
file_size1 = path.getsize(file_name)
print(f'get file_size #1 (os.path.getsize()) = {file_size1}')

# 2) use os.stat()
file_stat = stat(file_name)
print(f'file_stat = {file_stat}')
file_size2 = file_stat.st_size
print(f'get file_size #2 (os.stat()) = {file_size2}')

# 3) use open(), seek(), tell(), close()
f = open(file_name, 'rb')
f.seek(0, SEEK_END)
file_size3 = f.tell()
print(f'get file_size #3 (seek(), tell()) = {file_size3}')
f.close()

""" Result
get file_size #1 (os.path.getsize()) = 592
file_stat = os.stat_result(st_mode=33206, st_ino=281474976928763, st_dev=2551902280, st_nlink=1, st_uid=0, st_gid=0, st_size=592, st_atime=1652058224, st_mtime=1652058224, st_ctime=1652057736)
get file_size #2 (os.stat()) = 592
get file_size #3 (seek(), tell()) = 592
"""