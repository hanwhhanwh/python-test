from .user import CreateUser
from .addr import Addr


def register_apis(api):
	api.add_resource(Addr, '/api/v2.0/addr')
	api.add_resource(CreateUser, '/api/v2.0/user')
