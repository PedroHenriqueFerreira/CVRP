class CVRPTW:
    ''' Class for the Capacitated Vehicle Routing Problem with Time Windows ''' 
    
    def __init__(self, instance: str):
        ''' Initialize the CVRPTW instance with the file name '''
        
        self.instance = instance # Instance file
        
        self.vehicle_number = 0 # Number of vehicles
        self.capacity = 0 # Each vehicle capacity
        
        self.customers: dict[int, dict[str, int]] = {} # Customers data
        
        self.load() # Load the data from the file
                
    def load(self):
        try:
            with open(self.file, 'r') as f:
                lines = f.readlines()
                
                for i, line in enumerate(lines):
                    if i == 0:
                        self.vehicle_number, self.capacity = map(int, line.split())
                    else:
                        cid, x, y, demand, ready, due, service = map(int, line.split())
                        self.customers[cid] = {'x': x, 'y': y, 'demand': demand, 'ready': ready, 'due': due, 'service': service}