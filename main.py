from sys import argv

from cvrp import Instance, ClarkeWright, TwoOpt, KNeighbors, Solver

if __name__ == '__main__':
    if len(argv) < 4:
        print('Usage: python main.py <instance> <vehicle_number> <neighbor_number>')
        exit(1)
    
    cvrp = Instance(argv[1], int(argv[2]), int(argv[3])).load()
    
    routes = ClarkeWright(cvrp).run()
    routes = TwoOpt(routes).run()
    
    matrices = KNeighbors(cvrp, routes).run()
    routes = Solver(cvrp, matrices).run()
    
    print(routes)