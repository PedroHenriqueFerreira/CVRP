from sys import argv

from cvrp import CVRP, ClarkeWright, TwoOpt

if __name__ == '__main__':
    if len(argv) < 4:
        print('Usage: python main.py <instance> <vehicle_number> <neighbor_number>')
        exit(1)
    
    cvrp = CVRP(argv[1], int(argv[2]), int(argv[3])).load()
    
    routes = ClarkeWright(cvrp).run()
    
    print('CW:', sum(route.cost() for route in routes))
    
    routes = TwoOpt(routes).run()
    
    print('2OPT:', sum(route.cost() for route in routes))
    
    