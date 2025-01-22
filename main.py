from sys import argv

from cvrptw import CVRPTW
from solver import Solver

if __name__ == '__main__':
    if len(argv) < 2:
        print('Usage: python main.py <instance>')
        exit(1)
    
    Solver(CVRPTW(argv[1])).solve()