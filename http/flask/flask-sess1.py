# flask session test1

from flask import Flask, session

app = Flask(__name__)

app.config['SECRET_KEY'] = 'flask-sess1'
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route("/")
def hello():
	return "hello, world!"

if __name__ == '__main__':
	app.run(host = '0.0.0.0', port = 80)