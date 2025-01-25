from cvrptw import CVRPTW, Vehicle

class Solver:
    ''' Class for the solver '''
    
    def __init__(self, cvrptw: CVRPTW):
        ''' Initialize the solver with the problem instance '''
        
        self.cvrptw = cvrptw # CVRPTW instance
    
    def solve(self):
        ''' Solve the problem '''
        
        self.clarke_wright()

    def clarke_wright(self):
        ''' Clarke-Wright savings heuristic '''
        
        vehicle_capacity = self.cvrptw.vehicle_capacity
        
        distances = self.cvrptw.distances
        customers = self.cvrptw.customers
        n_customers = self.cvrptw.n_customers
        
        routes: list[list[int]] = []
        route_demands: list[int] = []
        route_times: list[int] = []
        for i in range(1, n_customers):
            customer = customers[i]
            
            routes.append([i])
            route_demands.append(customer.demand)
            route_times.append(distances[i, 0] + customer.service_time)
            
            # if customer.ready_time > distances[i, 0]:
            #     print('INFEASIBLE')
        
        for s, i, j in savings:
            customer = customers[j]
            
            route_i = next((r for r in routes if i in r), None)           
            route_j = next((r for r in routes if j in r), None)
            
            if not route_i or not route_j or route_i == route_j:
                continue
            
            idx_i = routes.index(route_i)
            idx_j = routes.index(route_j)
            
            load_i = route_demands[idx_i]
            load_j = route_demands[idx_j]
            
            if load_i + load_j > vehicle_capacity:
                continue
                
            route_i_due_date = route_times[idx_i] + distances[i, j] + customer.service_time
            
            # new_route_i = route_i.copy()
            # new_route_j = route_j.copy()
            
            # if route_i[0] == i and route_j[-1] == j:
            #     new_route_i.reverse()
            # if route_j[-1] == j:
            #     new_route_j.reverse()
            
            # new_route = new_route_i + new_route_j
            
            # #######
            
            # current_customer = customers[new_route[0]]
            # current_time = max(current_customer.ready_time, distances[current_customer.cust_no, 0])
            
            # feasible = True
            
            # for k in range(1, len(new_route)):
            #     previous_customer = customers[new_route[k - 1]]
            #     current_customer = customers[new_route[k]]
                
            #     current_time += previous_customer.service_time + distances[new_route[k - 1], new_route[k]]
                
            #     if current_time < current_customer.ready_time:
            #         current_time = current_customer.ready_time
                    
            #     if current_time > current_customer.due_date:
            #         feasible = False
            #         break
            
            # depot_customer = customers[0]
            
            # if current_time + current_customer.service_time + distances[new_route[k], 0] > depot_customer.due_date:
            #     feasible = False
            
            # if not feasible:
            #     continue
            
            # #######
            
            # routes[idx_i] = new_route
            # routes.remove(route_j)
            
            # route_demands[idx_i] += load_j
            # route_demands.pop(idx_j)
            
            # route_times[idx_i] += distances[i, j] + customer.service_time
            # route_times.pop(idx_j)
        
        print('ROUTES:', routes)
        print('SERVED:', len(set(sum(routes, []))))
