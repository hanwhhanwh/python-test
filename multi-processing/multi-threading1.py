import threading

double_value = 0
num_array = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

def sum(s, e):
    global double_value
    global num_array

    double_value = 3.1415927
    num_array = [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]

    total = 0
    for i in range(s, e):
        total += i
    print("Subthread", total)


if __name__ == '__main__':
    t = threading.Thread(target=sum, args=(1, 100000))
    t.start()

    print("Main Thread")
    
    print(double_value)
    print(num_array)
