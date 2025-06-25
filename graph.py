import networkx as nx
import pandas as pd
from jaal import Jaal

G = nx.DiGraph()
G.add_edge("A", "B", weight=10)
G.add_edge("B", "A", weight=6)
G.add_edge("B", "C", weight=3)

# Convert to DataFrame
edges = pd.DataFrame([(u, v, str(d["weight"])) for u, v, d in G.edges(data=True)],
                     columns=['from', 'to', 'label'])

Jaal(edges).plot()
