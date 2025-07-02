import pandas as pd
from jaal import Jaal
import networkx as nx

class Graph:
    def __init__(self):
        self.eulerian = None
        self.graph = None
    def create(self, G):
        self.graph = G
        edges = pd.DataFrame([(u, v, str(d["weight"])) for u, v, d in G.edges(data=True)],
                        columns=['from', 'to', 'label'])
        Jaal(edges).plot()
        
    def is_eulerian(self, G):
        is_strong = nx.is_strongly_connected(G)
        balanced = all(G.in_degree(n) == G.out_degree(n) for n in G.nodes)

        if is_strong and balanced:
            eulerian = True
        else:
            eulerian = False
        self.eulerian = eulerian
        return (eulerian)
    
    def solver(self, G):
        if not self.is_eulerian(G):
            raise ValueError("Graph not Eulerian")
        
        # G_copy = G.copy()

        # nodes = list(G_copy.nodes)
        # currPath = [nodes[0]]
        # circuit = []

        # while currPath:
        #     currNode = currPath[-1]
        
        #     if G_copy.out_degree(currNode) > 0:
        #         nextNode = min(G_copy[currNode], key = lambda nbr: G_copy[currNode][nbr]['weight'])
        #         G_copy.remove_edge(currNode, nextNode)
        #         currPath.append(nextNode)
        #     else:
        #         circuit.append(currPath.pop())

        # circuit.reverse()
        # return circuit
        return 
    