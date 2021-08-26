import os
import requests
from typing import Tuple
from geopy.distance import distance
from geopy.geocoders import Nominatim
from geopy.exc import ConfigurationError, GeocoderServiceError, GeopyError
from shapely.geometry import Point, Polygon
from .mkad_coords import mkad_coords
from .exceptions import GeocoderError,\
                       YandexError,\
                       YandexValueError,\
                       YandexValidationError

YANDEX_KEY = os.getenv("YANDEX_API_KEY")
URL = "https://geocode-maps.yandex.ru/1.x/" \
      "?apikey=[key]&geocode=[address]&format=json"
URL = URL.replace("[key]", YANDEX_KEY, 1)


def default_geocoder(address: str) -> Tuple[float, float]:
    """
    Returns the coordinates of a given address.

    First tries to use yandex_geocoder(), if that fails,
    it tries to use geopy_geocoder() as a backup.
    """
    try:
        coordinates = yandex_geocoder(address)
        return coordinates
    except YandexError:
        try:
            coordinates = geopy_geocoder(address)
            return coordinates
        except GeopyError:
            raise GeocoderError


def yandex_geocoder(address: str) -> Tuple[float, float]:
    """
    Makes a request to the Yandex API in order to
    convert the given address to a pair of latitude longitude coordinates.
    """
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


def geopy_geocoder(address: str) -> Tuple[float, float]:
    """
    Returns coordinates of the given address.

    Uses the Nominatim API of the geopy library in order to
    convert the given address to a pair of latitude-longitude coordinates.
    Can be used as a backup in case Yandex server is down or not working.
    """
    try:
        geolocator = Nominatim(user_agent="mkad")
    except ConfigurationError:
        raise

    try:
        coordinates = geolocator.geocode(address)
        return (coordinates.latitude, coordinates.longitude)
    except GeocoderServiceError:
        raise


def is_inside_mkad(coordinates: Tuple[float, float]) -> bool:
    """
    Returns True if the given coordinates are inside the MKAD,
    false otherwise.

    The function uses the shapely library's Point and Polygon
    classes based on the given coordinates in order to use the
    Point.within() function to test against the Polygon formed
    from the MKAD kilometer coordinates.
    """
    point = Point(coordinates)
    mkad = [(item[2], item[1]) for item in mkad_coords]
    mkad_polygon = Polygon(mkad)

    return point.within(mkad_polygon)


def get_distance(coordinates: Tuple[float, float]) -> int:
    """
    Returns distance from given coordinates to the MKAD.

    Simple function that uses the geopy library to measure the shortest
    distance to the MKAD by comparing the distances from the given coords
    to each of the kilometer points of the Ring Road.
    """

    shortest_distance = distance(coordinates, (mkad_coords[0][2],
                                               mkad_coords[0][1])).km

    for km in mkad_coords[1:]:
        temp = distance(coordinates, (km[2], km[1])).km
        if temp < shortest_distance:
            shortest_distance = temp

    return int(shortest_distance)
