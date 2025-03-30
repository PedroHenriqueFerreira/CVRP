from sys import argv

from classes import Instance, ClarkeWright, TwoOpt, KNeighbors, Solver

if __name__ == '__main__':
    if len(argv) < 5:
        print('Usage: python main.py <instance> <vehicle_number> <neighbor_number> <solver_name>')
        print('Example: python main.py instances/P/P-n16-k8.vrp 8 5 clasp')
        exit(1)
        
    cvrp = Instance(argv[1]).load()
    
    cw_time, routes = ClarkeWright.run(cvrp, int(argv[2]))
    
    print('CW', cw_time, sum(route.cost for route in routes.values()), list(routes.values()))
    
    to_time, routes = TwoOpt.run(routes)
    
    print('TO', to_time, sum(route.cost for route in routes.values()), list(routes.values()))
     
    kn_time, matrices = KNeighbors.run(cvrp, int(argv[3]), routes)
    
    print('KN', kn_time)
    
    print('-' * 50)
    
    solver_time, solver_cost, solver_routes = Solver.run(cvrp, argv[4], matrices)
    
    print('SOLVER', solver_time, solver_cost, solver_routes)
    
    # print('-' * 80)
    
    # print('TIMES \n')
    
    # print('CLARKE-WRIGHT:', cw_time)
    # print('TWO-OPT:', to_time)
    # print('K-NEIGHBORS:', kn_time)
    # print('SOLVER:', solver_time)
    
    # print()
    
    # print('TOTAL:', cw_time + to_time + kn_time + solver_time)