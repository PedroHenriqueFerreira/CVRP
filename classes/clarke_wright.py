from classes.instance import Instance
from classes.route import Route
from classes.utils import timer

class ClarkeWright:
    ''' Class for the Clarke-Wright savings heuristic '''
    
    def __init__(self, cvrp: Instance):
        self.cvrp = cvrp # CVRP instance
        
        self.savings: list[tuple[int, int, int]] = []
        self.routes: list[Route] = []
    
    def load_savings(self):
        ''' Load the savings for the CVRP instance '''
        
        for i in range(1, self.cvrp.dimension):
            for j in range(i + 1, self.cvrp.dimension):
                s = self.cvrp.distances[i, 0] + self.cvrp.distances[j, 0] - self.cvrp.distances[i, j]
                
                self.savings.append((s, i, j))
                
        self.savings.sort(key=lambda x: x[0], reverse=True)
    
    def load_routes(self):
        ''' Load initial routes '''
        
        for c in range(1, self.cvrp.dimension):
            self.routes.append(Route(self.cvrp, [c]))

    def combine_routes(self):
        ''' Combine the routes '''
        
        for s, i, j in self.savings:
            if s < 0:
                continue
            
            route_i = route_j = None
            for k, route in enumerate(self.routes):
                if i in route:
                    route_i = k
                if j in route:
                    route_j = k
            
            if not route_i or not route_j or route_i == route_j:
                continue
            
            if self.routes[route_i][0] == i:
                self.routes[route_i] = self.routes[route_i].reverse()
                
            if self.routes[route_j][-1] == j:
                self.routes[route_j] = self.routes[route_j].reverse()
            
            if self.routes[route_i][-1] != i or self.routes[route_j][0] != j:
                continue
                
            new_route = Route.merge(self.routes[route_i], self.routes[route_j])
                
            if new_route.demand() > self.cvrp.capacity:
                continue
                
            self.routes[route_i] = new_route
            self.routes.pop(route_j)
        
    def reduce_routes(self):
        ''' Reduce the number of routes '''
        
        while len(self.routes) > self.cvrp.vehicle_number:
            min_route = min(self.routes, key=len)
            self.routes.remove(min_route)
            
            for customer in min_route:
                customer_added = False
                
                for route in sorted(self.routes, key=lambda r: sum(self.cvrp.distances[c, 0] for c in r)):
                    new_route = Route.merge(route, [customer])
                    
                    if new_route.demand() > self.cvrp.capacity:
                        continue
                    
                    self.routes[self.routes.index(route)] = new_route
                    
                    customer_added = True
                    
                    break
                
                if not customer_added:
                    raise Exception('Cannot add the customer to any route')
        
    @timer
    def run(self):
        ''' Run the Clarke-Wright savings heuristic '''
        
        self.load_savings()
        self.load_routes()
        
        self.combine_routes()
        self.reduce_routes()
        
        return self.routes