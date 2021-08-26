from typing import Dict, Tuple, Union
from flask import Blueprint, request
from flask_restful import Api, Resource
from marshmallow import Schema, fields
from geo_functions import yandex_geocoder, get_distance, geopy_geocoder


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
            return {"error": str(errors)}, 400

        try:
            # Attempt to convert address to coordinates using the yandex api.
            # [yandex_geocoder] can be switched to [geopy_geocoder] in case
            # of server failure or other issues with yandex.
            coords = yandex_geocoder(str(request.args.get('address')))
        except:
            return {"error": "Could not parse address provided"}, 400

        try:
            distance = get_distance(coords)
            return {"distance_km": distance}, 200
        except:
            return {"error": "Server error"}, 500


api.add_resource(DistanceFinder, '/mkad')
