import os
from dotenv import load_dotenv
import requests
import time
import random
from datetime import datetime, timezone
from itertools import islice
from here_location_services import LS
from here_location_services.config.matrix_routing_config import (
    WorldRegion,
    MATRIX_ATTRIBUTES,
)

class Locations:
    def __init__(self):
        load_dotenv()
        self.API = os.environ.get('HERE_API_KEY')
    def get_stops(self):
        overpass_url = "https://overpass-api.de/api/interpreter"

        # Fixed bounding box for Mumbai
        south = 18.905
        north = 19.294723
        west = 72.789062
        east = 72.964771

        # Overpass QL query
        query = f"""
        [out:json][timeout:25];
        (
        node["highway"="bus_stop"]({south},{west},{north},{east});
        );
        out body;
        """

        # Send request
        response = requests.post(overpass_url, data={'data': query})
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            return []

        data = response.json()
        elements = data.get("elements", [])

        # Parse bus stop data
        bus_stops = []
        for element in elements:
            tags = element.get("tags", {})
            name = tags.get("name") or tags.get("name:en") or "Unnamed Stop"

            stop = {
                "name": name,
                "location": {
                    "latitude": element["lat"],
                    "longitude": element["lon"]
                },
                "operator": tags.get("operator"),
                "shelter": tags.get("shelter"),
                "raw_tags": tags
            }
            bus_stops.append(stop)
        sampled_stops = random.sample(bus_stops, 100)

        return sampled_stops

    def chunked(self, iterable, size):
        for i in range(0, len(iterable), size):
            yield iterable[i:i + size]

    def get_times(self, bus_stops):
        ls = LS(api_key=self.API)
        all_times = []
        locations = [
            {"lat": stop['location']['latitude'], "lng": stop['location']['longitude']}
            for stop in bus_stops
        ]

        origin_chunks = list(self.chunked(list(enumerate(locations)), 15))
        destination_chunks = list(self.chunked(list(enumerate(locations)), 100))

        for origin_chunk in origin_chunks:
            for dest_chunk in destination_chunks:
                origin_indices, origin_locs = zip(*origin_chunk)
                dest_indices, dest_locs = zip(*dest_chunk)

                region_definition = WorldRegion()
                matrix_attributes = [
                    MATRIX_ATTRIBUTES.travelTimes,
                    MATRIX_ATTRIBUTES.distances,
                ]

                try:
                    result = ls.matrix(
                        origins=list(origin_locs),
                        destinations=list(dest_locs),
                        region_definition=region_definition,
                        matrix_attributes=matrix_attributes,
                        transport_mode="car",
                        departure_time=datetime.now(timezone.utc).isoformat(),
                    )

                    matrix = result.matrix
                    travel_times = matrix["travelTimes"]
                    distances = matrix["distances"]
                    num_dest = len(dest_indices)

                    print(f"Received matrix: {len(origin_indices)}×{len(dest_indices)}")

                    index = 0
                    for i_idx, i in enumerate(origin_indices):
                        for j_idx, j in enumerate(dest_indices):
                            time_value = travel_times[index]
                            distance_value = distances[index]
                            index += 1
                            if time_value is not None:
                                all_times.append({
                                    "fro": bus_stops[i],
                                    "to": bus_stops[j],
                                    "time": time_value,
                                    "distance": distance_value
                                })

                    time.sleep(0.2)  # prevent rate limiting

                except Exception as e:
                    print(f"Matrix request failed: {e}")
                    continue

        return all_times
