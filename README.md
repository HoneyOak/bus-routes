# Mumbai Bus Route Optimizer

A project to determine the most efficient route connecting all BEST bus stops across Mumbai using Graph Theory, Genetic Algorithms, and Graphistry visualizations. Built as part of the Hack Club Summer of Making.

## Features

- Uses HERE Maps Matrix Routing API to compute traffic-aware durations between bus stops.
- Genetic Algorithm to optimize a complete traversal across ~1600 stops on a graph.
- Visualizes optimal routes interactively using Graphistry.
- Caching for API calls to avoid recomputation.

## Demo

Check out the visual demo [here](https://hub.graphistry.com/graph/graph.html?dataset=7e0ce17e70a1480a98532a2f7e79c805&type=arrow&viztoken=e9f53d84-bebf-438c-a3dd-843d40eb2fff&usertag=0e087153-pygraphistry-0.39.0&splashAfter=false&info=true&play=5000&session=ac35d9488d0c4b45a9c2d9221a127339)

---

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/mumbai-bus-optimizer.git
cd mumbai-bus-optimizer
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the root directory with the following:

```dotenv
HERE_API_KEY=your_here_maps_api_key
PASSWORD=your_graphistry_password
```

You can get your HERE API key from: https://developer.here.com  
Graphistry account credentials: https://hub.graphistry.com
Also change the graphistry username in `graph.py`

---

## How It Works

1. Bus stop coordinates are retrieved and stored with .
2. HERE Maps' Matrix Routing API is used to calculate distance/time between stops.
3. A weighted graph is built from these distances.
4. The near-optimal shortest path is computed using a genetic algorithm.
5. The result is pushed to Graphistry for visual exploration.

---

## Tech Stack

- Python
- NetworkX
- Overpass
- HERE Location Services
- Graphistry

---

## 🙌 Acknowledgements

- [Hack Club](https://hackclub.com/) Summer of Making 2025
- Overpass
- HERE Technologies
- Graphistry
