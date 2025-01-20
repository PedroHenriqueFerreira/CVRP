import numpy as np

def to_dist_matrix(routes, original_dist_matrix):
    n_cities = original_dist_matrix.shape[0]
    new_dist_matrix = np.full((n_cities, n_cities), -1)

    for i in range(0, n_cities):
        new_dist_matrix[i][i] = 0
    
    for route in routes:
        for node_index in range(0,len(route)):
            if(node_index < len(route)-1):
                node_a = route[node_index]
                node_b = route[node_index+1]
            else:
                node_a = route[node_index]
                node_b = route[0]

            new_dist_matrix[node_a][node_b] = original_dist_matrix[node_a][node_b]
            new_dist_matrix[node_b][node_a] = original_dist_matrix[node_b][node_a]
    
    return new_dist_matrix

#function to convert TSPLIB instances into distance matrix
def convert_tsp_to_matrix (filepath):
    data = tsplib95.load(filepath)
    DistMatrix = np.zeros((data.dimension, data.dimension))

    if(data.edge_weight_type == 'EUC_2D'):
        for i in range(data.dimension):
            for j in range(data.dimension):
                DistMatrix[i][j] = data.get_weight(i+1, j+1)
                DistMatrix[j][i] = data.get_weight(i+1, j+1)

    elif(data.edge_weight_type == 'EXPLICIT'):
        for i in range(data.dimension):
            for j in range(data.dimension):
                DistMatrix[i][j] = data.get_weight(i, j)
                DistMatrix[j][i] = data.get_weight(i, j)

    return DistMatrix.astype(int)

def build_routes(output):
    routes_per_vehicle = {}

    for item in output:
        # Split the string using '_' as separator
        parts = item.split('_')

        # Extract informations
        city_a = int(parts[1])
        city_b = int(parts[2])
        vehicle = int(parts[3])

        # Create unique key for each vehicle 
        key_vehicle = f'veiculo_{vehicle}'

        # Addung route to the list
        if key_vehicle not in routes_per_vehicle:
            routes_per_vehicle[key_vehicle] = []

        routes_per_vehicle[key_vehicle].append((city_a, city_b))

    return routes_per_vehicle