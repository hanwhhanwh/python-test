# -*- coding: utf-8 -*-
# Flask access log 커스터마이징 예제
# made : hbesthee@naver.com
# date : 2024-12-30

from datetime import datetime
from logging import Formatter, getLogger, INFO
from logging.handlers import RotatingFileHandler
import time

from flask import Flask, request


app = Flask(__name__)

# Custom logger formatter
class CustomFormatter(Formatter):
	def format(self, record):
		# Add request-specific information
		if hasattr(record, 'request'):
			req = record.request
			record.url = req.url
			record.method = req.method
			if req.headers.getlist("X-Forwarded-For"):
				ip = req.headers.getlist("X-Forwarded-For")[0]
			else:
				ip = req.remote_addr
			ip = ip.replace('::ffff:', '') # 불필요한 IPv6 제거
			record.remote_addr = ip
			record.user_agent = req.headers.get('User-Agent', '-')
			record.status_code = record.response.status_code if hasattr(record, 'response') else 0
			record.response_time = record.response_time if hasattr(record, 'response_time') else 0

			return super().format(record)
		else:
			record.url = '-'
			record.method = '-'
			record.remote_addr = '-'
			record.user_agent = '-'
			record.status_code = 0
			record.response_time = 0

			return ''


def setup_logger():
	# Create logger
	logger = getLogger('werkzeug')
	logger.handlers.clear()
	# logger.setLevel(INFO)

	# Create handler
	handler = RotatingFileHandler('access.log', maxBytes=10000, backupCount=3)
	handler.setLevel(INFO)

	# Create formatter
	formatter = CustomFormatter(
		'%(remote_addr)s - - [%(asctime)s] "%(method)s %(url)s" %(status_code)s'
		' %(response_time).2fms "%(user_agent)s"'
	)
	
	# Add formatter to handler
	handler.setFormatter(formatter)
	
	# Add handler to logger
	logger.addHandler(handler)
	
	return logger

logger = setup_logger()

@app.before_request
def start_timer():
	request.start_time = time.time()

@app.after_request
def log_request(response):
	# Calculate request processing time
	if hasattr(request, 'start_time'):
		total_time = (time.time() - request.start_time) * 1000  # Convert to milliseconds
	else:
		total_time = 0
	
	# Create log record with custom attributes
	log_record = logger.makeRecord(
		'werkzeug',
		INFO,
		'.',
		0,
		'',
		[],
		None
	)
	
	# Add custom attributes
	log_record.request = request
	log_record.response = response
	log_record.response_time = total_time
	
	# Log the record
	# logger.handle(log_record)
	
	return response

@app.route("/")
def hello():
	return "hello, world!"

if __name__ == '__main__':
	app.run(debug=True)