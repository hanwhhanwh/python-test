# addr v2.0 API
# made : hbesthee@naver.com
# date : 2021-04-26

#from flask import jsonify
from flask import make_response
import json
from flask_restful import Resource
from ..models.addr_model import get_addr

class Addr(Resource):
	def get(self, addr_no):
		rows = get_addr(addr_no)
		result = {'result': [dict(row) for row in rows]}
		return make_response(json.dumps(result, ensure_ascii = False))
