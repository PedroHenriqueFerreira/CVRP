import numpy as np

from os import system
from networkx import minimum_spanning_tree, Graph

class Instance:
    ''' Class for the Capacitated Vehicle Routing Problem ''' 
    
    def __init__(self, instance_file: str, vehicle_number: int, neighbor_number: int):
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
    
    def __init__(self, cvrp: Instance, route: list[int]):
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
    
    def __init__(self, cvrp: Instance, routes: list[Route]):
        self.cvrp = cvrp # CVRP instance
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

class Solver:
    ''' Class for the solver '''
    
    def __init__(self, cvrp: Instance, matrices: list[np.ndarray]):
        self.cvrp = cvrp # CVRP instance
        self.matrices = matrices # Matrices list
        
        self.counter = 1
        
        self.mapping: dict[str, int] = {} # Mapping variable to literal
        self.mapping_inv: dict[int, str] = {} # Mapping literal to variable
        
        self.constraints: list[str] = [] # Constraints list
        self.objectives: list[str] = [] # Objectives list

    def get(self, variable: str):
        ''' Get the variable from the mapping '''
        
        if variable not in self.mapping:
            self.mapping[variable] = self.counter
            self.mapping_inv[self.counter] = variable
            
            self.counter += 1
            
        return self.mapping[variable]

    def encode_literal(self, literal: int, value: int):
        ''' Encode the literal '''
        
        return f'{value} {["~", ""][literal >= 0]}x{abs(literal)} '

    def encode_clause(self, clause: list[int], value: int = None):
        ''' Encode the clause '''
        
        return ''.join(self.encode_literal(literal, value) for literal in clause)

    def add_constraint(self, clause: list[int], operator: str, value: int):
        ''' Add a clause with an operator '''
        
        self.constraints.append(self.encode_clause(clause) + f'{operator} {value} ;')

    def add_constraint_eq(self, clause: list[int], value: int):
        ''' Add a clause with the equality operator '''
        
        self.add_constraint(clause, '=', value)
        
    def add_constraint_leq(self, clause: list[int], value: int):
        ''' Add a clause with the less than or equal operator '''
        
        self.add_constraint(clause, '<=', value)
        
    def add_constraint_geq(self, clause: list[int], value: int):
        ''' Add a clause with the greater than or equal operator '''
        
        self.add_constraint(clause, '>=', value)

    def add_objective(self, literal: int, value: int):
        self.objectives.append(self.encode_literal(literal, value))

    def create_objective_string(self):
        ''' Create the objective '''
        
        return ' '.join(self.objectives)

    def create_constraint_string(self):
        ''' Create the constraints '''
        
        return '\n'.join(self.constraints)

    def encode(self):
        ''' Encode the model '''
        
        string = f'* #variable= {self.counter - 1} #constraint= {len(self.constraints)}\n'
        string += f'min: {self.create_objective_string()} ; \n'
        string += self.create_constraint_string()
        
        return string
    
    def decode(self, output: list[str]):
        ''' Decode the model '''

        cost: int = None
        val: list[int] = []
        
        for line in output:
            if line.startswith('s UNSATISFIABLE'):
                break
            
            match line[0]:
                case 'o':
                    cost = line[2:]
                
                case 'v':
                    val += [int(v) for v in line[2:].replace('x', '').replace('c', '').split()]        
        
        return cost, val

    def solve(self):
        ''' Solve the model '''
        
        try:
            with open('input.txt', 'w+') as input_file:
                input_file.write(self.encode())
                
            system('./naps input.txt > output.txt')
                
            with open('output.txt', 'r') as output_file:
                output = output_file.readlines()    
            
            return self.decode(output)
        
        except:    
            return None, []
        
    def run(self):
        ''' Run the solver '''
        
        t: list[int] = []
        c: list[int] = []
        w: list[int] = []
        
        # Create the variables
        for k in range(self.cvrp.vehicle_number):   
            for i in range(self.cvrp.dimension):
                t.append(self.get(f't_{i}_{k}'))
                
                for j in range(self.cvrp.dimension):
                    c.append(self.get(f'c_{i}_{j}_{k}'))
                    
                    if i != j:
                        w.append(self.get(f'w_{i}_{j}_{k}'))
        
        # Only one vehicle leaves the depot
        for k in range(self.cvrp.vehicle_number):
            w_0_j_k = [self.get(f"w_0_{j}_{k}") for j in range(self.cvrp.dimension) if j != 0]
            self.add_constraint_eq(w_0_j_k, 1)
            
        # Only one vehicle enters the depot
        for k in range(self.cvrp.vehicle_number):
            w_i_0_k = [self.get(f"w_{i}_0_{k}") for i in range(self.cvrp.dimension) if i != 0]
            
            self.add_constraint_eq(w_i_0_k, 1)
            
        # A customer leaves only to one customer and by one vehicle
        for i in range(1, self.cvrp.dimension):
            w_i_j_k: list[int] = []
            
            for k in range(self.cvrp.vehicle_number):
                w_i_j_k += [self.get(f"w_{i}_{j}_{k}") for j in range(self.cvrp.dimension) if i != j]
            
            self.add_constraint_eq(w_i_j_k, 1)
        
        # A customer enters only by one customer and by one vehicle
        for j in range(1, self.cvrp.dimension):
            w_i_j_k: list[int] = []
            
            for k in range(self.cvrp.vehicle_number):
                w_i_j_k += [self.get(f"w_{i}_{j}_{k}") for i in range(self.cvrp.dimension) if i != j]
            
            self.add_constraint_eq(w_i_j_k, 1)
            
        