# Flask HelloWorld
# author : hbesthee@naver.com
# date : 2024-10-29

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
	return 'Hello, World!'

if (__name__ == '__main__'):
	app.run()
