import pandas as pd
from jaal import Jaal


class Graph:
    def __init__(self):
        pass
    def create(G):
        edges = pd.DataFrame([(u, v, str(d["weight"])) for u, v, d in G.edges(data=True)],
                        columns=['from', 'to', 'label'])
        Jaal(edges).plot()