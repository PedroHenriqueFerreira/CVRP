from sys import argv

from classes import Instance, ClarkeWright, TwoOpt, KNeighbors, Solver

if __name__ == '__main__':
    if len(argv) < 5:
        print('Usage: python main.py <instance> <vehicle_number> <neighbor_number> <solver_name>')
        print('Example: python main.py instances/eil22.vrp 4 5 naps')
        exit(1)
    
    cvrp = Instance(argv[1], int(argv[2]), int(argv[3]), argv[4]).load()
    
    cw_time, routes = ClarkeWright(cvrp).run()
    to_time, routes = TwoOpt(routes).run()
    
    kn_time, matrices = KNeighbors(cvrp, routes).run()
    
    print('-' * 80)
    
    print('BEFORE SOLVER \n')
    
    print('ROUTES', [route.route for route in routes])
    print('DEMAND', [route.demand() for route in routes])
    print('COST', sum([route.cost() for route in routes]))
    
    print('-' * 80)
    
    print('AFTER SOLVER \n')
    
    solver_time, solver_cost, solver_result = Solver(cvrp, matrices).run()
    
    print('RESULT', solver_result)
    print('OPTIMUM', solver_cost)
    
    print('-' * 80)
    
    print('TIMES \n')
    
    print('CLARKE-WRIGHT:', cw_time)
    print('TWO-OPT:', to_time)
    print('K-NEIGHBORS:', kn_time)
    print('SOLVER:', solver_time)
    
    print()
    
    print('TOTAL:', cw_time + to_time + kn_time + solver_time)