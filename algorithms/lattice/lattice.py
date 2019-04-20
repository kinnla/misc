from math import *
from random import *
import numpy as np

points = [np.array([random(), random(), random(), random()]) for _ in range(24)]

done = False
while not done:
	done = True
	# shuffle(points)
	for i in range(len(points)):
		for j in range(len(points)):
			if i == j:
				continue
			dist = np.linalg.norm(points[i] - points[j])
			if dist < 0.90:
				points[i] = points[j] + (points[i] - points[j]) * 2/(1+dist)
				done = False
				print(i)
			
		points[i] /= np.linalg.norm(points[i])

print(points)
for i in range(len(points)):
	n=0
	for j in range(len(points)):
		if np.linalg.norm(points[i] - points[j])<1.1:
			n+=1
	print(n)
	

		