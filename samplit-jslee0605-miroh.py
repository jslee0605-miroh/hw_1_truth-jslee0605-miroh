import sys
import random

PATH = sys.argv[1]

with open(PATH, 'r') as file:
    for line in file:
        random_number = random.random()
        if random_number < 0.01:
            print(line.strip())