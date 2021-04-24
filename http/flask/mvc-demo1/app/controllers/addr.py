from flask_restful import Resource

class Addr(Resource):
    def get(self):
        return {'addr response': 'get success'}

    def post(self):
        return {'addr response': 'post success'}
