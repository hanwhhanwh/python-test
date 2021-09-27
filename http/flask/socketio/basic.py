# reference : https://flask-socketio.readthedocs.io/en/latest/getting_started.html
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('message')
def handle_message(data):
	print('received message: ' + data)


@socketio.on('my event')
def handle_my_custom_event(json):
	print('received json: ' + str(json))
	emit('REFRESH', 'SMA')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=80, use_reloader=False)