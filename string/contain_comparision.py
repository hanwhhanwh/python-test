import timeit


result = timeit.timeit("""
class_id = 8
is_person = (class_id == 1) or (class_id == 2) or (class_id == 3) or (class_id == 4) or (class_id == 5) or (class_id == 6) or (class_id == 7)
""", number=3000000)
print('if = ', result)

result = timeit.timeit("""
class_id = 8
classes = [1 ,2,3,4,5,6]
is_person = (class_id in classes)
""", number=3000000)
print('list in = ', result)

result = timeit.timeit("""
class_id = 8
person_class_id_strings = ',1,2,3,4,5,6,'
is_person = person_class_id_strings.find(f',{class_id},')
""", number=3000000)
print('string find = ', result)

result = timeit.timeit("""
class_id = 8
person_class_id_strings = ',1,2,3,4,5,6,'
is_person = f',{class_id},' in person_class_id_strings
""", number=3000000)
print('string in = ', result)

""" Result
if =  0.3295459
list in =  0.32562700000000006
string find =  0.8498899
string in =  0.4576339999999999
"""