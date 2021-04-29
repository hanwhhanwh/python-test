from flask import Blueprint
from flask_restful import Api

from .user import CreateUser
from .addr import Addr
from .hello import hello


# RESTful API controllers
def register_apis(app):
	api_bp = Blueprint('api', __name__)
	api = Api(api_bp)

	api.add_resource(Addr, '/api/v2.0/addr/<int:addr_no>')
	api.add_resource(CreateUser, '/api/v2.0/user')

	app.register_blueprint(api_bp)

# normal controllers : by blueprint
def register_blueprint(app):
    app.register_blueprint(hello)
