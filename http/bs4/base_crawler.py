# BASE crawler
# make hbesthee@naver.com
# date 2023-10-09

from bs4 import BeautifulSoup, Tag
from logging import getLogger, Logger
from os import path
from requests import get as get_req
from time import sleep
from typing import Final


import sys
sys.path.append( path.abspath('../..') )
from lib.file_logger import createLogger
from lib.json_util import get_dict_value, init_conf_files, make_init_folders, load_json_conf, save_json_conf


DEF_RETRY_COUNT: Final					= 3 # request를 다시 시도할 회수
DEF_RETRY_WAIT_TIME: Final				= 3 # request를 다시 시도하기 전 대기시간 (초)
DEF_DB_ENCODING: Final					= 'utf-8'



class BaseBoardCrawler:
	""" 게시판 수집기 부모 클래스 """

	def __init__(self) -> None:
		""" 수집기 기본 생성자 """
		self._logger: Logger = getLogger() # 기본 로거
		self._headers: dict = None # 헤더 정보
		self._db = None # 데이터 모델
		self._is_local = False


	def fetchHtmlSource(self, url: str) -> str:
		""" 주어진 URL에서 HTML 소스를 받아 반환합니다.

		Args:
			url (str): HTML 정보를 받아올 URL 주소

		Returns:
			str: URL에서 가져온 HTML 소스 문자열
		"""
		html = ''
		for retry_index in range(1, DEF_RETRY_COUNT + 1):
			try:
				response = get_req(url, headers = self._headers)
			except Exception as e:
				self._logger.warning(f'request fail {url=} : {e}')
				continue
			if (response.status_code == 200):
				html = response.text
				break
			else:
				self._logger.warning(f'fetch HTML fail {retry_index} : {response.status_code=} : {url}')

			sleep(DEF_RETRY_WAIT_TIME)

		self._logger.debug(f'HTML source {len(html)=}')
		return html


	def getChildCount(self, a_tag: Tag) -> int:
		""" 자식 엘리먼트의 개수를 반환합니다.

		Args:
			a_tag (_type_): 태그 정보

		Returns:
			int: 태그의 자식 엘리먼트 개수
		"""
		count = 0
		if ( (a_tag == None) or (not hasattr(a_tag, 'children')) ):
			return count

		for _ in a_tag.children:
			count += 1

		return count


	def fetchDetailHtmlSource(self, board_no: int = 1) -> str:
		""" 상세 정보에 대한 HTML 소스를 얻어오기

		Args:
			board_no (int): 게시글의 번호

		Returns:
			str: 게시글에 대한 HTML 소스
		"""
		html: str = ''

		return html


	def init(self) -> int:
		""" 수집기 초기화를 수행합니다.

		Returns:
			int: 초기화 수행 결과. 0 = success, else internal error
		"""
		pass


	def initConf(self, conf_file: str, def_conf: dict) -> None:
		""" 설정 파일을 로딩합니다.

		Args:
			conf_file (str): 설정 파일 (*.json) 경로
			def_conf (dict): 기본 설정 정보
		"""
		self._conf, error_msg = load_json_conf(conf_file)
		if (self._conf == None):
			self._logger.warning(error_msg)
			self._conf = def_conf
			save_json_conf(conf_file, self._conf)
		# self._logger.debug(_conf)



	def fetchListHtmlSource(self, page_no: int = 1) -> str:
		""" 목록 부분에 대한 HTML 소스를 얻어오기

		Args:
			page_no (int): 목록의 페이지 번호

		Returns:
			str: 목록에 대한 HTML 소스
		"""
		html: str = ''

		return html


	def loadHeader(self, header_file: str) -> dict:
		""" 헤더 파일 정보를 로딩합니다. 헤더 정보를 읽지 못한 경우에는 None를 반환합니다.

		Args:
			header_file (str): 헤더 정보가 들어 있는 파일 경로 문자열

		Returns:
			dict: 변환된 헤더 정보. 읽지 못한 경우에는 None
		"""
		if (not path.exists(header_file)):
			return None

		header = dict()
		f = open(header_file, mode = "rt", encoding = "utf-8", newline = '\n')
		lines = f.read().splitlines()
		for line in lines:
			if (not line.startswith("  -H '")):
				continue

			items = line[6:-3].split(': ')
			if (len(items) != 2):
				continue
			header[items[0]] = items[1]
		f.close()

		return header


	def parseDetailInfo(self, info: dict, html: str) -> int:
		""" 게시글 상세 정보를 수집합니다.

		Args:
			info (dict): 게시글 기본 정보가 담겨있는 객체
			html (str): 게시글 상세 정보에 대한 HTML 소스

		Returns:
			int: 정보 획득 성공 여부. 0 = 성공, else 오류 코드
		"""
		return 0


	def parseList(self, info_list: list, html: str) -> int:
		""" 게시판 목록을 분석하여 목록 정보를 분석합니다.

		Args:
			info_list (list): 게시글 정보가 담길 list 객체
			html (str): 파싱할 게시판 목록 HTML 내용

		Returns:
			int: 파싱 성공 여부. 필수 항목들을 모두 가져왔는가?
		"""
		return 0


	def run(self) -> int:
		""" 게시판 자료를 수집합니다.

		Returns:
			int: 성공 여부. 0 = 성공, else 오류 코드
		"""
		return 0


if (__name__ == '__main__'):

	c = BaseBoardCrawler()
	header = c.loadHeader('hellven-header.txt')
	print(header)