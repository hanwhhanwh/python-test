# MVC flask 예제
from flask import Flask
from flask_restful import Api
from app.config.config import config
from app.controllers import register_apis, register_blueprint

app = Flask(__name__)
api = Api(app)

# load custom Config
app.config.from_object(config)

# register RESTful APIs
register_apis(api)
# register Blueprint Controllers
register_blueprint(app)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)