# reference : https://flask-socketio.readthedocs.io/en/latest/getting_started.html
#		https://stackoverflow.com/questions/31647081/
#		https://heodolf.tistory.com/125
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from socketio import Client
from threading import Thread
from time import sleep


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')

sio_client = Client()


@sio_client.event
def connect():
	print("sio_client: I'm connected!")


@sio_client.event
def connect_error(data):
	print("sio_client: The connection failed!")


@sio_client.event
def disconnect():
	print("sio_client: I'm disconnected!")



def somefunction():
	# some tasks
	someotherfunction()


def someotherfunction():
	print('threaded : someotherfunction()')

	sleep(10)
	sio_client.emit('message', 'my jsondata') # here occurs the error
	sleep(5)
	sio_client.emit('message', 'my jsondata') # here occurs the error
	

@app.before_first_request
def activate_job():
	print('before_first_request : activate_job()')
	if (sio_client != None):
		sio_client.connect('http://localhost', wait_timeout = 10)


@app.route('/')
def index():
	return render_template('index.html')


@socketio.on('connect')
def setupconnect():
	# global someThread
	print('socketio.on connected...')
	# someThread = Thread(target=somefunction)


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
