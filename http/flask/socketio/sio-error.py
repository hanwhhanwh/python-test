# reference : https://flask-socketio.readthedocs.io/en/latest/getting_started.html
#		https://stackoverflow.com/questions/31647081/
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from threading import Thread
from time import sleep


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def somefunction():
	# some tasks
	someotherfunction()


def someotherfunction():
	# some other tasks
	print('threaded : someotherfunction()')
	sleep(10)
	emit('anEvent', 'jsondata', namespace='/test') # here occurs the error >> RuntimeError: Working outside of request context.


@app.route('/')
def index():
	return render_template('index.html')


@socketio.on('connect', namespace='/sio')
def setupconnect():
	global someThread
	print('socketio.on connected...')
	someThread = Thread(target=somefunction)


@socketio.on('message')
def handle_message(data):
	print('received message: ' + data)


@socketio.on('my event')
def handle_my_custom_event(json):
	print('received json: ' + str(json))
	emit('REFRESH', 'SMA')


if __name__ == '__main__':
	someThread = Thread(target=somefunction)
	someThread.start()
	
	socketio.run(app, host='0.0.0.0', port=80, use_reloader=False)
