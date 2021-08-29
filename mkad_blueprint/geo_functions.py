import os
import requests
from typing import Tuple
from geopy.distance import distance
from geopy.geocoders import Nominatim
from geopy.exc import ConfigurationError, GeocoderServiceError, GeopyError
from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points
from .mkad_coords import mkad_coords
from .exceptions import (
    GeocoderError,
    YandexError,
    YandexValueError,
    YandexValidationError
)

YANDEX_KEY = os.getenv("YANDEX_API_KEY")
URL = "https://geocode-maps.yandex.ru/1.x/" \
      "?apikey=[key]&geocode=[address]&format=json"
if YANDEX_KEY:
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

    The order of the coordinates is reversed to comply with the order
    in which the geopy distance function accepts them.
    """
    result = requests.get(URL.replace("[address]", address, 1))

    if result.status_code == 400:
        raise YandexValueError
    elif result.status_code == 403:
        raise YandexValidationError
    else:
        # Exctract coordinates from the result.json() dictionary and
        # reverse their order when returning them.
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
        raise GeopyError
    except AttributeError:
        raise GeopyError


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


def get_distance_shapely(coordinates: Tuple[float, float]) -> int:
    """
    Returns distance from given coordinates to the MKAD.

    This function uses the shapely library to determine the shortest
    distance to the MKAD. It is a direct alternative to get_distance().
    """
    point = Point(coordinates)
    mkad = [(item[2], item[1]) for item in mkad_coords]
    mkad_polygon = Polygon(mkad)

    mkad_nearest_point, _ = nearest_points(mkad_polygon, point)
    shortest_distance = distance(
        coordinates, (mkad_nearest_point.x, mkad_nearest_point.y)
    ).km

    return int(shortest_distance)


def get_distance_binary_search(coordinates: Tuple[float, float]) -> int:
    """
    Returns distance from given coordinates to the MKAD.

    This function is another alternative to get_distance(), using a
    modified form of binary search to reduce the amount of comparisons
    needed to return the shortest distance to the MKAD.
    """
    # Find four equidistant points on the MKAD with which to compare.
    index_list = [(len(mkad_coords) // 4) * i for i in range(4)]
    distance_list = []

    # Obtain the distances from the given coords to the four points
    for index in index_list:
        new_distance = distance(coordinates, (mkad_coords[index][2],
                                              mkad_coords[index][1])).km
        distance_list.append([index, new_distance])

    # Sort list from shorter to longer distances, keeping corresponding index
    distance_list.sort(key=lambda x: x[1])

    index_list = []

    # If the second shortest point is the same distance as the third shortest
    # point, then the given coordinates are in such a position that we cannot
    # take the first and second shortest point from the four indexes, instead
    # we take the second and third shortest.
    if (distance_list[1][1] == distance_list[2][1]):
        low_point = distance_list[1][0]
        high_point = distance_list[2][0]
    # Otherwise we take the first and second shortest.
    else:
        low_point = distance_list[0][0]
        high_point = distance_list[1][0]

    # We now proceed to eliminate points that are in between the two points
    # we have selected. All other points are discarded.

    while high_point - low_point > 1:
        low_distance = distance(
            coordinates,
            (mkad_coords[low_point][2], mkad_coords[low_point][1])
        ).km
        high_distance = distance(
            coordinates,
            (mkad_coords[high_point][2], mkad_coords[high_point][1])
        ).km

        if low_distance == high_distance:
            low_point += 1
        elif low_distance < high_distance:
            mid_point = (low_point + high_point) // 2
            high_point = mid_point
        elif low_distance > high_distance:
            mid_point = (low_point + high_point) // 2
            low_point = mid_point

    # After the while loop we have reduced the possibilities to two points
    # on the MKAD, indexed as low_point and high_point. We simply measure
    # the distances to these and return the shortest.

    low_distance = distance(
        coordinates,
        (mkad_coords[low_point][2], mkad_coords[low_point][1])
    ).km
    high_distance = distance(
        coordinates,
        (mkad_coords[high_point][2], mkad_coords[high_point][1])
    ).km

    if low_distance < high_distance:
        return int(low_distance)
    else:
        return int(high_distance)
