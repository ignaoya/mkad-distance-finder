from flask import Blueprint, request
from flask_restful import Api, Resource
from marshmallow import Schema, fields


# marshmallow Schema is used in order to validate and filter input data in order to ensure App security
# expected request format is: '/mkad?address=[example address]'
class QuerySchema(Schema):
    address = fields.Str(required=True)

mkad_bp = Blueprint('mkad_bp', __name__)
api = Api(mkad_bp)
schema = QuerySchema()


class DistanceFinder(Resource):
    def get(self):
        errors = schema.validate(request.args)
        if errors:
            return {"error": str(errors)}, 400

        return {"distance": {"km": 10, "miles": 15}}, 200

api.add_resource(DistanceFinder, '/mkad')
