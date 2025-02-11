import numpy as np
from networkx import minimum_spanning_tree, Graph

class CVRP:
    ''' Class for the Capacitated Vehicle Routing Problem ''' 
    
    def __init__(self, instance_file: str, vehicle_number: int, neighbor_number: int):
        ''' Initialize the CVRPTW instance with the file name '''
        
        self.instance_file = instance_file # Instance file name
        self.vehicle_number = vehicle_number # Number of vehicles
        self.neighbor_number = neighbor_number # Number of neighbors
        
        self.dimension = 0 # Number of customers
        self.capacity = 0 # Each vehicle capacity
        
        self.edge_weight_type = '' # Edge weight type
        self.edge_weight_format = '' # Edge weight format
        
        self.distances: np.ndarray = None # Distance matrix
        
        self.positions: list[tuple[int, int]] = [] # Positions list
        self.demands: list[int] = [] # Demands list
        
        self.depot = 0 # Depot node
        
        # Auxiliary variables
        self.section = '' # Section name
        self.i, self.j = 1, 0 # Indexes
    
    def load_field(self, line: str):
        ''' Load a field from the line '''
        
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
    
    def load_section(self, line: str):
        ''' Load a section from the line '''
            
        values = line.split()
                
        match self.section:            
            case 'EDGE_WEIGHT_SECTION':
                for value in values:
                    self.distances[self.i, self.j] = self.distances[self.j, self.i] = int(value)
                    
                    self.i += 1
                    if self.i == self.dimension:
                        self.i, self.j = self.j + 2, self.j + 1
                
            case 'NODE_COORD_SECTION':
                x, y = float(values[1]), float(values[2])
                self.positions.append((x, y))
                
            case 'DEMAND_SECTION':
                demand = int(values[1])
                self.demands.append(demand)

            case 'DEPOT_SECTION':
                depot = int(values[0])
                
                if depot > 0:
                    if self.depot > 0:
                        raise Exception('Only one depot is supported')
                    
                    self.depot = depot
    
    def load_distances(self):
        ''' Load the distances for the CVRP instance '''
        
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
    
    def load(self):
        ''' Load an instance from the file '''
        
        with open(self.instance_file, 'r') as file:
            for l in file.readlines():
                line = l.strip()
                
                if not line:
                    continue
                
                if ':' in line:
                    self.load_field(line)
                    
                if line.isupper():
                    self.section = line
                    
                    continue
                
                self.load_section(line)
            
            if len(self.positions) != 0:
                self.load_distances()
        
        return self
        
class Route:
    ''' Class for the route '''
    
    def __init__(self, cvrp: CVRP, route: list[int]):
        self.cvrp = cvrp # CVRP instance
        self.route = route # Route list
        
    def __iter__(self):
        ''' Iterate over the route '''
        
        return iter(self.route)
        
    def __contains__(self, customer: int):
        ''' Check if a customer is in the route '''
        
        return customer in self.route
    
    def __getitem__(self, idx: int | slice):
        ''' Get the customer at the index '''
        
        return self.route[idx]
    
    def __len__(self):
        ''' Get the length of the route '''
        
        return len(self.route)
    
    def reverse(self, i = None, j = None):
        ''' Reverse the route '''
        
        route = self.route[:]
        
        route[i:j] = route[i:j][::-1]
        
        return Route(self.cvrp, route)
        
    def merge(self, other):
        ''' Merge two routes '''
        
        if isinstance(other, Route):
            return Route(self.cvrp, self.route + other.route)
            
        if isinstance(other, list):
            return Route(self.cvrp, self.route + other)
        
        raise Exception('Cannot merge the routes')
        
    def cost(self):
        ''' Calculate the cost for the route '''
        
        cost = self.cvrp.distances[0, self.route[0]]
        for i in range(len(self.route) - 1):
            cost += self.cvrp.distances[self.route[i], self.route[i + 1]]
        cost += self.cvrp.distances[0, self.route[-1]]
        
        return cost
    
    def demand(self):
        ''' Calculate the demand for the route '''
        
        return sum(self.cvrp.demands[c] for c in self.route)

class ClarkeWright:
    ''' Class for the Clarke-Wright savings heuristic '''
    
    def __init__(self, cvrp: CVRP):
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
        
    def run(self):
        ''' Run the Clarke-Wright savings heuristic '''
        
        self.load_savings()
        self.load_routes()
        
        self.combine_routes()
        self.reduce_routes()
        
        return self.routes
    
class TwoOpt:
    ''' Class for the 2-opt heuristic '''
    
    def __init__(self, routes: list[Route]):
        self.routes = routes # Routes list

    def improve_routes(self):
        ''' Improve the routes '''
        
        for idx, route in enumerate(self.routes):
            best_route = route
            best_route_cost = route.cost()
            
            improve = True
            while improve:
                improve = False
                for i in range(len(route) - 1):
                    for j in range(i + 1, len(route)):
                        new_route = route.reverse(i, j + 1)
                        
                        new_route_cost = new_route.cost()

                        if new_route_cost < best_route_cost:
                            best_route = new_route
                            best_route_cost = new_route_cost
                            
                            improve = True        
                
                route = best_route

            self.routes[idx] = route

    def run(self):
        ''' Run the 2-opt heuristic '''
        
        self.improve_routes()
        
        return self.routes

class KNeighbors:
    ''' Class for the k-nearest neighbors heuristic '''
    
    def __init__(self, routes: list[Route]):
        self.cvrp = routes[0].cvrp # CVRP instance
        self.routes = routes # Routes list
        
        self.mst: Graph = None # Minimum spanning tree
        self.matrices: list[np.ndarray] = []
        
    def load_mst(self):
        ''' Load the minimum spanning tree '''  
        
        graph = Graph()
        for i in range(self.cvrp.dimension):
            for j in range(self.cvrp.dimension):
                graph.add_edge(i, j, weight=self.cvrp.distances[i, j])
    
        self.mst = minimum_spanning_tree(graph)
        
    def nearest_neighbors_mst(self, customer: int):
        ''' Get the nearest neighbors from the minimum spanning tree '''
    
        neighbors = list(self.mst.neighbors(customer))
        weights = [self.mst.get_edge_data(customer, c)['weight'] for c in neighbors]
        
        sorted_neighbors = [c for _, c in sorted(zip(weights, neighbors))]
        
        return sorted_neighbors[:self.cvrp.neighbor_number]
        
    def nearest_neighbors_mat(self, customer: int):
        ''' Get the nearest neighbors from the distance matrix '''
        
        neighbors = list(range(self.cvrp.dimension))
        weights = list(self.cvrp.distances[customer])
        
        sorted_neighbors = [c for _, c in sorted(zip(weights, neighbors)) if c != customer]
        
        return sorted_neighbors[:self.cvrp.neighbor_number]
        
    def nearest_neighbors(self, customer: int):
        ''' Get the nearest neighbors '''
        
        neighbors = self.nearest_neighbors_mst(customer)
        
        if len(neighbors) < self.cvrp.neighbor_number:
            for neighbor in self.nearest_neighbors_mat(customer):
                if neighbor not in neighbors:
                    neighbors.append(neighbor)
                    
                if len(neighbors) == self.cvrp.neighbor_number:
                    break
        
        if len(neighbors) < self.cvrp.neighbor_number:
            raise Exception('Cannot find all neighbors')
        
        return neighbors
    
    def load_matrices(self):
        ''' Load distance matrices based on nearest neighbors '''
        
        for route in self.routes:
            matrix = np.full((self.cvrp.dimension, self.cvrp.dimension), -1, dtype=int)
            
            for i in range(self.cvrp.dimension):
                matrix[i, i] = 0
            
            matrix[0, route[0]] = matrix[route[0], 0] = self.cvrp.distances[0, route[0]]    
            for r in range(len(route) - 1):
                matrix[route[r], route[r + 1]] = self.cvrp.distances[route[r], route[r + 1]]
                matrix[route[r + 1], route[r]] = self.cvrp.distances[route[r + 1], route[r]]
            matrix[route[-1], 0] = matrix[0, route[-1]] = self.cvrp.distances[route[-1], 0]
                
            for customer in route:
                for neighbor in self.nearest_neighbors(customer):
                    matrix[customer, neighbor] = self.cvrp.distances[customer, neighbor]
                    matrix[neighbor, customer] = self.cvrp.distances[neighbor, customer]
            
            self.matrices.append(matrix)
    
    def run(self):
        ''' Run the k-nearest neighbors heuristic '''
        
        self.load_mst()
        self.load_matrices()
        
        return self.matrices

class Mapper:
    ''' Class for the propositional logic mapper '''
    
    def __init__(self):
        self.counter = 1
        
        self.mapping: dict[str, int] = {}
        self.mapping_inv: dict[int, str] = {}
        
        self.model: list[str] = []
        self.model_optimizer: list[str] = []

    def add(self, variable: str):
        ''' Add a new variable to the mapping '''
        
        if variable not in self.mapping:
            self.mapping[variable] = self.counter
            self.mapping_inv[self.counter] = variable
            
            self.counter += 1
            
        return self.mapping[variable]

    def transform_literal(self, literal: int, value: int = 1):
        ''' Transform the literal '''
        
        prefix = 'x' if literal >= 0 else '~x'
        
        return f'{value} {prefix}{abs(literal)} '

    def transform_optimizers(self, optimizers: list[tuple[int, int]]):
        ''' Transform the optimizers '''
        
        output = ''
        for literal, value in optimizers:
            output += self.transform_literal(literal, value)  
        return output

    def transform_clauses(self, clause: list[int], value: int = None):
        ''' Transform the clauses '''
        
        output = ''
        for literal in clause:
            output += self.transform_literal(literal, value)   
        return output

    def transform_optimizer(self, literal: int, value: int):
        ''' Transform the optimizer '''
        
        self.model_optimizer.append((literal, value))

    def create_min_function_with_optimizer(self):
        optimizers = [(x[0], x[1]) for x in self.model_optimizer]
        return self.transform_optimizers(optimizers)

    def transform_clauses_inequality(self, clause: list[int], operator: str, value: int = 1):
        self.model.append(self.transform_clauses(clause) + f'{operator} {value} ;')

    def transform_clauses_geq(self, clause: list[int], value: int):
        self.transform_clauses_inequality(clause, '>=', value)

    def transform_clauses_leq(self, clause: list[int], value: int):
        self.transform_clauses_inequality(clause, '<=', value)

    def transform_clauses_equal(self, clause: list[int], value: int):
        self.transform_clauses_inequality(clause, '=', value)

    def generate_model(self):
        model_string = f"* #variable= {self.counter-1} #constraint= {len(self.model)}\n"
        model_string += f"min: {self.create_min_function_with_optimizer()} ; \n"
        
        for line in self.model:
            model_string += line + "\n" 
        return model_string