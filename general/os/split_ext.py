# split file extension
# make hbesthee@naver.com
# date 2023-10-21

from os import path
from os.path import splitext

file_path = '/path/to/filename.ext'
basename = path.basename(file_path)
dirname = path.dirname(file_path)

print('')
print('')
print(f'{basename=}')
print(f'{dirname=}')
filenames = path.splitext(path.basename(file_path))
print(f'{filenames=}')

print('')
print(f"{splitext('bar')=}")
print(f"{splitext('foo.bar.exe')=}")
print(f"{splitext('/foo/bar.exe')=}")
print(f"{splitext('.cshrc')=}")
print(f"{splitext('/foo/a....jpeg')=}")
print(f"{splitext('/foo/...a.jpeg')=}")
print(f"{splitext('/foo/...a....jpeg')=}")
print(f"{splitext('/foo/....jpeg')=}")
print(f"{splitext('')=}")
# print(f"{splitext(None)=}") # TypeError: expected str, bytes or os.PathLike object, not NoneType

""" RESULT:
basename='filename.ext'
dirname='/path/to'
filenames=('filename', '.ext')

splitext('bar')=('bar', '')
splitext('foo.bar.exe')=('foo.bar', '.exe')
splitext('/foo/bar.exe')=('/foo/bar', '.exe')
splitext('.cshrc')=('.cshrc', '')
splitext('/foo/a....jpeg')=('/foo/a...', '.jpeg')
splitext('/foo/...a.jpeg')=('/foo/...a', '.jpeg')
splitext('/foo/...a....jpeg')=('/foo/...a...', '.jpeg')
splitext('/foo/....jpeg')=('/foo/....jpeg', '')
splitext('')=('', '')
"""
