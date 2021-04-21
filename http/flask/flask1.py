# 첫 번째 flask 예제
# reference : 
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
	return "hello, world!"
