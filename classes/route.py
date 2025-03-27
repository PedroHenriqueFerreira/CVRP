from typing import Union   

from classes.instance import Instance

class Route:
    ''' Class for the route '''
    
    def __init__(self, cvrp: Instance, route: list[int]):
        self.cvrp = cvrp # CVRP instance
        self.route = route # Route list
        
        self._cost: int = -1 # Route cost
        self._demand: int = -1 # Route demand
        
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
    
    def __add__(self, other: Union[list[int], 'Route']):
        ''' Add a customer to the route '''
        
        if isinstance(other, Route):
            other = other.route
        
        return Route(self.cvrp, self.route + other)
        
    def __radd__(self, other: Union[list[int], 'Route']):
        ''' Add a customer to the route '''
        
        if isinstance(other, Route):
            other = other.route
        
        return Route(self.cvrp, other + self.route)
    
    def reversed(self, i = None, j = None):
        ''' Returns a reversed route on the given indexes '''
        
        route = self.route[:]
        route[i:j] = route[i:j][::-1]
        
        return Route(self.cvrp, route)
    
    @property
    def cost(self):
        ''' Get the route cost '''
        
        if self._cost < 0:
            self._cost = self.calculate_cost()
        
        return self._cost
    
    @property
    def demand(self):
        ''' Get the route demand '''
        
        if self._demand < 0:
            self._demand = self.calculate_demand()
        
        return self._demand
        
    def calculate_cost(self):
        ''' Calculate the cost for the route '''
        
        cost = self.cvrp.distances[0, self.route[0]]
        for i in range(len(self.route) - 1):
            cost += self.cvrp.distances[self.route[i], self.route[i + 1]]
        cost += self.cvrp.distances[0, self.route[-1]]
        
        return cost
    
    def calculate_demand(self):
        ''' Calculate the demand for the route '''
        
        return sum(self.cvrp.demands[c] for c in self.route)