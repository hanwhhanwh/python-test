# MVC flask 예제 ; 멀티 스레드로 Flask 구동 예시
# date	2023-11-15
# author	hbesthee@naver.com
# reference : https://stackoverflow.com/questions/56856153/

from datetime import datetime
from flask import Flask, Blueprint
from threading import Thread
from time import sleep

from app.config.config import config
from app.controllers import register_apis, register_blueprint


def handleFlask() -> None:
	print("Flask handler started...\n")

	app = Flask(__name__)

	# DEBUG 설정을 반드시 False로 해주어야 signal 관련 오류가 발생하지 않습니다.
	config.DEBUG = False
	app.config.from_object(config) # load custom Config

	register_apis(app) # register RESTful APIs
	register_blueprint(app) # register Blueprint Controllers

	app.run() # 또는 app.run(debug = Flase)


def handleTimer() -> None:
	for index in range(5):
		print(f"  {index} passed...")
		sleep(1)

	print(f'timer end')


def main() -> None:
	Thread(target = handleFlask).start()

	Thread(target = handleTimer).start()


if __name__ == '__main__':
	main()