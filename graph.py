import pandas as pd
import networkx as nx
import random
import math
import graphistry
from dotenv import load_dotenv
import os

class Graph:
    def __init__(self):
        load_dotenv()
        self.password = os.environ.get('PASSWORD')
        self.eulerian = None
        self.graph = None
    def create(self, G, solved):
        path_nodes = solved['path']
        total_time = solved['cost']
        print(solved)

        # Register with Graphistry once (ideally at startup)
        graphistry.register(api=3, username='HoneyOak', password=self.password)

        highlight_edges = set(zip(path_nodes, path_nodes[1:]))
        # Convert networkx DiGraph to DataFrame
        edges = pd.DataFrame([
            {
                "from": u,
                "to": v,
                "weight": d.get("weight", 1),
                'is_path': 'yes' if (u, v) in highlight_edges else 'no'
            }
            for u, v, d in G.edges(data=True)
        ])

        # Optional: nodes data
        nodes = pd.DataFrame({
            'id': list(G.nodes),
            'label': list(G.nodes),
         })


        # Visualize with Graphistry
        graphistry.bind(
            source="from",
            destination="to",
            node="id",
            edge_title="weight",
            point_title="label",
        ).nodes(nodes).edges(edges).encode_edge_color(
            "is_path",
            categorical_mapping={
                "yes": "#e74c3c",  # red for path
                "no": "#aaaaaa"    # grey for all others
            },
            default_mapping="#aaaaaa"  # fallback grey
        ).plot()
            
    def solver(self, G, pop_size=100, elite_size=2, stall_limit=100, mut_rate=0.5):
        nodes = list(G.nodes)
        n = len(nodes)

        index = {node: i for i, node in enumerate(nodes)}

        cost_matrix = [[math.inf]*n for _ in range(n)]

        for u, v, data in G.edges(data=True):
            i = index[u]
            j = index[v]
            cost_matrix[i][j] = data['weight']

        def order_crossover(p1, p2):
            size = len(p1)
            a, b = sorted(random.sample(range(size), 2))
            child = [None] * size
            child[a:b+1] = p1[a:b+1]

            fill = [x for x in p2 if x not in child]
            j = 0
            for i in range(size):
                if child[i] is None:
                    child[i] = fill[j]
                    j = j + 1
            return child

        def mutate(path):
            a, b = random.sample(range(len(path)), 2)
            path[a], path[b] = path[b], path[a]
            return path

        def fitness(path, cost_matrix):
            total = 0
            for i in range(len(path)-1):
                cost = cost_matrix[path[i]][path[i+1]]
                if cost == math.inf:
                    return math.inf 
                total = total + cost
            return total

        def genetic_algorithm(cost_matrix, nodes, pop_size=pop_size, elite_size=elite_size, stall_limit=stall_limit):
            n = len(cost_matrix)
            population = [random.sample(range(n), n) for _ in range(pop_size)]

            best_path = None
            best_cost = math.inf
            generations_without_improvement = 0
            generation = 0

            while generations_without_improvement < stall_limit:
                generation += 1
                population.sort(key=lambda path: fitness(path, cost_matrix))

                current_best = population[0]
                current_cost = fitness(current_best, cost_matrix)

                if current_cost < best_cost:
                    best_path = current_best
                    best_cost = current_cost
                    generations_without_improvement = 0
                else:
                    generations_without_improvement += 1
                
                print(f"Generation {generation}: Best = {[nodes[i] for i in current_best]} | Cost = {current_cost}")

                new_population = population[:elite_size]  # Elitism

                while len(new_population) < pop_size:
                    p1, p2 = random.choices(population[:4], k=2)
                    child = order_crossover(p1, p2)
                    if random.random() < mut_rate:
                        child = mutate(child)
                        print(f"    Mutated: {[nodes[i] for i in child]}")
                    new_population.append(child)

                population = new_population

            best = min(population, key=lambda path: fitness(path, cost_matrix))
            best_named = [nodes[i] for i in best]
            print(f"\n Best Path Found: {best_named}")
            print(f"Final Cost: {fitness(best, cost_matrix)}")
            return best_named, fitness(best, cost_matrix)

        solved = genetic_algorithm(cost_matrix, nodes)
        return solved
            
    
