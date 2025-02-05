from traceback import print_exc

import numpy as np

class Customer:
    ''' Class for the customers data '''
    
    def __init__(self, i: int, x: int, y: int):
        ''' Initialize the customer data '''
        
        self.i = i # Customer number
        self.x = x # X coordinate
        self.y = y # Y coordinate
        
        self.demand = 0 # Demand
        
        self.depot = False # Depot flag

class CVRP:
    ''' Class for the Capacitated Vehicle Routing Problem ''' 
    
    def __init__(self, instance_file: str, vehicle_number: int):
        ''' Initialize the CVRPTW instance with the file name '''
        
        self.instance_file = instance_file # Instance file name
        self.vehicle_number = vehicle_number # Number of vehicles
        
        self.vehicle_capacity = 0 # Each vehicle capacity
        
        self.customers: list[Customer] = [] # Customers data
        
        self.distances: np.ndarray[np.int32] = np.array([]) # Distance matrix
        
        self.routes: list[list[int]] = [] # Routes list
        
        self.load() # Load the data from the file
    
    def load_instance(self):
        ''' Load an instance from the file '''
        
        with open(self.instance_file, 'r') as file:
            section = ''
            
            for line in file.readlines():
                values = line.split()
                
                if not values:
                    continue
                
                match values[0]:
                    case 'CAPACITY':
                        self.vehicle_capacity = int(values[-1])
                        continue
                    
                    case 'EDGE_WEIGHT_TYPE':
                        if values[-1] == 'EUC_2D':
                            continue
                        
                        raise Exception('Only EUC_2D edge weight type is supported')
                
                if not values[0].isdigit():
                    section = values[0]
                    continue
                
                match section:
                    case 'NODE_COORD_SECTION':
                        i, x, y = map(int, values)
                        self.customers.append(Customer(i, x, y))
                        
                    case 'DEMAND_SECTION':
                        i, demand = map(int, values)
                        self.customers[i - 1].demand = demand 

                    case 'DEPOT_SECTION':
                        i = int(values[0])
                        self.customers[i - 1].depot = True
            
    def load_distances(self):
        ''' Load a distance matrix from customers data '''
        
        self.distances = np.zeros((len(self.customers), len(self.customers)), dtype=int)
        
        for i in range(len(self.customers)):
            for j in range(i + 1, len(self.customers)):
                delta_x = self.customers[i].x - self.customers[j].x
                delta_y = self.customers[i].y - self.customers[j].y
                
                self.distances[i][j] = self.distances[j][i] = round(np.linalg.norm((delta_x, delta_y)))
              
    def capacity_constraint(self, route: list[int]):
        ''' Check the capacity constraint for a route '''
        
        return sum(self.customers[c - 1].demand for c in route) <= self.vehicle_capacity
               
    def load_routes(self):
        ''' Load the routes using the Clarke-Wright savings heuristic '''
        
        # Calculate the savings
        
        savings: list[tuple[int, int, int]] = []
        
        for i in range(1, len(self.customers)):
            for j in range(i + 1, len(self.customers)):
                s = self.distances[i, 0] + self.distances[j, 0] - self.distances[i, j]
                savings.append((s, i, j))
                
        savings.sort(key=lambda x: x[0], reverse=True)
        
        # Initialize the routes
        
        routes = [[c.i] for c in self.customers[1:]]
        
        # Combine the routes
        
        for s, i, j in savings:
            if s < 0:
                continue
            
            route_i = route_j = None
            for k, route in enumerate(routes):
                if i in route:
                    route_i = k
                if j in route:
                    route_j = k
            
            if not route_i or not route_j or route_i == route_j:
                continue
            
            if routes[route_i][0] != i and routes[route_i][-1] != i:
                continue
                
            if routes[route_j][0] != j and routes[route_j][-1] != j:
                continue
            
            if routes[route_i][0] == i:
                routes[route_i].reverse()
                
            if routes[route_j][-1] == j:
                routes[route_j].reverse()
                
            combined_route = routes[route_i] + routes[route_j]
            
            if not self.capacity_constraint(combined_route):
                continue
        
            routes[route_i] = combined_route
            routes.pop(route_j)
            
        # Reduce the number of routes
        while len(routes) > self.vehicle_number:
            min_route = min(routes, key=len)
            routes.remove(min_route)
            
            for customer in min_route:
                sorted_routes = sorted(routes, key=lambda r: sum(self.distances[c - 1][0] for c in r))
                
                breaked = False
                
                for route in sorted_routes:
                    if not self.capacity_constraint(route + [customer]):
                        continue
                
                    route.append(customer)
                    breaked = True
                    break
                
                if not breaked:
                    raise Exception('Cannot add the customer to any route')

        self.routes = routes
        
    def load(self):
        ''' Load the data from the file '''
        
        try:
            self.load_instance()
            self.load_distances()  
            self.load_routes()
            
        except Exception:
            print('Error loading the instance file')
            
            print_exc()
            exit(1)