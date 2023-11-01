import random


def gen_plate(mean, multiplication_factor, variance):
    LETTERS = 'ABCDEFGHIJKLMNOP'
    plate = ''
    for row in range(16):
        plate += LETTERS[row] + ','
        for col in range(24):
            plate += str(int(random.gauss(mean + (row * multiplication_factor) + (col * multiplication_factor), variance)))
            plate += ','
        plate += '\n'
    return plate