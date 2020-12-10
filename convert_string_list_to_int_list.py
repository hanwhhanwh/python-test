# Ref : https://stackoverflow.com/questions/7368789/

str_list = ['1', '2', '3']

#int_list = [1, 2, 3]

int_list = list(map(int, str_list)) # 있어 보임
print(int_list)

int_list = [int(i) for i in str_list] # 직관적
print(int_list)

pts1 = []
pts1.append(int_list)
pts1.append(int_list)
print(pts1)