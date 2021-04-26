from flask import Blueprint

from .user import CreateUser
from .addr import Addr
from .hello import hello


# RESTful API controllers
def register_apis(api):
	api.add_resource(Addr, '/api/v2.0/addr')
	api.add_resource(CreateUser, '/api/v2.0/user')


# normal controllers : by blueprint
def register_blueprint(app):
    app.register_blueprint(hello)
