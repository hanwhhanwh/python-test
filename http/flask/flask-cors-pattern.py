from flask import Flask, Blueprint, jsonify
from flask_cors import CORS

app = Flask(__name__)

api_v1 = Blueprint('API_v1', __name__)
CORS(app, resources=r'/api/*')

@app.route("/")
def helloWorld():
	return "Hello, world!"

@api_v1.route("/api/v1/users")
def list_users():
	return jsonify(user="hbesthee@naver.com")

app.register_blueprint(api_v1)

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80, debug=True)