# Hello WebServer main source
# made : hbesthee@naver.com
# date : 2022-09-13

from flask import Flask
from app.config.config import config
from app.controllers import register_apis, register_blueprint

app = Flask(__name__)

# load custom Config
app.config.from_object(config)

# register RESTful APIs
register_apis(app)

# register Blueprint Controllers
register_blueprint(app)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80)
