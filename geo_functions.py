import os
import requests
from geopy.distance import distance
from geopy.geocoders import Nominatim
from mkad_coords import mkad_coords

YANDEX_KEY = os.getenv("YANDEX_API_KEY")
URL = "https://geocode-maps.yandex.ru/1.x/" \
      "?apikey=[key]&geocode=[address]&format=json"
URL = URL.replace("[key]", YANDEX_KEY, 1)


# Makes a request to the Yandex API in order to
# convert the given address to a pair of latitude longitude coordinates.
def yandex_geocoder(address: str):
    # call the yandex Api using the requests library
    # and save the response to 'res'
    res = requests.get(URL.replace("[address]", address, 1))
    coords = res.json()['response']['GeoObjectCollection'][
        'featureMember'][-1]['GeoObject']['Point']['pos']
    coords = (float(item) for item in coords.split())
    return coords


# Uses the Nominatim API of the geopy library in order to
# convert the given address to a pair of latitude-longitude coordinates.
# Can be used as a backup in case Yandex server is down or not working.
def geopy_geocoder(address: str):
    geolocator = Nominatim(user_agent="mkad")
    location = geolocator.geocode(address)
    return (location.latitude, location.longitude)


# Simple function that uses the geopy library to measure the shortest
# distance to the MKAD by comparing the distances from the given coords
# to each of the kilometer points of the Ring Road.
def get_distance(coords):
    shortest = distance(coords, (mkad_coords[0][2], mkad_coords[0][1])).miles

    for km in mkad_coords[1:]:
        temp = distance(coords, (km[2], km[1])).miles
        if temp < shortest:
            shortest = temp

    return int(shortest)
