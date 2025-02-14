import numpy as np

from networkx import Graph, minimum_spanning_tree

from classes.instance import Instance
from classes.route import Route
from classes.utils import timer

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
    
    @timer
    def run(self):
        ''' Run the k-nearest neighbors heuristic '''
        
        self.load_mst()
        self.load_matrices()
        
        return self.matrices