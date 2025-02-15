from os import system, remove

import numpy as np

from classes.instance import Instance
from classes.route import Route
from classes.utils import timer

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
        
        self.model: list[int] = [] # Model list
        self.routes: list[str] = [] # Routes list

    def get(self, variable: str):
        ''' Get the variable from the mapping '''
        
        if variable not in self.mapping:
            self.mapping[variable] = self.counter
            self.mapping_inv[self.counter] = variable
            
            self.counter += 1
            
        return self.mapping[variable]

    def encode_literal(self, literal: int, factor: int):
        ''' Encode the literal '''
        
        return f'{factor} {["~", ""][literal >= 0]}x{abs(literal)} '

    def encode_clause(self, factors: list[int], clause: list[int]):
        ''' Encode the clause '''
        
        return ''.join(self.encode_literal(literal, factor) for literal, factor in zip(clause, factors))

    def add_constraint(self, factors: list[int], clause: list[int], operator: str, value: int):
        ''' Add a clause with an operator '''
        
        if factors is None:
            factors = [1] * len(clause)
        
        self.constraints.append(self.encode_clause(factors, clause) + f'{operator} {value} ;')

    def add_constraint_eq(self, factors: list[int], clause: list[int], value: int):
        ''' Add a clause with the equality operator '''
        
        self.add_constraint(factors, clause, '=', value)
        
    def add_constraint_leq(self, factors: list[int], clause: list[int], value: int):
        ''' Add a clause with the less than or equal operator '''
        
        self.add_constraint(factors, clause, '<=', value)
        
    def add_constraint_geq(self, factors: list[int], clause: list[int], value: int):
        ''' Add a clause with the greater than or equal operator '''
        
        self.add_constraint(factors, clause, '>=', value)

    def add_objective(self, literal: int, value: int):
        self.objectives.append(self.encode_literal(literal, value))

    def create_objective_string(self):
        ''' Create the objective '''
        
        return ''.join(self.objectives)

    def create_constraint_string(self):
        ''' Create the constraints '''
        
        return '\n'.join(self.constraints)

    def encode(self):
        ''' Encode the model '''
        
        string = f'* #variable= {self.counter - 1} #constraint= {len(self.constraints)}\n'
        string += f'min: {self.create_objective_string()} ; \n'
        string += f'{self.create_constraint_string()} \n'
        
        return string
    
    def decode(self, output: list[str]):
        ''' Decode the model '''

        for line in output:
            if line.startswith('s UNSATISFIABLE'):
                raise Exception('The model is unsatisfiable')
            
            if line[0] != 'v':
                continue
            
            self.model += [int(v) for v in line[2:].replace('x', '').replace('c', '').split()]        

    def solve(self):
        ''' Solve the model '''
        
        try:
            with open('input.txt', 'w+') as input_file:
                input_file.write(self.encode())
                
            system('./solvers/clasp input.txt > output.txt')
                
            with open('output.txt', 'r') as output_file:
                output = output_file.readlines()    
            
            self.decode(output)
        
            remove('input.txt')
            remove('output.txt')
        
        except:    
            raise Exception('Cannot solve the model')
        
    def load_model(self):
        ''' Load the model '''
        
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
            w_0_j_k = [self.get(f'w_0_{j}_{k}') for j in range(self.cvrp.dimension) if j != 0]
            
            self.add_constraint_eq(None, w_0_j_k, 1)
            
        # Only one vehicle enters the depot
        for k in range(self.cvrp.vehicle_number):
            w_i_0_k = [self.get(f'w_{i}_0_{k}') for i in range(self.cvrp.dimension) if i != 0]

            self.add_constraint_eq(None, w_i_0_k, 1)
            
        # A customer leaves only to one customer and by one vehicle
        for i in range(1, self.cvrp.dimension):
            w_i_j_k: list[int] = []
            
            for k in range(self.cvrp.vehicle_number):
                w_i_j_k += [self.get(f'w_{i}_{j}_{k}') for j in range(self.cvrp.dimension) if i != j]
            
            self.add_constraint_eq(None, w_i_j_k, 1)
        
        # A customer enters only by one customer and by one vehicle
        for j in range(1, self.cvrp.dimension):
            w_i_j_k: list[int] = []
            
            for k in range(self.cvrp.vehicle_number):
                w_i_j_k += [self.get(f'w_{i}_{j}_{k}') for i in range(self.cvrp.dimension) if i != j]
            
            self.add_constraint_eq(None, w_i_j_k, 1)
            
        # A vehicle cannot enter and leave the same customer
        for i in range(self.cvrp.dimension):
            for j in range(i + 1, self.cvrp.dimension):
                for k in range(self.cvrp.vehicle_number):
                    w_i_j_k = self.get(f'w_{i}_{j}_{k}')
                    w_j_i_k = self.get(f'w_{j}_{i}_{k}')
                    
                    self.add_constraint_geq(None, [-w_i_j_k, -w_j_i_k], 1)
                    
        # If a vehicle leaves a customer and visits another one then both customers was visited
        for i in range(1, self.cvrp.dimension):
            for j in range(1, self.cvrp.dimension):
                for k in range(self.cvrp.vehicle_number):
                    if i == j:
                        continue
                    
                    w_i_j_k = self.get(f'w_{i}_{j}_{k}')
                    t_i_k = self.get(f't_{i}_{k}')
                    t_j_k = self.get(f't_{j}_{k}')
                    
                    self.add_constraint_geq(None, [-w_i_j_k, t_i_k], 1)
                    self.add_constraint_geq(None, [-w_i_j_k, t_j_k], 1)
        
        # A customer is only visited by one vehicle
        for i in range(1, self.cvrp.dimension):
            for k in range(self.cvrp.vehicle_number):
                for l in range(self.cvrp.vehicle_number):
                    if k == l:
                        continue
                    
                    t_i_k = self.get(f't_{i}_{k}')
                    t_i_l = self.get(f't_{i}_{l}')
                    
                    self.add_constraint_geq(None, [-t_i_k, -t_i_l], 1)
                    
        # A vehicle visits a customer after leaving the depot
        for j in range(1, self.cvrp.dimension):
            for k in range(self.cvrp.vehicle_number):
                w_0_j_k = self.get(f'w_{0}_{j}_{k}')
                t_j_k = self.get(f't_{j}_{k}')
                
                self.add_constraint_geq(None, [-w_0_j_k, t_j_k], 1)
        
        # A vehicle visits a customer before enters the depot
        for i in range(1, self.cvrp.dimension):
            for k in range(self.cvrp.vehicle_number):
                w_i_0_k = self.get(f'w_{i}_{0}_{k}')
                t_i_k = self.get(f't_{i}_{k}')
                
                self.add_constraint_geq(None, [-w_i_0_k, t_i_k], 1)

        # Base path
        for i in range(self.cvrp.dimension):
            for j in range(self.cvrp.dimension):
                if i == j:
                    continue
                
                for k in range(self.cvrp.vehicle_number):
                    w_i_j_k = self.get(f'w_{i}_{j}_{k}')
                    c_i_j_k = self.get(f'c_{i}_{j}_{k}')
                    
                    self.add_constraint_geq(None, [-w_i_j_k, c_i_j_k], 1)

        # Induction path
        for i in range(1, self.cvrp.dimension):
            for j in range(1, self.cvrp.dimension):
                if i == j:
                    continue
                    
                for k in range(1, self.cvrp.dimension):
                    for l in range(self.cvrp.vehicle_number):
                        w_i_j_l = self.get(f'w_{i}_{j}_{l}')
                        c_j_k_l = self.get(f'c_{j}_{k}_{l}')
                        c_i_k_l = self.get(f'c_{i}_{k}_{l}')
                        
                        self.add_constraint_geq(None, [-w_i_j_l, -c_j_k_l, c_i_k_l], 1)
        
        # There is no path from a customer to the same customer
        for i in range(1, self.cvrp.dimension):
            c_i_i_v = [self.get(f'c_{i}_{i}_{k}') for k in range(self.cvrp.vehicle_number)]
            
            self.add_constraint_eq(None, c_i_i_v, 0)
        
        # Set the weights
        for k in range(self.cvrp.vehicle_number):
            for i in range(self.cvrp.dimension):  
                for j in range(self.cvrp.dimension):
                    if i == j:
                        continue
                        
                    w_i_j_k = self.get(f'w_{i}_{j}_{k}')
                    
                    self.add_objective(w_i_j_k, self.cvrp.distances[i, j])
        
        # Set false the removed neighbors
        for k in range(self.cvrp.vehicle_number):
            for i in range(self.cvrp.dimension):
                for j in range(self.cvrp.dimension):
                    if self.matrices[k][i, j] != 0 and self.matrices[k][i, j] != -1:
                        continue
                    
                    w_i_j_k = self.get(f'w_{i}_{j}_{k}')
                    
                    self.add_constraint_eq(None, [w_i_j_k], 0)
            
        # Capacity constraint
        
        demands_negative = [-d for d in self.cvrp.demands]
        
        for k in range(self.cvrp.vehicle_number):
            t_i_k = [self.get(f't_{i}_{k}') for i in range(self.cvrp.dimension)]
            
            self.add_constraint_geq(demands_negative, t_i_k, -self.cvrp.capacity)
                    
        self.solve()
        
    def load_routes(self):
        ''' Load the routes ''' 
        
        vehicle_paths: list[list[Route]] = [[] for _ in range(self.cvrp.vehicle_number)]
        
        for item in self.model:
            var = self.mapping_inv.get(item, '')
            
            if not var.startswith('w_'):
                continue
            
            i, j, k = map(int, var.split('_')[1:])
            
            p: list[int] = []
            
            if i != 0:
                p.append(i)
                
            if j != 0:
                p.append(j)
                
            vehicle_paths[k].append(Route(self.cvrp, p))
        
        for paths in vehicle_paths:
            route = paths.pop(0)
            
            while True:
                if len(paths) == 0:
                    break
                
                for path in paths[:]:
                    if path[0] == route[-1]:
                        route = Route.merge(route, path[1:])
                        
                        paths.remove(path)
                    
                    elif path[-1] == route[0]:
                        route = Route.merge(path[:-1], route)
                        
                        route.remove(path)
            
            self.routes.append(route)
        
    @timer
    def run(self):
        ''' Run the solver '''
        
        self.load_model()
        self.load_routes()
        
        return self.routes