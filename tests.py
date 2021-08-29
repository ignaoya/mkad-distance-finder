from __future__ import annotations
import unittest
from unittest.mock import patch
from typing import Dict, Optional
from app import app
from geopy.exc import GeopyError, ConfigurationError, GeocoderServiceError
from mkad_blueprint.geo_functions import (
    default_geocoder,
    yandex_geocoder,
    geopy_geocoder,
    is_inside_mkad,
    get_distance,
    get_distance_shapely,
    get_distance_binary_search
)
from mkad_blueprint.exceptions import (
    GeocoderError,
    YandexError,
    YandexValueError,
    YandexValidationError
)


class DistanceFinderApiTests(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_incomplete_url(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 404)

    def test_incomplete_request(self):
        correct_message = "{'address': ['Missing data for required field.']}"
        response = self.app.get('/mkad', follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], correct_message)

    @patch('mkad_blueprint.mkad_blueprint.default_geocoder')
    def test_both_geocoders_failing(self, mock_geocoder):
        mock_geocoder.side_effect = GeocoderError
        response = self.app.get('/mkad?address=?')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json['error'], "Could not parse address provided"
        )

    @patch('mkad_blueprint.mkad_blueprint.default_geocoder')
    def test_index_error(self, mock_geocoder):
        mock_geocoder.side_effect = IndexError
        response = self.app.get('/mkad?address=?')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json['error'], "Could not parse address provided"
        )

    @patch('mkad_blueprint.mkad_blueprint.default_geocoder')
    def test_key_error(self, mock_geocoder):
        mock_geocoder.side_effect = KeyError
        response = self.app.get('/mkad?address=?')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json['error'], "Could not parse address provided"
        )

    @patch('mkad_blueprint.mkad_blueprint.is_inside_mkad')
    @patch('mkad_blueprint.mkad_blueprint.default_geocoder')
    def test_valid_request_outside(self, mock_geocoder, mock_is_inside):
        mock_geocoder.return_value = (50, 30)
        mock_is_inside.return_value = False
        url = '/mkad?address=2+15th+St+NW,+Washington,+DC+20024'
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('distance_km', response.json)

    @patch('mkad_blueprint.mkad_blueprint.is_inside_mkad')
    @patch('mkad_blueprint.mkad_blueprint.default_geocoder')
    def test_valid_request_inside(self, mock_geocoder, mock_is_inside):
        mock_geocoder.return_value = (55.715423, 37.646013)
        mock_is_inside.return_value = True
        url = '/mkad?address=Paveletskaya+Naberezhnaya,+Moscow'
        correct_message = 'Given address is inside the MKAD.'
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], correct_message)


class DefaultGeocoderTests(unittest.TestCase):
    """Tests for default_geocoder()"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_invalid_address(self):
        self.assertRaises(GeocoderError, default_geocoder, "")

    @patch('mkad_blueprint.geo_functions.yandex_geocoder')
    def test_valid_address_with_yandex(self, mock_yandex_geocoder):
        correct_coordinates = (38.889865, -77.033039)
        mock_yandex_geocoder.return_value = correct_coordinates
        address = '2 15th St NW, Washington, DC 20024, United States'
        coordinates = default_geocoder(address)
        self.assertEqual(coordinates, correct_coordinates)

    @patch('mkad_blueprint.geo_functions.geopy_geocoder')
    @patch('mkad_blueprint.geo_functions.yandex_geocoder')
    def test_valid_address_with_geopy(
        self,
        mock_yandex_geocoder,
        mock_geopy_geocoder
    ):
        mock_yandex_geocoder.side_effect = YandexError
        correct_coordinates = (38.889865, -77.033039)
        mock_geopy_geocoder.return_value = correct_coordinates
        address = '2 15th St NW, Washington, DC 20024, United States'
        coordinates = default_geocoder(address)
        self.assertEqual(coordinates, correct_coordinates)


class YandexGeocoderTests(unittest.TestCase):
    """Tests for yandex_geocoder()"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('mkad_blueprint.geo_functions.requests.get')
    def test_raise_value_error(self, mock_get):
        mock_get.return_value = mocked_requests_get("value_error_example")
        address = ''
        self.assertRaises(YandexValueError, yandex_geocoder, address)

    @patch('mkad_blueprint.geo_functions.requests.get')
    def test_raise_validation_error(self, mock_get):
        mock_get.return_value = mocked_requests_get("validation_error_example")
        address = ''
        self.assertRaises(YandexValidationError, yandex_geocoder, address)

    @patch('mkad_blueprint.geo_functions.requests.get')
    def test_return_coordinates(self, mock_get):
        mock_get.return_value = mocked_requests_get("return_coordinates")
        address = 'valid address'
        correct_coordinates = (50, 30)
        coordinates = yandex_geocoder(address)
        self.assertEqual(coordinates, correct_coordinates)


class GeopyGeocoderTests(unittest.TestCase):
    """Tests for geopy_geocoder()"""

    @patch('mkad_blueprint.geo_functions.Nominatim')
    def test_raise_config_error(self, mock_nominatim):
        mock_nominatim.side_effect = ConfigurationError
        address = ''
        self.assertRaises(ConfigurationError, geopy_geocoder, address)

    @patch('mkad_blueprint.geo_functions.Nominatim')
    def test_geocoder_service_error(self, mock_nominatim):
        mock_nominatim.return_value = MockGeolocator()
        address = 'ServiceError'
        self.assertRaises(GeopyError, geopy_geocoder, address)

    @patch('mkad_blueprint.geo_functions.Nominatim')
    def test_attribute_error(self, mock_nominatim):
        mock_nominatim.return_value = MockGeolocator()
        address = 'AttributeError'
        self.assertRaises(GeopyError, geopy_geocoder, address)

    @patch('mkad_blueprint.geo_functions.Nominatim')
    def test_return_coordinates(self, mock_nominatim):
        mock_nominatim.return_value = MockGeolocator()
        address = 'ValidAddress'
        correct_coordinates = (50, 30)
        coordinates = geopy_geocoder(address)
        self.assertEqual(coordinates, correct_coordinates)


class IsInsideMKADTests(unittest.TestCase):
    """Tests for is_inside_mkad()"""

    def test_return_true(self):
        coordinates = (55.688198, 37.589790)
        self.assertTrue(is_inside_mkad(coordinates))

    def test_return_false(self):
        coordinates = (55, 37)
        self.assertFalse(is_inside_mkad(coordinates))


class GetDistanceTests(unittest.TestCase):
    """Tests for get_distance()"""

    def test_return_value(self):
        coordinates = (55, 37)
        result = get_distance(coordinates)
        self.assertTrue(result > 0)
        self.assertTrue(type(result) == int)


class GetDistanceShapelyTests(unittest.TestCase):
    """Tests for get_distance_shapely()"""

    def test_return_value(self):
        coordinates = (55, 37)
        result = get_distance_shapely(coordinates)
        self.assertTrue(result > 0)
        self.assertTrue(type(result) == int)


class GetDistanceBinarySearchTests(unittest.TestCase):
    """Tests for get_distance_binary_search()"""

    def test_return_value(self):
        coordinates = (40, 30)
        binary_search_result = get_distance_binary_search(coordinates)
        brute_force_result = get_distance(coordinates)
        self.assertEqual(binary_search_result, brute_force_result)


def mocked_requests_get(*args, **kwargs) -> MockResponse:
    """Helper function to mock requests.get() responses."""
    class MockResponse:
        def __init__(self, json_data: Dict, status_code: int):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == "value_error_example":
        return MockResponse(None, 400)
    elif args[0] == "validation_error_example":
        return MockResponse(None, 403)
    elif args[0] == "return_coordinates":
        json_content = {
            'response': {
                'GeoObjectCollection': {
                    'featureMember': [{
                        'GeoObject': {
                            'Point': {
                                'pos': '30 50'}}}]}}}
        return MockResponse(json_content, 200)

    return MockResponse(None, 404)


class MockCoordinates:
    """Helper function to mock geolocator.geocode() calls."""

    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude


class MockGeolocator:
    """Helper class to mock geolocator.geocode() calls."""

    def geocode(self, address: str) -> Optional[MockCoordinates]:
        if address == "ServiceError":
            raise GeocoderServiceError
        elif address == "AttributeError":
            raise AttributeError
        elif address == "ValidAddress":
            return MockCoordinates(50, 30)


if __name__ == "__main__":
    unittest.main()
