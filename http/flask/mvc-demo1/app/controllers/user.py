from flask_restful import Resource

class CreateUser(Resource):
    def get(self):
        return {'status': 'get success'}

    def post(self):
        return {'status': 'post success'}
