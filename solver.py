from cvrptw import CVRPTW, Vehicle

class Solver:
    ''' Class for the solver '''
    
    def __init__(self, cvrptw: CVRPTW):
        ''' Initialize the solver with the problem instance '''
        
        self.cvrptw = cvrptw # CVRPTW instance
    
    def solve(self):
        ''' Solve the problem '''
        
        self.clarke_wright_heuristic()
    
    def nearest_neighbor_heuristic(self):
        ''' Nearest neighbor heuristic '''
        
        served = [True] + [False for _ in range(1, self.cvrptw.n)]
        
        vehicles = [Vehicle(self.cvrptw) for _ in range(self.cvrptw.vehicle_number)]
        
        for vehicle in vehicles:
            while True:
                found = False
                
                for customer in sorted(self.cvrptw.customers, key=lambda x: self.cvrptw.distances[x.cust_no, vehicle.route[-1]] + x.ready_time):
                    if served[customer.cust_no]:
                        continue
                    
                    if vehicle.move(customer):
                        served[customer.cust_no] = True
                        found = True
                        
                        break
                
                if not found:
                    break
                
            if all(served):
                break
                
        print('SERVED:', served)
                
        for vehicle in vehicles:
            print('ROUTE:', vehicle.route)

    def clarke_wright_heuristic(self):
        ''' Clarke-Wright heuristic '''
        
        routes: list[list[int]] = []
        route_loads: list[int] = []
        route_times: list[int] = []
        
        for i in range(1, self.cvrptw.n):
            customer = self.cvrptw.customers[i]
            
            routes.append([i])
            route_loads.append(customer.demand)
            route_times.append(max(customer.ready_time, self.cvrptw.distances[i, 0]) + customer.service_time)
        
        savings: list[tuple[float, int, int]] = []
        
        for i in range(1, self.cvrptw.n):
            for j in range(i + 1, self.cvrptw.n):
                i_0_distance = self.cvrptw.distances[i, 0]
                j_0_distance = self.cvrptw.distances[j, 0]
                i_j_distance = self.cvrptw.distances[i, j]
                
                savings.append((i_0_distance + j_0_distance - i_j_distance, i, j))
                
        savings.sort(key=lambda x: x[0], reverse=True)
        
        for s, i, j in savings:
            customer = self.cvrptw.customers[j]
            
            route_i = next((r for r in routes if i in r), None)           
            route_j = next((r for r in routes if j in r), None)
            
            if route_i is None or route_j is None or route_i == route_j:
                continue
            
            load_i = route_loads[routes.index(route_i)]
            load_j = route_loads[routes.index(route_j)]
            
            if load_i + load_j > self.cvrptw.vehicle_capacity:
                continue
            
            new_route_i = route_i.copy()
            new_route_j = route_j.copy()
            
            if route_i[0] == i and route_j[-1] == j:
                new_route_i.reverse()
            if route_j[-1] == j:
                new_route_j.reverse()
            
            new_route = new_route_i + new_route_j
            
            #######
            
            current_customer = self.cvrptw.customers[new_route[0]]
            current_time = max(current_customer.ready_time, self.cvrptw.distances[current_customer.cust_no, 0])
            
            feasible = True
            
            for k in range(1, len(new_route)):
                previous_customer = self.cvrptw.customers[new_route[k - 1]]
                current_customer = self.cvrptw.customers[new_route[k]]
                
                current_time += previous_customer.service_time + self.cvrptw.distances[new_route[k - 1], new_route[k]]
                
                if current_time < current_customer.ready_time:
                    current_time = current_customer.ready_time
                    
                if current_time > current_customer.due_date:
                    feasible = False
                    break
            
            depot_customer = self.cvrptw.customers[0]
            
            if current_time + current_customer.service_time + self.cvrptw.distances[new_route[k], 0] > depot_customer.due_date:
                feasible = False
            
            if not feasible:
                continue
            
            #######
            
            i_idx = routes.index(route_i)
            j_idx = routes.index(route_j)
            
            routes[i_idx] = new_route
            routes.remove(route_j)
            
            route_loads[i_idx] += load_j
            route_loads.pop(j_idx)
            
            route_times[i_idx] += self.cvrptw.distances[i, j] + customer.service_time
            route_times.pop(j_idx)
        
        print('ROUTES:', routes)
        print('SERVED:', len(set(sum(routes, []))))
