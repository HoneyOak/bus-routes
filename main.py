from locations import Locations
import networkx as nx
from graph import Graph

loc = Locations()
stops = loc.get_stops(18.9401, 72.8348, 1000.0)

times = loc.get_times(stops)

G = nx.DiGraph()
for edge in times:
    G.add_edge(edge['fro']['name'], edge['to']['name'], weight=edge['time'])
graph = Graph()
# graph.create(G)

solved = graph.solver(G)

print(solved)