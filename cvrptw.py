from traceback import print_exc

import numpy as np

class Customer:
    ''' Class for the customers data '''
    
    def __init__(
        self, 
        cust_no: int, 
        x: int, 
        y: int, 
        demand: int, 
        ready_time: int, 
        due_date: int, 
        service_time: int
    ):
        ''' Initialize the customer data '''
        
        self.cust_no = cust_no # Customer number
        self.x = x # X coordinate
        self.y = y # Y coordinate
        self.demand = demand # Demand
        self.ready_time = ready_time # Earliest time to start the service
        self.due_date = due_date # Latest time to start the service
        self.service_time = service_time # Service time

class CVRPTW:
    ''' Class for the Capacitated Vehicle Routing Problem with Time Windows ''' 
    
    def __init__(self, instance_file: str):
        ''' Initialize the CVRPTW instance with the file name '''
        
        self.instance_file = instance_file # Instance file name
        
        self.vehicle_number = 0 # Number of vehicles    
        self.vehicle_capacity = 0 # Each vehicle capacity
        self.customers: list[Customer] = [] # Customers data
        
        self.distances: np.ndarray[np.int32] = np.array([]) # Distance matrix
        self.routes: list[list[int]] = [] # Routes list
        
        self.load() # Load the data from the file
    
    def load_instance(self):
        ''' Load an instance from the file '''
        
        with open(self.instance_file, 'r') as file:
            for line in file.readlines():
                if not line.strip():
                    continue
                
                values = line.split()
                
                if not values[0].isdigit():
                    continue
                
                if len(values) == 2:
                    self.vehicle_number, self.vehicle_capacity = map(int, values)
                    
                if len(values) == 7:
                    self.customers.append(Customer(*map(int, values)))
            
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
        
        return sum(self.customers[c].demand for c in route) <= self.vehicle_capacity
                
    def time_constraint(self, route: list[int]):
        ''' Check the time constraint for a route '''
        
        time = 0
        
        for k in route:
            prev_customer = self.customers[0] if k == 0 else self.customers[k - 1]
            curr_customer = self.customers[k]
            
            time += self.distances[prev_customer.cust_no, curr_customer.cust_no]
            
            if time < curr_customer.ready_time:
                time = curr_customer.ready_time
                
            if time > curr_customer.due_date:
                return False
            
            time += curr_customer.service_time
            
        time += self.distances[0, route[-1]]
            
        return time <= self.customers[0].due_date
                
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
        
        routes = [[c.cust_no] for c in self.customers[1:]]
        
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
            
            if not self.capacity_constraint(combined_route) or not self.time_constraint(combined_route):
                continue
        
            routes[route_i] = combined_route
            routes.pop(route_j)
            
        # Reduce the number of routes
        
        # while len(routes) > self.vehicle_number:
        #     min_route = min(routes, key=len)
        #     routes.remove(min_route)
            
        #     for k in min_route:
        #         reduced = False
                
        #         for r in routes:
        #             combined_route_1 = r + [k]
        #             combined_route_2 = [k] + r
                    
        #             if self.capacity_constraint(combined_route_1) and self.time_constraint(combined_route_1):
        #                 routes.append(combined_route_1)
        #                 reduced = True
        #                 break
                    
        #             if self.capacity_constraint(combined_route_2) and self.time_constraint(combined_route_2):
        #                 routes.append(combined_route_2)
        #                 reduced = True
        #                 break
                
        #         if not reduced:
        #             print('INFEASIBLE')
        
        #
            
        for route in routes:
            print(route)
            
        print('ALL', len(set(sum(routes, []))))
        print('ROUTES', len(routes))
        print('VEHICLES', self.vehicle_number)
        
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