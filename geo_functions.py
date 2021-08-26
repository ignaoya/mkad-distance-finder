import os
import requests
from typing import Tuple
from geopy.distance import distance
from geopy.geocoders import Nominatim
from mkad_coords import mkad_coords
from exceptions import YandexValueError, YandexValidationError

YANDEX_KEY = os.getenv("YANDEX_API_KEY")
URL = "https://geocode-maps.yandex.ru/1.x/" \
      "?apikey=[key]&geocode=[address]&format=json"
URL = URL.replace("[key]", YANDEX_KEY, 1)


# Makes a request to the Yandex API in order to
# convert the given address to a pair of latitude longitude coordinates.
def yandex_geocoder(address: str) -> Tuple[float, float]:
    # call the yandex Api using the requests library
    # and save the response to 'res'
    result = requests.get(URL.replace("[address]", address, 1))
    print(result.status_code)

    if result.status_code == 400:
        raise YandexValueError
    elif result.status_code == 403:
        raise YandexValidationError
    else:
        coordinates = result.json()['response']['GeoObjectCollection'][
            'featureMember'][-1]['GeoObject']['Point']['pos']
        coordinates = [float(item) for item in coordinates.split()]
        return (coordinates[1], coordinates[0])


# Uses the Nominatim API of the geopy library in order to
# convert the given address to a pair of latitude-longitude coordinates.
# Can be used as a backup in case Yandex server is down or not working.
def geopy_geocoder(address: str) -> Tuple[float, float]:
    geolocator = Nominatim(user_agent="mkad")
    coordinates = geolocator.geocode(address)
    return (coordinates.latitude, coordinates.longitude)


# Simple function that uses the geopy library to measure the shortest
# distance to the MKAD by comparing the distances from the given coords
# to each of the kilometer points of the Ring Road.
def get_distance(coordinates: Tuple[float, float]) -> int:
    shortest_distance = distance(coordinates, (mkad_coords[0][2], mkad_coords[0][1])).km

    for km in mkad_coords[1:]:
        temp = distance(coordinates, (km[2], km[1])).km
        if temp < shortest_distance:
            shortest_distance = temp

    return int(shortest_distance)
