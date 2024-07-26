# NumPy mean example
# make hbesthee@naver.com
# date 2022-10-01
import numpy as np

# 2차원 배열 생성
arr2d = np.array([[1, 2, 3], 
                [4, 5, 6], 
                [7, 8, 9]])

print(arr2d)
# [[1 2 3]
#  [4 5 6]
#  [7 8 9]]

# 열의 평균 계산 - axis=0
col_means = arr2d.mean(axis = 0)

print(col_means)
#[4. 5. 6.]

# 행의 평균 계산 - axis=1
row_means = arr2d.mean(axis = 1)
print(row_means)
# [2. 5. 8.]
