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
        
        self.distances: np.ndarray | None = None # Distance matrix
        
        self.n = 0 # Number of customers
        
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
            
        self.n = len(self.customers)
            
    def load_distances(self):
        ''' Load a distance matrix from customers data '''
        
        self.distances = np.zeros((len(self.customers), len(self.customers)))
        
        for i in range(len(self.customers)):
            for j in range(i + 1, len(self.customers)):
                delta_x = self.customers[i].x - self.customers[j].x
                delta_y = self.customers[i].y - self.customers[j].y
                distance = round(np.sqrt(delta_x ** 2 + delta_y ** 2))
                
                self.distances[i][j] = distance
                self.distances[j][i] = distance
        
        self.distances = self.distances.astype(int)
                
    def load(self):
        ''' Load the data from the file '''
        
        try:
            self.load_instance()
            self.load_distances()  
            
        except Exception:
            from traceback import print_exc
            
            print_exc()
            
            print('Error loading the instance file')
            exit(1)
            
class Vehicle:
    ''' Class for the vehicles data '''
    
    def __init__(self, cvrptw: CVRPTW):
        ''' Initialize the vehicle data '''
        
        self.cvrptw = cvrptw # CVRPTW instance
        
        self.vehicle_capacity = cvrptw.vehicle_capacity # Vehicle capacity
        
        self.total_distance = 0 # Total distance traveled
        self.time = 0 # Total time spent
        
        self.route = [0] # Route with the customers to visit
        
    def move(self, customer: Customer):
        ''' Try to move to a customer '''
        
        distance = self.cvrptw.distances[self.route[-1], customer.cust_no]

        depo = self.cvrptw.customers[0]
        depo_distance = self.cvrptw.distances[customer.cust_no, 0]

        # If the vehicle capacity exceeds the demand
        if self.vehicle_capacity < customer.demand:
            return False
                
        arrive_time = self.time + distance
        depo_time = arrive_time + customer.service_time + depo_distance

        # If the vehicle arrives out of the time window        
        if arrive_time < customer.ready_time or arrive_time > customer.due_date:
            return False
            
        # If the vehicle arrives at the depot out of the time window
        if depo_time > depo.due_date:
            return False
                
        self.vehicle_capacity -= customer.demand
        
        self.total_distance += distance
        self.time = arrive_time + customer.service_time
        
        self.route.append(customer.cust_no)
        
        return True