# author : hbesthee@naver.com
# date : 2023-01-16
# reference : https://www.geeksforgeeks.org/python-program-for-binary-search/

# Iterative Binary Search Function
# It returns index of target in given number array num_arr if present,
# else insert index for target
def binary_search(num_arr, target):
	low = 0
	high = len(num_arr) - 1
	mid = 0

	while low <= high:

		mid = (high + low) // 2

		# If x is greater, ignore left half
		if num_arr[mid] < target:
			low = mid + 1

		# If x is smaller, ignore right half
		elif num_arr[mid] > target:
			high = mid - 1

		# means x is present at mid
		else:
			return mid, True

	# If we reach here, then the element was not present
	return low, False



if __name__ == '__main__':
	arr = [1, 3, 5, 8, 11, 15, 19, 24, 55, 77, 99]
	check_arr = [5, 77, 32, 4, 101, 90, 16, 120, 66, 88, 99]

	for item in check_arr:
		index, exists = binary_search(arr, item)
		print((index, exists))
		if (not exists):
			arr.insert(index, item)
			print(arr)

""" Run Result
(2, True)
(9, True)
(8, False)
[1, 3, 5, 8, 11, 15, 19, 24, 32, 55, 77, 99]
(2, False)
[1, 3, 4, 5, 8, 11, 15, 19, 24, 32, 55, 77, 99]
(13, False)
[1, 3, 4, 5, 8, 11, 15, 19, 24, 32, 55, 77, 99, 101]
(12, False)
[1, 3, 4, 5, 8, 11, 15, 19, 24, 32, 55, 77, 90, 99, 101]
(7, False)
[1, 3, 4, 5, 8, 11, 15, 16, 19, 24, 32, 55, 77, 90, 99, 101]
(16, False)
[1, 3, 4, 5, 8, 11, 15, 16, 19, 24, 32, 55, 77, 90, 99, 101, 120]
(12, False)
[1, 3, 4, 5, 8, 11, 15, 16, 19, 24, 32, 55, 66, 77, 90, 99, 101, 120]
(14, False)
[1, 3, 4, 5, 8, 11, 15, 16, 19, 24, 32, 55, 66, 77, 88, 90, 99, 101, 120]
(16, True)
"""