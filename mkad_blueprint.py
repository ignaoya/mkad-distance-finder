import logging
from typing import Dict, Tuple, Union
from flask import Blueprint, request
from flask_restful import Api, Resource
from marshmallow import Schema, fields
from geo_functions import yandex_geocoder, get_distance, geopy_geocoder


logging.basicConfig(level=logging.INFO, filename='mkad.log', filemode='a')


# marshmallow Schema is used in order to validate and
# filter input data in order to ensure App security.
# Expected request format is: '/mkad?address=[example address]'
class QuerySchema(Schema):
    address = fields.Str(required=True)


mkad_bp = Blueprint('mkad_bp', __name__)
api = Api(mkad_bp)
schema = QuerySchema()


# DistanceFinder only has a get() method implemented,
# restricting the use of the api to GET requests.
class DistanceFinder(Resource):

    def get(self) -> Tuple[Dict[str, Union[str, int]], int]:
        errors = schema.validate(request.args)
        if errors:
            logging.error(str(errors))
            return {"error": str(errors)}, 400
        else:
            address = request.args.get('address')

        try:
            # Attempt to convert address to coordinates using the yandex api.
            # [yandex_geocoder] can be switched to [geopy_geocoder] in case
            # of server failure or other issues with yandex.
            coords = yandex_geocoder(address)
        except:
            logging.error("Could not parse address provided")
            return {"error": "Could not parse address provided"}, 400

        try:
            distance = get_distance(coords)
            logging.info("Distance from MKAD to " + address + ": " + str(distance))
            return {"distance_km": distance}, 200
        except:
            logging.error("Server error")
            return {"error": "Server error"}, 500


api.add_resource(DistanceFinder, '/mkad')
