list1 = [34, 46, 58, 56, 22, 62, 34, 97, 57]

print(list1[0:3])
print(list1[3:6])
print(list1[6:9])

print(list1[-2:])
print(list1[7:])
print(list1[:-2])


for index in list1:
	print(index)

print('----')
# for문 내에서 index 값을 변경하여도 원래 지정한 range 범위 순서를 벗어나지 않음을 보장함
for index in range(0, len(list1)):
	print(f'index = {index} / list1[index] = {list1[index]}')
	index = index + 3
	print(f'changed index = {index}')

del(list1[0])
print(f'list1 = {list1}')