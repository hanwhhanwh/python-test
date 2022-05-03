import cv2
import numpy as np

polygon = np.array([0,0,640,0,640,480,0,480], dtype=np.int32)
print(f'polygon = {polygon}')

polygon1 = polygon.reshape(4,2)
print(f'polygon1 = {polygon1}')
print(f'polygon1.reshape(-1) = {polygon1.reshape(-1)}')

polygon2 = polygon.reshape((-1,1,2)).astype(np.int32)
print(f'polpolygon2ygon = {polygon2}')
result = cv2.pointPolygonTest(polygon2, (10, 47), True)
print(f'result = {result}')
