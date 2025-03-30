from os import system, remove
from os.path import sep

import numpy as np

from classes.instance import Instance
from classes.route import Route
from classes.utils import timer

class Solver:
    ''' Class for the solver '''
    
    def __init__(self, cvrp: Instance, solver_name: str, matrices: list[np.ndarray]):
        self.cvrp = cvrp # CVRP instance
        self.solver_name = solver_name # Solver name
        self.matrices = matrices # Matrices list
        
        self.counter = 1
        
        self.mapping: dict[str, int] = {} # Mapping variable to literal
        self.mapping_inv: dict[int, str] = {} # Mapping literal to variable
        
        self.constraints: list[str] = [] # Constraints list
        self.objectives: list[str] = [] # Objectives list
        
        self.optimum: float = 0 # Optimum value
        self.routes: list[str] = [] # Routes list

    def get(self, variable: str):
        ''' Get the variable from the mapping '''
        
        if variable not in self.mapping:
            self.mapping[variable] = self.counter
            self.mapping_inv[self.counter] = variable
            
            self.counter += 1
            
        return self.mapping[variable]

    def encode_literal(self, factor: int, literal: int):
        ''' Encode the literal '''
        
        return f'{factor} {["~", ""][literal >= 0]}x{abs(literal)}'

    def encode_clause(self, factors: list[int], clause: list[int]):
        ''' Encode the clause '''
        
        return ' '.join(self.encode_literal(factor, literal) for factor, literal in zip(factors, clause))

    def add_constraint(self, factors: list[int], clause: list[int], operator: str, value: int):
        ''' Add a clause with an operator '''
        
        if factors is None:
            factors = [1] * len(clause)
        
        self.constraints.append(self.encode_clause(factors, clause) + f' {operator} {value} ;')

    def add_constraint_eq(self, factors: list[int], clause: list[int], value: int):
        ''' Add a clause with the equality operator '''
        
        self.add_constraint(factors, clause, '=', value)
        
    def add_constraint_leq(self, factors: list[int], clause: list[int], value: int):
        ''' Add a clause with the less than or equal operator '''
        
        self.add_constraint(factors, clause, '<=', value)
        
    def add_constraint_geq(self, factors: list[int], clause: list[int], value: int):
        ''' Add a clause with the greater than or equal operator '''
        
        self.add_constraint(factors, clause, '>=', value)

    def add_objective(self, factor: int, literal: int):
        self.objectives.append(self.encode_literal(factor, literal))

    def create_objective_string(self):
        ''' Create the objective '''
        
        return ' '.join(self.objectives)

    def create_constraint_string(self):
        ''' Create the constraints '''
        
        return '\n'.join(self.constraints)

    def encode(self):
        ''' Encode the model '''
        
        string = f'* #variable= {self.counter - 1} #constraint= {len(self.constraints)}\n'
        string += f'min: {self.create_objective_string()}  ; \n'
        string += f'{self.create_constraint_string()} \n'
        
        return string
    
    def decode(self, output: list[str]):
        ''' Decode the model '''

        model = []

        for line in output:
            if line.startswith('s UNSATISFIABLE'):
                raise Exception('The model is unsatisfiable')
            
            if line.startswith('o'): 
                self.optimum = float(line[2:])
            
            if line.startswith('v'):
                model += [int(v) for v in line[2:].replace('x', '').replace('c', '').split()] 
                         
        for item in model:
            if item not in self.mapping_inv:
                continue
            
            var = self.mapping_inv[item]
            
            if not var.startswith('w_'):
                continue
            
            self.routes.append(var)
    
    def solve(self):
        ''' Solve the model '''
        
        try:
            with open('input.txt', 'w+') as input_file:
                input_file.write(self.encode())
                
            system(f'{self.solver_name} input.txt > output.txt')
            
            with open('output.txt', 'r') as output_file:
                self.decode(output_file.readlines())
        
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
        for v in range(len(self.matrices)):   
            for i in range(self.cvrp.dimension):
                t.append(self.get(f't_{i}_{v}'))
                
                for j in range(self.cvrp.dimension):
                    c.append(self.get(f'c_{i}_{j}_{v}'))
                    
                    if i != j:
                        w.append(self.get(f'w_{i}_{j}_{v}'))
        
        # Each vehicle leaves the depot by one customer
        for v in range(len(self.matrices)):
            w_0_j_v = [self.get(f'w_0_{j}_{v}') for j in range(self.cvrp.dimension) if j != 0]
            
            self.add_constraint_eq(None, w_0_j_v, 1)
            
        # Each vehicle enters the depot by one customer
        for v in range(len(self.matrices)):
            w_i_0_v = [self.get(f'w_{i}_0_{v}') for i in range(self.cvrp.dimension) if i != 0]

            self.add_constraint_eq(None, w_i_0_v, 1)
            
        # A customer leaves only to one customer and by one vehicle
        for i in range(1, self.cvrp.dimension):
            w_i_j_v: list[int] = []
            
            for v in range(len(self.matrices)):
                w_i_j_v += [self.get(f'w_{i}_{j}_{v}') for j in range(self.cvrp.dimension) if i != j]
            
            self.add_constraint_eq(None, w_i_j_v, 1)
        
        # A customer enters only by one customer and by one vehicle
        for j in range(1, self.cvrp.dimension):
            w_i_j_v: list[int] = []
            
            for v in range(len(self.matrices)):
                w_i_j_v += [self.get(f'w_{i}_{j}_{v}') for i in range(self.cvrp.dimension) if i != j]
            
            self.add_constraint_eq(None, w_i_j_v, 1)
            
        # A vehicle cannot enter and leave the same customer
        for i in range(self.cvrp.dimension):
            for j in range(i + 1, self.cvrp.dimension):
                for v in range(len(self.matrices)):
                    w_i_j_v = self.get(f'w_{i}_{j}_{v}')
                    w_j_i_v = self.get(f'w_{j}_{i}_{v}')
                    
                    self.add_constraint_geq(None, [-w_i_j_v, -w_j_i_v], 1)
                    
        # If a vehicle leaves a customer and visits another one then both customers was visited
        for i in range(1, self.cvrp.dimension):
            for j in range(1, self.cvrp.dimension):
                for v in range(len(self.matrices)):
                    if i == j:
                        continue
                        
                    w_i_j_v = self.get(f'w_{i}_{j}_{v}')
                    t_i_v = self.get(f't_{i}_{v}')
                    t_j_v = self.get(f't_{j}_{v}')
                    
                    self.add_constraint_geq(None, [-w_i_j_v, t_i_v], 1)
                    self.add_constraint_geq(None, [-w_i_j_v, t_j_v], 1)
        
        # A customer is only visited by one vehicle
        for i in range(1, self.cvrp.dimension):
            for v in range(len(self.matrices)):
                for l in range(len(self.matrices)):
                    if v == l:
                        continue
                        
                    t_i_v = self.get(f't_{i}_{v}')
                    t_i_l = self.get(f't_{i}_{l}')
                    
                    self.add_constraint_geq(None, [-t_i_v, -t_i_l], 1)
                    
        # A vehicle visits a customer before enters and after leaving the depot
        for ij in range(1, self.cvrp.dimension):
            for v in range(len(self.matrices)):
                w_0_ij_v = self.get(f'w_{0}_{ij}_{v}')
                w_ij_0_v = self.get(f'w_{ij}_{0}_{v}')
                t_ij_v = self.get(f't_{ij}_{v}')
                
                self.add_constraint_geq(None, [-w_0_ij_v, t_ij_v], 1)
                self.add_constraint_geq(None, [-w_ij_0_v, t_ij_v], 1)

        # Base path
        for i in range(self.cvrp.dimension):
            for j in range(self.cvrp.dimension):
                if i == j:
                    continue
                
                for v in range(len(self.matrices)):
                    w_i_j_v = self.get(f'w_{i}_{j}_{v}')
                    c_i_j_v = self.get(f'c_{i}_{j}_{v}')
                    
                    self.add_constraint_geq(None, [-w_i_j_v, c_i_j_v], 1)

        # Induction path
        for i in range(1, self.cvrp.dimension):
            for j in range(1, self.cvrp.dimension):
                if i == j:
                    continue
                    
                for k in range(1, self.cvrp.dimension):
                    for v in range(len(self.matrices)):
                        w_i_j_v = self.get(f'w_{i}_{j}_{v}')
                        c_j_k_v = self.get(f'c_{j}_{k}_{v}')
                        c_i_k_v = self.get(f'c_{i}_{k}_{v}')
                        
                        self.add_constraint_geq(None, [-w_i_j_v, -c_j_k_v, c_i_k_v], 1)
        
        # There is no path from a customer to the same customer
        for i in range(1, self.cvrp.dimension):
            c_i_i_v = [self.get(f'c_{i}_{i}_{v}') for v in range(len(self.matrices))]
            
            self.add_constraint_eq(None, c_i_i_v, 0)
        
        # Capacity constraint
        neg_demands = [-demand for demand in self.cvrp.demands]
        
        for v in range(len(self.matrices)):
            t_i_v = [self.get(f't_{i}_{v}') for i in range(self.cvrp.dimension)]
            
            self.add_constraint_geq(neg_demands, t_i_v, -self.cvrp.capacity)
        
        # Set the weights
        for v in range(len(self.matrices)):
            for i in range(self.cvrp.dimension):  
                for j in range(self.cvrp.dimension):
                    if i == j:
                        continue
                        
                    w_i_j_v = self.get(f'w_{i}_{j}_{v}')
                    
                    self.add_objective(self.cvrp.distances[i, j], w_i_j_v)
        
        # Set false the removed customers
        for v in range(len(self.matrices)):
            for i in range(self.cvrp.dimension):
                for j in range(self.cvrp.dimension):
                    if self.matrices[v][i, j] != 0 and self.matrices[v][i, j] != -1:
                        continue
                    
                    w_i_j_v = self.get(f'w_{i}_{j}_{v}')
                    
                    self.add_constraint_eq(None, [w_i_j_v], 0)
        
    # ONLY FOR VISUALIZATION
    # def load_routes(self):
    #     ''' Load the routes ''' 
        
    #     vehicle_paths: list[list[Route]] = [[] for _ in range(len(self.matrices))]
        
    #     for item in self.model:
    #         var = self.mapping_inv.get(item, '')
            
    #         if not var.startswith('w_'):
    #             continue
            
    #         i, j, k = map(int, var.split('_')[1:])
            
    #         p: list[int] = []
            
    #         if i != 0:
    #             p.append(i)
                
    #         if j != 0:
    #             p.append(j)
                
    #         vehicle_paths[k].append(Route(self.cvrp, p))
        
    #     for paths in vehicle_paths:
    #         route = paths.pop(0)
            
    #         while True:
    #             if len(paths) == 0:
    #                 break
                
    #             for path in paths[:]:
    #                 if path[0] == route[-1]:
    #                     route = route + path[1:]
                        
    #                     paths.remove(path)
                    
    #                 elif path[-1] == route[0]:
    #                     route = path[:-1] + route
                        
    #                     route.remove(path)
            
    #         self.routes.append(route)
        
    @timer
    @staticmethod
    def run(cvrp: Instance, solver_name: str, matrices: list[np.ndarray]) -> tuple[float, float, list[str]]:
        ''' Run the solver '''
        
        solver = Solver(cvrp, solver_name, matrices)
        
        solver.load_model()
        solver.solve()
        
        return solver.optimum, solver.routes