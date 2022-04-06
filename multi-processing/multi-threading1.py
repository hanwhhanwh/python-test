import threading

double_value = 0
num_array = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

def sum(start, end):
	global double_value
	global num_array

	double_value = 3.1415927
	num_array = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]

	total = 0
	for i in range(start, end):
		total += i
	print(f"Subthread total = {total}")


if __name__ == '__main__':
	thread = threading.Thread(target=sum, args=(1, 100000))
	thread.start()
	
	print(f"Main Thread : double_value = {double_value}")
	print(f"Main Thread : num_array = {num_array}")
