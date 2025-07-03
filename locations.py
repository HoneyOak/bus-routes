import os
from dotenv import load_dotenv
import requests
import time
import math

class Locations:
    def __init__(self):
        load_dotenv()
        self.API = os.environ.get('MAPS_API_KEY')
    def get_stops(self, latitude, longitude, radius):
        places_url = "https://places.googleapis.com/v1/places:searchNearby"

        # JSON payload
        payload = {
            "includedTypes": ["bus_stop",  "bus_station"],
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": radius
                }
            }
        }

        # Headers
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.API,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location"
        }

        # Send POST request
        response = requests.post(places_url, headers=headers, json=payload)
        print(response.json())
        if not response.json(): 
            return []
        places = response.json()['places']

        bus_stops = []

        for place in places:
            stop = {
                "name": place['displayName']['text'],
                "location": place['location'],
                "address": place['formattedAddress']
            }
            bus_stops.append(stop)
        return bus_stops

    def sweep_mumbai(self, north=19.264723, south=18.905, east=72.964771, west=72.789062, step_km=1.0, radius=1000):
        def km_to_lat(km):
            return km / 110.574

        def km_to_lng(km, lat):
            return km / (111.320 * math.cos(math.radians(lat)))

        lat_step = km_to_lat(step_km)
        lon_step = km_to_lng(step_km, (north + south) / 2)

        all_stops = []
        seen_coords = set()

        lat = south
        while lat <= north:
            lon = west
            while lon <= east:
                stops = self.get_stops(lat, lon, radius)
                for stop in stops:
                    key = (round(stop['location']['latitude'], 5), round(stop['location']['longitude'], 5))
                    if key not in seen_coords:
                        seen_coords.add(key)
                        all_stops.append(stop)
                lon += lon_step
                time.sleep(0.2)
            lat += lat_step

        return all_stops
    
    def get_times(self, bus_stops):
        times = []
        for stop in bus_stops:
            origin = f"{stop['location']['latitude']},{stop['location']['longitude']}"
            for stop_2 in bus_stops:
                if stop['location'] == stop_2['location']:
                    continue
                destination =  f"{stop_2['location']['latitude']},{stop_2['location']['longitude']}"
                # get stop and stop2 pair duration_in_traffic
                distance_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
                distance_params = {
                    "origins": origin,
                    "destinations": destination,
                    "units": "metric",
                    "departure_time": "now",
                    "mode": "driving",
                    "key": self.API
                }
                distance_res = requests.get(distance_url, params=distance_params).json()
                # store in times
                time = {
                    "fro": stop,
                    "to": stop_2,
                    "time": distance_res['rows'][0]['elements'][0]['duration_in_traffic']['value']
                }
                times.append(time)
        return times

       
