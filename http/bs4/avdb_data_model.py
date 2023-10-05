# Data model for AVDB
# make hbesthee@naver.com
# date 2023-10-03

from logging import Logger, getLogger
from mysql.connector.errors import IntegrityError
from sqlalchemy import create_engine


from avdb_constants import *



class AvdbDataModel:
	""" 자료 처리를 위한 데이터 모델 클래스	"""

	def __init__(self) -> None:
		""" 데이터 모델 기본 생성자
		"""
		self._engine = None # sqlalchemy engine 객체
		self._connection = None # 데이터베이스 연결 객체
		self._cursor = None # 데이터베이스 커서 객체
		self._logger: Logger = getLogger() # 로깅 처리 객체


	def connectDatabase(self, conf: dict) -> tuple:
		""" 주어진 DB 연결정보를 바탕으로 데이터베이스 연결을 시도합니다.

		Args:
			conf (dict): 데이터베이스 연결에 필요한 상세 정보가 담겨있는 객체

		Returns:
			tuple: (connection, cursor, result_code) : result_code : 0 = 성공, -1 = 오류 발생 (세부 오류 내용은 로그 파일 확인하기)
		"""
		db_url = f"mysql+mysqlconnector://{conf.get(JKEY_USERNAME)}:{conf.get(JKEY_PASSWORD)}@{conf.get(JKEY_DB_HOST)}:{conf.get(JKEY_DB_PORT)}/{conf.get(JKEY_DB_NAME)}?charset=utf8mb4&collation=utf8mb4_general_ci"
		self._logger.debug(f'connecting... : {conf.get(JKEY_DB_HOST)}:{conf.get(JKEY_DB_PORT)}/{conf.get(JKEY_DB_NAME)}')
		self._engine = create_engine(db_url, encoding = conf.get(JKEY_DB_ENCODING))
		if self._engine == None:
			# 데이터베이스 연결을 위한 엔진 객체 얻기 실패
			self._logger.error(f'database engine fail!')
			return None, None, -1

		try:
			self._connection = self._engine.raw_connection()
		except Exception as e: # 데이터베이스 연결 실패
			self._logger.error(f'database connection fail! >> {e}')
			return None, None, -1

		try:
			self._cursor = self._connection.cursor()  # get Database cursor
		except Exception as e: # Database cursor fail
			self._logger.error(f'database cursor fail! >> {e}')
			return None, None, -1

		return self._connection, self._cursor, 0


	def insertAvgosu(self, avgosu_info: dict) -> int:
		""" 수집한 AVGOSU 정보를 등록합니다.

		Args:
			avgosu_info (dict): AVGOSU에서 수집한 정보

		Returns:
			int: 수집한 정보 등록 성공 여부. 0 = 성공, 1 = 이미 동일 정보가 존재함, -1 = 기타 오류 (상세 정보는 오류 로그 확인 필요)
		"""
		try:
			query_insert = f"""
INSERT INTO `AVGOSU`
(
	{CN_DETAIL_URL}, {CN_TITLE}, {CN_FILM_ID}, {CN_DATE}, {CN_FILE_SIZE}
	, {CN_COVER_IMAGE_URL}, {CN_THUMBNAIL_URL}, {CN_MAGNET_ADDR}
)
VALUES
(
	%s, %s, %s, %s, %s
	, %s, %s, %s
)
	;"""
			self._cursor.execute(query_insert, (avgosu_info.get(CN_DETAIL_URL), avgosu_info.get(CN_TITLE), avgosu_info.get(CN_FILM_ID), avgosu_info.get(CN_DATE), avgosu_info.get(CN_FILE_SIZE)
							, avgosu_info.get(CN_COVER_IMAGE_URL), avgosu_info.get(CN_THUMBNAIL_URL), avgosu_info.get(CN_MAGNET_ADDR)))
			avgosu_no = self._cursor.lastrowid
			if avgosu_no == 0 or avgosu_no == None:
				self._logger.error(f'insert execution fail : avgosu info')
			self._connection.commit()
		except IntegrityError as ie:
			self._logger.info(f'duplicated info : {avgosu_info.get(CN_FILM_ID)} / {avgosu_info.get(CN_FILE_SIZE)} / {avgosu_info.get(CN_DATE)} : {ie}')
			return ERR_DB_INTEGRITY
		except Exception as e:
			self._logger.error(f'insert execution fail : avgosu info2 >> {e}')
			return ERR_DB_INTERNAL

		return avgosu_no


	def insertYamoonScript(self, yamoon_script: dict) -> int:
		""" 수집한 자막 정보를 등록합니다.

		Args:
			info (dict): 수집한 자막 정보

		Returns:
			int: 수집한 정보 등록 성공 여부. 0 = 성공, 1 = 이미 동일 정보가 존재함, -1 = 기타 오류 (상세 정보는 오류 로그 확인 필요)
		"""
		try:
			query_insert = f"""
INSERT INTO `SCRIPT_YAMOON`
(
	{CN_DETAIL_URL}, {CN_TITLE}, {CN_FILM_ID}, {CN_DATE}, {CN_FILE_SIZE}
	, {CN_COVER_IMAGE_URL}, {CN_THUMBNAIL_URL}, {CN_MAGNET_ADDR}
)
VALUES
(
	%s, %s, %s, %s, %s
	, %s, %s, %s
)
	;"""
			self._cursor.execute(query_insert, (yamoon_script.get(CN_DETAIL_URL), yamoon_script.get(CN_TITLE), yamoon_script.get(CN_FILM_ID), yamoon_script.get(CN_DATE), yamoon_script.get(CN_FILE_SIZE)
							, yamoon_script.get(CN_COVER_IMAGE_URL), yamoon_script.get(CN_THUMBNAIL_URL), yamoon_script.get(CN_MAGNET_ADDR)))
			script_yamoon_no = self._cursor.lastrowid
			if script_yamoon_no == 0 or script_yamoon_no == None:
				self._logger.error(f'insert execution fail : yamoon_script info')
			self._connection.commit()
		except IntegrityError as ie:
			self._logger.info(f'duplicated info : {yamoon_script.get(CN_FILM_ID)} / {yamoon_script.get(CN_FILE_SIZE)} / {yamoon_script.get(CN_DATE)} : {ie}')
			return ERR_DB_INTEGRITY
		except Exception as e:
			self._logger.error(f'insert execution fail : yamoon_script info2 >> {e}')
			return ERR_DB_INTERNAL

		return script_yamoon_no


	def setLogger(self, logger: Logger) -> None:
		""" 로깅 객체를 설정합니다.

		Args:
			logger (Logger): 변경할 로깅 객체
		"""
		self._logger = logger
