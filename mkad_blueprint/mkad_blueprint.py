import logging
from typing import Dict, Tuple, Union
from flask import Blueprint, request
from flask_restful import Api, Resource
from marshmallow import Schema, fields
from .geo_functions import default_geocoder, is_inside_mkad, get_distance
from .exceptions import GeocoderError


logging.basicConfig(level=logging.INFO, filename='logs/mkad.log', filemode='a')


class QuerySchema(Schema):
    """
    The marshmallow Schema is used in order to validate and
    filter input data in order to ensure App security.

    Expected request format is: '/mkad?address=[example address]'
    """
    address = fields.Str(required=True)


mkad_bp = Blueprint('mkad_bp', __name__)
api = Api(mkad_bp)
schema = QuerySchema()


class DistanceFinder(Resource):
    """
    DistanceFinder only has a get() method implemented,
    restricting the use of the api to GET requests.
    """

    def get(self) -> Tuple[Dict[str, Union[str, int]], int]:

        # Perform argument validation with our schema
        input_errors = schema.validate(request.args)
        if input_errors:
            logging.error(str(input_errors))
            return {"error": str(input_errors)}, 400
        else:
            address = request.args.get('address')

        # Convert given address to coordinates
        try:
            coords = default_geocoder(address)
        except GeocoderError:
            logging.error("Geocoder parser error")
            return {"error": "Could not parse address provided"}, 400
        except IndexError as error:
            logging.error(error)
            return {"error": "Could not parse address provided"}, 400
        except KeyError as error:
            logging.error(error)
            return {"error": "Could not parse address provided"}, 400

        # Determine whether the coordinates are inside the MKAD and
        # calculate distance if they are not.
        try:
            if is_inside_mkad(coords):
                logging.info(address + " is inside of the MKAD.")
                return {"message": "Given address is inside the MKAD."}, 200
            else:
                distance = get_distance(coords)
                logging.info("Distance to " + address + ": " + str(distance))
                return {"distance_km": distance}, 200
        except ValueError as error:
            logging.error(error)
            return {"error": "An error occurred, try again later!"}, 400


api.add_resource(DistanceFinder, '/mkad')
