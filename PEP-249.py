"""
PEP-249 example

RESULT >>
1
(1,)
[1]
[1]
"""

addr_no = 1
not_tuple_param = (addr_no)
print(not_tuple_param)
tuple_param = (addr_no, )
print(tuple_param)

list_param1 = [addr_no]
print(list_param1)
list_param2 = [addr_no, ]
print(list_param2)
