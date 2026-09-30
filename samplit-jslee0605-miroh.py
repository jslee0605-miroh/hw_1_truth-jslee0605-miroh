import sys
import random

PATH = sys.argv[1]
print("File Path:", PATH)
with open(PATH, 'r', encoding='utf-8') as file:
    for i, line in enumerate(file):
        random_number = random.random()
        if random_number < 0.01:
            print(line.strip())