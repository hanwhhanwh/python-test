# MVC flask 예제
from flask import Flask
from flask_restful import Api
from app.controllers import register_apis
from app.controllers.hello import hello

app = Flask(__name__)
api = Api(app)

# register RESTful APIs
register_apis(api)
# register Controllers
app.register_blueprint(hello)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)