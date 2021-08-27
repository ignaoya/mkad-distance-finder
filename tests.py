import unittest
from unittest.mock import Mock, patch
from app import app
import mkad_blueprint


class ApiTests(unittest.TestCase):
    
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

    @patch('mkad_blueprint.geo_functions.requests.get')
    def test_both_geocoders_error(self, mock_yandex_call):
        mock_yandex_call.return_value = Mock(status_code=400)
        response = self.app.get('/mkad?address=?')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], "Could not parse address provided")

    @patch('mkad_blueprint.geo_functions.requests.get')
    def test_yandex_geocoder_validation_error(self, mock_yandex_call):
        mock_yandex_call.return_value = Mock(status_code=403)
        url = '/mkad?address=2+15th+St+NW,+Washington,+DC+20024,+United%20States'
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['distance_km'], 7825)

    @patch('mkad_blueprint.geo_functions.requests.get')
    def test_yandex_geocoder_value_error(self, mock_yandex_call):
        mock_yandex_call.return_value = Mock(status_code=400)
        url = '/mkad?address=2+15th+St+NW,+Washington,+DC+20024,+United%20States'
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['distance_km'], 7825)

    def test_valid_request_outside(self):
        url = '/mkad?address=2+15th+St+NW,+Washington,+DC+20024,+United%20States'
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('distance_km', response.json)

    def test_valid_request_inside(self):
        url = '/mkad?address=Paveletskaya+Naberezhnaya,+Moscow,+Russia,+115114'
        correct_message = 'Given address is inside the MKAD.'
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], correct_message)


if __name__ == "__main__":
    unittest.main()
