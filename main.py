from sys import argv

from cvrp import CVRP

if __name__ == '__main__':
    if len(argv) < 3:
        print('Usage: python main.py <instance> <vehicle_number>')
        exit(1)
    
    CVRP(argv[1], int(argv[2]))