from graph import Graph
import networkx as nx

G = nx.DiGraph()
G.add_edge("A", "B", weight=3)
G.add_edge("B", "C", weight=7)
G.add_edge("C", "A", weight=2)


graph = Graph()
solved = graph.solver(G)
print(solved)
graph.create(G)