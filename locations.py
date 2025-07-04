import os
from dotenv import load_dotenv
import requests
import time
import math
from datetime import datetime, timezone


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

        return bus_stops

    def get_times(self, bus_stops):
        here_api_key = self.API
        url = "https://router.hereapi.com/v8/routes"
        headers = {"Content-Type": "application/json"}
        
        times = []
        for i, stop in enumerate(bus_stops):
            origin = f"{stop['location']['latitude']},{stop['location']['longitude']}"
            for j, stop_2 in enumerate(bus_stops):
                if i == j:
                    continue
                destination = f"{stop_2['location']['latitude']},{stop_2['location']['longitude']}"

                params = {
                    "transportMode": "car",
                    "origin": origin,
                    "destination": destination,
                    "return": "summary",
                    "apikey": here_api_key
                }

                try:
                    res = requests.get(url, headers=headers, params=params)
                    data = res.json()
                    duration = data["routes"][0]["sections"][0]["summary"]["duration"]  # in seconds
                    print(data)

                    times.append({
                        "fro": stop,
                        "to": stop_2,
                        "time": duration
                    })

                    time.sleep(0.2)  # prevent rate limiting

                except Exception as e:
                    print(f"Exception for {origin} → {destination}: {e}")
                    continue

        return times