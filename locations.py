import os
from dotenv import load_dotenv
import requests

class Locations:
    def __init__(self):
        load_dotenv()
        self.API = os.environ.get('MAPS_API_KEY')
    def get_stops(self, latitude, longitude, radius):
        places_url = "https://places.googleapis.com/v1/places:searchNearby"

        # JSON payload
        payload = {
            "includedTypes": ["bus_stop",  "bus_station"],
            "maxResultCount": 10,
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
    
    def get_times(self, bus_stops):
        times = []
        for stop in bus_stops:
            origin = f"{stop['location']['latitude']},{stop['location']['longitude']}"
            for stop_2 in bus_stops:
                if stop_2 == stop:
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

       
