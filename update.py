import json
from locations import Locations
from graph import Graph


class Update:
    CACHE_TIMES_FILE = "cached_times.json"
    CACHE_SOLVED_FILE = "cached_solved.json"

    def __init__(self):
        pass

    def load_cache(self):
        with open(self.CACHE_TIMES_FILE, 'r') as f:
            return json.load(f)

    def save_cache(self, data):
        with open(self.CACHE_TIMES_FILE, 'w') as f:
            json.dump(data, f)

    def load_solved(self):
        with open(self.CACHE_SOLVED_FILE, 'r') as f:
            return json.load(f)
        
    def save_solved(self, solved):
        data = {
            "path": solved[0],
            "cost": solved[1]
        }
        with open(self.CACHE_SOLVED_FILE, 'w') as f:
            json.dump(data, f)

    def update_times(self):
        loc = Locations()
        stops = loc.get_stops()
        times = loc.get_times(stops)
        self.save_cache(times)

    def update_solved(self, G):
        graph = Graph()
        solved = graph.solver(G, pop_size=10000, elite_size=30, stall_limit=5000, mut_rate = 0.1)
        self.save_solved(solved)
        print(solved)