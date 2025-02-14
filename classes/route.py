from typing import Union   

from classes.instance import Instance

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
        
    @staticmethod
    def merge(self: Union[list[int], 'Route'], other: Union[list[int], 'Route']):
        ''' Merge two routes '''
        
        self_route = self.route if isinstance(self, Route) else self
        other_route = other.route if isinstance(other, Route) else other
        
        return Route(self.cvrp, self_route + other_route)
        
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