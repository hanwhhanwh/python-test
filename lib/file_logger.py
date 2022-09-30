# 파일 및 콘솔 로깅 처리를 위한 라이브러리 소스
# date: 2021-06-08
# author: hbesthee@naver.com
#-*- coding: utf-8 -*-
# use tab char size: 4

from os import path, remove, rename

import gzip
import logging
import logging.handlers
import os


class GZipRotator:
	""" 로그를 분할 처리할 때 로그 파일을 압축하는데 이용하는 Rotator """

	def __call__(self, source, dest):
		if ( path.exists(source) and (not path.exists(dest)) ):
			rename(source, dest)
			f_in = open(dest, 'rb')
			f_out = gzip.open(f'{dest}.gz', 'wb')
			f_out.writelines(f_in)
			f_out.close()
			f_in.close()
			remove(dest)


class FileLogger:
	"""콘솔과 파일로 동시에 로깅 처리하는 디버깅을 위한 로깅 클래스
	사용법:
		from lib.file_logger import FileLogger

		logger = FileLogger(log_filename = 'test_logger', log_path = '/tmp/test')
		logger.info('start test app')
	"""
	__log = None

	def __init__(self
			, log_path = './logs'
			, log_filename = 'logger'
			, log_ext = '.log'
			, log_level = logging.WARNING
			, log_console = True):
		"""Logger 클래스를 초기화합니다.

		Args:
			log_path (string): 로깅 파일이 쌓이는 폴더 경로 ; "./logs"
			log_filename (string): 로깅 파일 이름 ; "logger"
			log_ext (string): 로깅 파일 기본 확장자 ; ".log"
			log_level : 로깅 레벨 = logging.DEBUG (10), logging.INFO (20), logging.WARNING (30), logging.ERROR (40), logging.CRITICAL (50)
			log_console (boolean): 콘솔로도 로깅 출력 여부
		"""

		self.log_path		= log_path
		self.log_filename	= log_filename
		self.log_ext		= log_ext
		self.log_level		= log_level
		self.log_console	= log_console

		# folder create
		if not os.path.exists(self.log_path):
			os.makedirs(self.log_path)

		self.__log = self.__createLogger()


	def __createLogger(self):
		"""실제 로깅 처리를 위한 객체를 생성하고 초기화합니다.

		Returns:
			logging.Logger: 로깅처리 실 객체
		"""
		# intialize logger
		log = logging.getLogger(self.log_filename)
		log.setLevel(self.log_level) 

		# Make file handler
		LOG_FILENAME = self.log_path + '/' + self.log_filename + self.log_ext
		file_handler = logging.handlers.TimedRotatingFileHandler(
			filename = LOG_FILENAME, when = 'midnight', interval = 1
			, backupCount = 100, encoding = 'utf-8'
		) # Rotate at midnight
		file_handler.suffix = "%Y%m%d" # add file date

		formatter = logging.Formatter(
			'%(asctime)s %(levelname)s %(lineno)d] %(message)s'
		)
		log.addHandler(file_handler)
		file_handler.setFormatter(formatter)
		if (self.log_console == True):
			stream_handler = logging.StreamHandler()
			log.addHandler(stream_handler)
			stream_handler.setFormatter(formatter)
		#log.debug('created')
		file_handler.rotator = GZipRotator() # 압축 분할 처리

		return log


	def critical(self, msg, *args, **kwargs):
		if self.__log != None:
			self.__log.critical(msg, *args, **kwargs)


	def debug(self, msg, *args, **kwargs):
		if self.__log != None:
			self.__log.debug(msg, *args, **kwargs)


	def error(self, msg, *args, **kwargs):
		if self.__log != None:
			self.__log.error(msg, *args, **kwargs)


	def info(self, msg, *args, **kwargs):
		if self.__log != None:
			self.__log.info(msg, *args, **kwargs)


	def warning(self, msg, *args, **kwargs):
		if self.__log != None:
			self.__log.warning(msg, *args, **kwargs)


def createLogger(log_path = './logs'
			, log_filename = 'logger'
			, log_ext = '.log'
			, log_level = logging.WARNING
			, log_console = True):
	"""Logger 클래스를 초기화합니다.

	Args:
		log_path (string): 로깅 파일이 쌓이는 폴더 경로 ; "./logs"
		log_filename (string): 로깅 파일 이름 ; "logger"
		log_ext (string): 로깅 파일 기본 확장자 ; ".log"
		log_level : 로깅 레벨 = logging.DEBUG (10), logging.INFO (20), logging.WARNING (30), logging.ERROR (40), logging.CRITICAL (50)
		log_console (boolean): 콘솔로도 로깅 출력 여부
	"""

	# intialize logger
	log = logging.getLogger(log_filename)
	log.setLevel(log_level) 

	# Make file handler
	LOG_FILENAME = log_path + '/' + log_filename + log_ext
	file_handler = logging.handlers.TimedRotatingFileHandler(
		filename = LOG_FILENAME, when = 'midnight', interval = 1
		, backupCount = 100, encoding = 'utf-8'
	) # Rotate at midnight
	file_handler.suffix = "%Y%m%d" # add file date

	formatter = logging.Formatter(
		'%(asctime)s %(levelname)s %(lineno)d] %(message)s'
	)
	log.addHandler(file_handler)
	file_handler.setFormatter(formatter)
	if (log_console == True):
		stream_handler = logging.StreamHandler()
		log.addHandler(stream_handler)
		stream_handler.setFormatter(formatter)
	#log.debug('created')
	file_handler.rotator = GZipRotator() # 압축 분할 처리

	return log


# Testing at shell
if __name__ == '__main__':
	log = FileLogger(log_filename = 'logger_test', log_level = logging.DEBUG)
	log.debug('debug?')
	log.info('info?')
	log.warning('warning?')
	log.error('error?')
	log.critical('critical?')
