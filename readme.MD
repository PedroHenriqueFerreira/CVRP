# CVRP Solver

This repository provides an implementation of a solver for the **Capacitated Vehicle Routing Problem** (CVRP), a well-known combinatorial optimization problem. The solver utilizes heuristic methods to compute optimal or near-optimal solutions for a given set of instances. This project includes two main scripts:

- `run.py`: A script that solves the CVRP for a specific instance, given the number of vehicles and neighbors to consider during the search process.
- `run_all.py`: A script that iterates over all instance files in the `instances` directory and solves them using the solver.

## Usage

### Running a Single Instance

To run the solver on a specific instance, execute the following command:

```bash
python run.py <instance> <vehicle_number> <neighbor_number>
```

### Running All Instances

To run the solver on all instances in the `instances` directory, execute the following command:

```bash
python run_all.py
```