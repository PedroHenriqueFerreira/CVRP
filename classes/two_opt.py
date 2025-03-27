from classes.route import Route
from classes.utils import timer

class TwoOpt:
    ''' Class for the 2-opt heuristic '''
    
    def __init__(self, routes: list[Route]):
        self.routes = routes # Routes list

    def improve_routes(self):
        ''' Improve the routes '''
        
        for idx, route in enumerate(self.routes):
            best_route = route
            best_route_cost = route.cost
            
            improve = True
            while improve:
                improve = False
                for i in range(len(route) - 1):
                    for j in range(i + 1, len(route)):
                        new_route = route.reverse(i, j + 1)
                        
                        new_route_cost = new_route.cost

                        if new_route_cost < best_route_cost:
                            best_route = new_route
                            best_route_cost = new_route_cost
                            
                            improve = True        
                
                route = best_route

            self.routes[idx] = route

    @timer
    def run(self):
        ''' Run the 2-opt heuristic '''
        
        self.improve_routes()
    
        return self.routes