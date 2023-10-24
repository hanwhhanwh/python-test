# split file extension
# make hbesthee@naver.com
# date 2023-10-21

from os.path import splitext

print(f"{splitext('bar')=}")
print(f"{splitext('foo.bar.exe')=}")
print(f"{splitext('/foo/bar.exe')=}")
print(f"{splitext('.cshrc')=}")
print(f"{splitext('/foo/....jepg')=}")
print(f"{splitext('/foo/...a.jepg')=}")
print(f"{splitext('/foo/...a....jepg')=}")
print(f"{splitext('/foo/a....jepg')=}")
print(f"{splitext('')=}")
print(f"{splitext(None)=}")
