import numpy as np

class Instance:
    ''' Class for the Capacitated Vehicle Routing Problem ''' 
    
    def __init__(self, instance_file: str, vehicle_number: int, neighbor_number: int, solver_name: str):
        self.instance_file = instance_file # Instance file name
        self.vehicle_number = vehicle_number # Number of vehicles
        self.neighbor_number = neighbor_number # Number of neighbors
        self.solver_name = solver_name # Name of solver
        
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