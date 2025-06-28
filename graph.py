import networkx as nx
import pandas as pd
from jaal import Jaal

G = nx.DiGraph()
G.add_edge("Dadar Fire brigade", "Madhav Nagar", weight=6)
G.add_edge("Madhav Nagar", "Dadar Fire brigade", weight=7)

# Convert to DataFrame
edges = pd.DataFrame([(u, v, str(d["weight"])) for u, v, d in G.edges(data=True)],
                     columns=['from', 'to', 'label'])

Jaal(edges).plot()

