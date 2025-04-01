# CVRP Solver

This project provides a simple implementation of a solver for the Capacitated Vehicle Routing Problem (CVRP).

## Files

- `run.py`: A script that solves the CVRP for a specific instance with a given number of vehicles and neighbors.
- `run_all.py`: A script that runs the solver for all instances found in the `instances` folder.

## Usage

### Running a Single Instance

To solve a single instance, use the following command:

```bash
python run.py <instance> <vehicle_number> <neighbor_number>