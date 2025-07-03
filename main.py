from locations import Locations
import networkx as nx
from graph import Graph
from update import Update

loc = Locations()
update = Update()
update.update_times()

times = update.load_cache()

G = nx.DiGraph()
for edge in times:
    G.add_edge(edge['fro']['name'], edge['to']['name'], weight=edge['time'])
G.remove_edges_from(nx.selfloop_edges(G))
graph = Graph()

update.update_solved(G)

solved = update.load_solved()

graph.create(G, solved)

