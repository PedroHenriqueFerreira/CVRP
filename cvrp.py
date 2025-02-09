from traceback import print_exc

import numpy as np

class CVRP:
    ''' Class for the Capacitated Vehicle Routing Problem ''' 
    
    def __init__(self, instance_file: str, vehicle_number: int):
        ''' Initialize the CVRPTW instance with the file name '''
        
        self.instance_file = instance_file # Instance file name
        self.vehicle_number = vehicle_number # Number of vehicles
        
        self.dimension = 0 # Number of customers
        self.capacity = 0 # Each vehicle capacity
        self.edge_weight_type = '' # Edge weight type
        self.edge_weight_format = '' # Edge weight format
        self.distances: np.ndarray = None # Distance matrix
        self.positions: list[tuple[int, int]] = [] # Positions list
        self.demands: list[int] = [] # Demands list
        self.depot = 0 # Depot node
        
        self.routes: list[list[int]] = None # Routes list
        
        self.load() # Load the data from the file
    
    def load_instance(self):
        ''' Load an instance from the file '''
        
        with open(self.instance_file, 'r') as file:
            i, j = 1, 0
            section = ''
            
            for l in file.readlines():
                line = l.strip()
                
                if not line:
                    continue
                
                if ':' in line:
                    field, value = line.split(':', 1)
                    field, value = field.strip(), value.strip()
                    
                    match field:
                        case 'TYPE':
                            if value != 'CVRP':
                                raise Exception('Only CVRP instances are supported')
                            
                        case 'DIMENSION':
                            self.dimension = int(value)
                            self.distances = np.zeros((self.dimension, self.dimension), dtype=int)
                            
                        case 'CAPACITY':
                            self.capacity = int(value)
                            
                        case 'EDGE_WEIGHT_TYPE':
                            if value not in ('EUC_2D', 'ATT', 'EXPLICIT'):
                                raise Exception('Only (EUC_2D, ATT, EXPLICIT) edge weight types are supported')
                            
                            self.edge_weight_type = value
                            
                        case 'EDGE_WEIGHT_FORMAT':
                            if value != 'LOWER_COL':
                                raise Exception('Only LOWER_COL edge weight format is supported')
                        
                            self.edge_weight_format = value
                    
                if line.isupper():
                    section = line
                    continue
                
                values = line.split()
                
                match section:            
                    case 'EDGE_WEIGHT_SECTION':
                        for value in values:
                            self.distances[i, j] = self.distances[j, i] = int(value)
                            
                            i += 1
                            if i == self.dimension:
                                i, j = j + 2, j + 1
                        
                    case 'NODE_COORD_SECTION':
                        x, y = float(values[1]), float(values[2])
                        self.positions.append((x, y))
                        
                    case 'DEMAND_SECTION':
                        demand = int(values[1])
                        self.demands.append(demand)

                    case 'DEPOT_SECTION':
                        depot = int(values[0])
                        
                        if depot <= 0:
                            continue
                        
                        if self.depot > 0:
                            raise Exception('Only one depot is supported')
                        
                        self.depot = depot
            
            if len(self.positions) != 0:
                for i in range(self.dimension):
                    for j in range(self.dimension):
                        sdx = (self.positions[i][0] - self.positions[j][0]) ** 2
                        sdy = (self.positions[i][1] - self.positions[j][1]) ** 2
                        
                        distance = 0
                        
                        match self.edge_weight_type:
                            case 'EUC_2D':
                                distance: float = round(np.sqrt(sdx + sdy))
                            
                            case 'ATT':
                                distance: float = round(np.sqrt((sdx + sdy) / 10))
                        
                        self.distances[i, j] = self.distances[j, i] = distance
        
    def clarke_wright(self):
        ''' Load the routes using the Clarke-Wright savings heuristic '''

        # Calculate the savings

        savings: list[tuple[int, int, int]] = []
        
        for i in range(1, self.dimension):
            for j in range(i + 1, self.dimension):
                s = self.distances[i, 0] + self.distances[j, 0] - self.distances[i, j]
                savings.append((s, i, j))
                
        savings.sort(key=lambda x: x[0], reverse=True)
        
        # Initialize the routes
        
        self.routes = [[i] for i in range(1, self.dimension)]
        route_demands = self.demands[1:]
    
        # Combine the routes
        
        for s, i, j in savings:
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
                self.routes[route_i].reverse()
                
            if self.routes[route_j][-1] == j:
                self.routes[route_j].reverse()
            
            if self.routes[route_i][-1] != i or self.routes[route_j][0] != j:
                continue
                
            if route_demands[route_i] + route_demands[route_j] > self.capacity:
                continue
        
            route_demands[route_i] += route_demands[route_j]
            route_demands.pop(route_j)
            
            self.routes[route_i] += self.routes[route_j]
            self.routes.pop(route_j)
            
        # Reduce the number of routes
        
        while len(self.routes) > self.vehicle_number:
            min_route = min(self.routes, key=len)
            
            idx = self.routes.index(min_route)
            
            route_demands.pop(idx)
            self.routes.pop(idx)
            
            for customer in min_route:
                
                customer_added = False
                
                for route in sorted(self.routes, key=lambda r: sum(self.distances[c, 0] for c in r)):
                    idx = self.routes.index(route)
                    
                    if route_demands[idx] + self.demands[customer] > self.capacity:
                        continue
                    
                    route_demands[idx] += self.demands[customer]
                    route += [customer]
                    
                    customer_added = True
                    
                    break
                
                if not customer_added:
                    raise Exception('Cannot add the customer to any route')
    
    def calculate_length(self, route: list[int]):
        ''' Calculate the length for a route '''
        
        length = self.distances[0, route[0]] + self.distances[0, route[-1]]
        for i in range(len(route) - 1):
            length += self.distances[route[i], route[i + 1]]
        
        return length
    
    def two_opt(self):
        for idx, route in enumerate(self.routes):
            best_route = route
            best_route_length = self.calculate_length(route)
            
            improve = True
            while improve:
                improve = False
                for i in range(len(route) - 1):
                    for j in range(i + 1, len(route)):
                        new_route = route[:i] + route[i:j + 1][::-1] + route[j + 1:]
                        new_route_length = self.calculate_length(new_route)

                        if new_route_length < best_route_length:
                            best_route = new_route
                            best_route_length = new_route_length
                            
                            improve = True        
                
                route = best_route
            
            self.routes[idx] = route
        
    def load(self):
        ''' Load the data from the file '''
        
        try:
            self.load_instance()
            self.clarke_wright()
            
            print('BEFORE', sum(self.calculate_length(route) for route in self.routes))
            print('ROUTES', self.routes)
            
            self.two_opt()
            
            print('AFTER', sum(self.calculate_length(route) for route in self.routes))
            print('ROUTES', self.routes)
            
        except Exception:
            print('Error loading the instance file')
            
            print_exc()
            exit(1)