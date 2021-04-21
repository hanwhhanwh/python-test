# reference : https://python.flowdas.com/library/multiprocessing.html
from multiprocessing import current_process, Process, Value, Array

double_value = 0
num_array = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

def f(n, a):
    global double_value
    global num_array

    double_value = 3.1415927
    num_array = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]

    n.value = 3.1415927
    for i in range(len(a)):
        a[i] = -a[i]

    print(current_process().name)

if __name__ == '__main__':
    print(current_process().name)

    num = Value('d', 0.0)
    arr = Array('i', range(10))

    p = Process(target=f, args=(num, arr))
    p.start()
    p.join()

    print(double_value)
    print(num_array)

    print(num.value)
    print(arr[:])
