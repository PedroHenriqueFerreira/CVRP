from sys import argv

from cvrptw import CVRPTW

if __name__ == '__main__':
    if len(argv) < 2:
        print('Usage: python main.py <instance>')
        exit(1)
    
    CVRPTW(argv[1])