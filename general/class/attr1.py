a = object()
"""
a.recording_path = './video'
Traceback (most recent call last):
  File "<pyshell#2>", line 1, in <module>
    a.recording_path = './video'
AttributeError: 'object' object has no attribute 'recording_path'
"""
"""
a['recording_path'] = './video'
Traceback (most recent call last):
  File "<pyshell#3>", line 1, in <module>
    a['recording_path'] = './video'
TypeError: 'object' object does not support item assignment
"""
print(a) # <object object at 0x000002D98B118E10>


class A:
	pass

a = A()
a.recording_path = './video'
print(a) # <__main__.A object at 0x000002D98D738190>
print(a.recording_path) # './video'


class B(object):
	pass

b = B()
b.recording_path = './video'
print(b) # <__main__.B object at 0x000002D98D738370>
print(b.recording_path) # './video'
"""
b['recording_path'] = './video'
Traceback (most recent call last):
  File "<pyshell#26>", line 1, in <module>
    b['recording_path'] = './video'
TypeError: 'B' object does not support item assignment
"""
print(b.__getattribute__('recording_path')) # './video'
"""
print(b.__getattribute__('recording_path1'))
Traceback (most recent call last):
  File "<pyshell#28>", line 1, in <module>
    b.__getattribute__('recording_path1')
AttributeError: 'B' object has no attribute 'recording_path1'
"""
print(hasattr(b, 'recording_path')) # True
print(hasattr(b, 'recording_path1')) # False

"""
help(hasattr)
Help on built-in function hasattr in module builtins:

hasattr(obj, name, /)
    Return whether the object has an attribute with the given name.
    
    This is done by calling getattr(obj, name) and catching AttributeError.
"""

""" 전체 실행결과
<object object at 0x000002107C3A81D0>
<__main__.A object at 0x000002107C8E2FD0>
./video
<__main__.B object at 0x000002107C8E2F70>
./video
./video
True
False
"""