# gather YA-MOON sample 1
# make hbesthee@naver.com
# date 2023-10-03

from bs4 import BeautifulSoup, PageElement, Tag
from datetime import datetime
from logging import getLogger, Logger
from os import path, makedirs, remove
from requests import get as get_req, post as post_req
from time import sleep
from typing import Final
from urllib.parse import urlparse
from urllib3 import request


from avdb_data_model import AvdbDataModel
from base_crawler import BaseBoardCrawler
import avdb_constants as const

import sys
sys.path.append( path.abspath('../..') )
from lib.file_logger import createLogger
from lib.json_util import get_dict_value, init_conf_files, make_init_folders, load_json_conf, save_json_conf


LOGGER_LEVEL_DEBUG: Final				= 10
LOGGER_NAME: Final						= 'yamoon'

URL_HOST_YAMOON: Final					= 'www.ya-moon.com'

DOM_PATH_AV_LIST: Final					= '#fboardlist > div.list-container'
DOM_PATH_SUB_INFO: Final				= 'body > div.wrapper > div.container.content > div:nth-child(1) > div.col-md-3.col-sm-12 > div.panel.panel-default'

DEFAULT_HEADERS: Final					= {
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
	, 'Accept-Encoding': 'gzip, deflate, br'
	, 'Accept-Language': 'ko-KR,ko;q=0.9'
	, 'Cache-Control': 'no-cache'
	, 'Connection': 'keep-alive'
	, 'Cookie': '_ga=GA1.1.1671706350.1696760343; filemanagercookie=hbesthee; ckCsrfToken=noF6XP41ac8kk970a5O7UC49pNFHs4xoOYY01hpv; ASPSESSIONIDCQCUSCAB=CLOPFFCBEMOCFLFNLDEPLOLB; member%5Finfo=username=hbesthee&grade=333&membercolor=lightskyblue&regtext=%EC%9D%BC%EB%B0%98&regcolor=btn%2Du%2Dblue&getetc=0&gradepoint=&loginsave=off&readok=no; ASPSESSIONIDAUERTCAA=ABPNDBPBKNLAENLGFNCMHFDA; _ga_N6N5N6RS06=GS1.1.1696852550.10.1.1696852552.58.0.0'
	, 'Host': 'www.ya-moon.com'
	, 'Pragma': 'no-cache'
	, 'Sec-Fetch-Dest': 'document'
	, 'Sec-Fetch-Mode': 'navigate'
	, 'Sec-Fetch-Site': 'none'
	, 'Sec-Fetch-User': '?1'
	, 'Upgrade-Insecure-Requests': '1'
	, 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
	, 'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"'
	, 'sec-ch-ua-mobile': '?0'
	, 'sec-ch-ua-platform': '"Windows"'
}

DEF_YAMOON_CONF_FILE: Final				= '../../conf/yamoon_script.json'

DEF_CONF_YAMOON: Final					= {
	const.JSON_DB: {
		const.JKEY_DB_HOST: 'localhost'
		, const.JKEY_DB_PORT: '3306'
		, const.JKEY_DB_NAME: 'MyDB'
		, const.JKEY_DB_ENCODING: const.DEF_DB_ENCODING
		, const.JKEY_USERNAME: 'username'
		, const.JKEY_PASSWORD: 'password'
	}
	, const.JKEY_LIMIT_PAGE_COUNT: const.DEF_LIMIT_PAGE_COUNT
}







class YamoonScriptCrawler(BaseBoardCrawler):
	""" Yamoon script crawler """

	def __init__(self) -> None:
		""" 수집기 기본 생성자 """
		super(YamoonScriptCrawler, self).__init__()

		self._headers = DEFAULT_HEADERS

		make_init_folders(('../../logs', '../../db', '../../conf'))
		self._logger: Logger = createLogger(log_path = '../../logs', log_filename = LOGGER_NAME, log_level = LOGGER_LEVEL_DEBUG)


	def downloadScriptFile(self, to_file: str, info: dict) -> str:
		""" 주어진 URL을 파일로 다운로드 받습니다.

		Args:
			to_file (str): 다운로드 받아서 저장될 파일 경로
			info (dict): 자막 파일 정보

		Returns:
			str: URL에서 가져온 HTML 소스 문자열
		"""
		url = f'https://{URL_HOST_YAMOON}{info.get(const.CN_SCRIPT_FILE_URL)}'
		try:
			file = get_req(url, headers = self._headers)
		except Exception as e:
			self._logger.error(f'url request fail: {url=} ; {e}')
			return const.ERR_FAIL_REQUEST
		try:
			open(to_file, 'wb').write(file.content)
		except Exception as e:
			self._logger.error(f'file download fail: {to_file=} << {url=} ; {e}')
			return const.ERR_DOWNLOAD_FILE

		return 0


	def fetchDetailHtmlSource(self, board_no: int = 1) -> str:
		""" 상세 정보에 대한 HTML 소스를 얻어오기

		Args:
			board_no (int): 게시글의 번호

		Returns:
			str: _description_
		"""
		html: str = ''
		if (self._is_local):
			with open('./ym/detail.html', encoding = 'UTF-8') as f:
				html = f.read()
		else:
			url = f'https://{URL_HOST_YAMOON}/newboard/yamoonboard/board-read.asp?fullboardname=yamoonmemberboard&mtablename=subtitled&num={board_no}'

			html = self.fetchHtmlSource(url)

		return html.replace('\r\n', '').replace('\n', '')


	def fetchListHtmlSource(self, page_no: int = 1) -> str:
		""" 목록 부분에 대한 HTML 소스를 얻어오기

		Args:
			page_no (int): 목록의 페이지 번호

		Returns:
			str: 목록에 대한 HTML 소스
		"""
		html: str = ''
		if (self._is_local):
			with open('./ym/list.html', encoding = 'UTF-8') as f:
				html = f.read()
		else:
			url = f'https://{URL_HOST_YAMOON}/newboard/yamoonboard/board-list.asp?fullboardname=yamoonmemberboard&mtablename=subtitled&page={page_no}'

			html = self.fetchHtmlSource(url)

		return html.replace('\r\n', '').replace('\n', '')


	def init(self) -> int:
		self.initConf(DEF_YAMOON_CONF_FILE, DEF_CONF_YAMOON)

		self._db = AvdbDataModel()
		self._db.setLogger(self._logger)
		self._db.connectDatabase(self._conf.get(const.JSON_DB))

		try:
			headers, error_message = load_json_conf('../../conf/yamoon_header.json')
			if (error_message != None):
				self._logger.error(f'Header loading fail! : {error_message}')
				return const.ERR_HEADER_LOADING
			else:
				self._headers = headers
		except Exception as e:
			self._logger.error(f'Header loading error : {e}')
			return const.ERR_HEADER_LOADING2

		return 0


	def parseDetailInfo(self, script_list: list, info: dict, html: str) -> int:
		""" yamoon에서 수집한 기본 정보를 바탕으로 보다 자막파일 정보들을 추출합니다.

		Args:
			script_list (list): 상세 정보에서 수집한 자막파일 목록
			info (dict): yamoon에서 수집한 기본 정보가 담겨있는 객체
			html (str): 상세 정보에 대한 HTML 소스

		Returns:
			int: 정보 획득 성공 여부. 0 = 성공, else 오류 코드
		"""
		soup = BeautifulSoup(html, 'html.parser')
		if (soup == None):
			self._logger.error(f'hml.parser error')
			return const.ERR_BS4_PARSER_FAIL
		
		content_tag: Tag = soup.find('div', id = 'read-content')
		if (content_tag == None):
			self._logger.warning(f'"read-content" div tag not found')
			return const.ERR_BS4_ELM_NOT_FOUND
		
		a_tags = content_tag.find_all('a')
		for a_index, a_tag in enumerate(a_tags):
			script_info = dict()
			script_info[const.CN_YAMOON_BOARD_NO]	= info.get(const.CN_YAMOON_BOARD_NO)
			script_info[const.CN_UPLOADER]			= info.get(const.CN_UPLOADER)
			script_info[const.CN_TITLE]				= info.get(const.CN_TITLE)
			script_info[const.CN_BOARD_DATE]		= info.get(const.CN_BOARD_DATE)
			script_info[const.CN_DETAIL_URL]		= info.get(const.CN_DETAIL_URL)

			script_name = a_tag.text.strip()
			try:
				film_id = path.splitext(script_name)[0].replace('[', '').replace(']', ' ').replace('_', ' ').split(' ')[0]
			except Exception as e:
				self._logger.warning(f'not found film_id : {script_name=}')
				film_id = None
			script_info[const.CN_SCRIPT_NAME] = script_name
			script_info[const.CN_FILM_ID] = film_id
			script_info[const.CN_SCRIPT_FILE_URL] = a_tag.get("href")
			self._logger.debug(f'  parsing {a_index=}: {script_info}')
			script_list.append(script_info)
		return 0


	def parseScriptList(self, info_list: list, html: str) -> int:
		""" 주어진 HTML 내용을 파싱히여 AV 정보를 가져옵니다.

		Args:
			info_list (list): AV 정보가 저장될 list 객체
			html (str): 파싱할 HTML 내용

		Returns:
			int: 파싱 성공 여부. 필수 항목들을 모두 가져왔는가?
		"""
		soup = BeautifulSoup(html, 'html.parser')
		if (soup == None):
			self._logger.error(f'hml.parser error')
			return const.ERR_BS4_PARSER_FAIL

		# 주요 목록 정보
		table_tag = soup.find('table', 'table table-striped table-bordered table-inside-border-0 margin-bottom--1')
		if (table_tag == None):
			self._logger.error(f'not found info list element(<TABLE>).')
			return const.ERR_BS4_ELM_NOT_FOUND

		for _, tr_tag in enumerate(table_tag.children):
			if ((tr_tag.name == None) or (self.getChildCount(tr_tag) < 11) ):
				continue # 정보가 없는 항목은 건너뜀

			info = dict()
			for td_index, td_tag in enumerate(tr_tag.children):
				if (td_index == 1): # 번호
					info[const.CN_YAMOON_BOARD_NO] = td_tag.next_element.text.strip()
				elif (td_index == 3): # 올린이
					info[const.CN_UPLOADER] = td_tag.select_one('a').text.strip()
				elif (td_index == 5): # 제목
					info[const.CN_TITLE] = td_tag.select_one('a').text.strip()
				elif (td_index == 7): # 게시판에 올린 날짜
					info[const.CN_BOARD_DATE] = f'20{td_tag.text.strip()}'.replace('/', '-')

			# info[const.CN_DETAIL_URL] = f'https://{URL_HOST_YAMOON}/newboard/yamoonboard/board-read.asp?fullboardname=yamoonmemberboard&mtablename=subtitled&num={info.get(const.CN_YAMOON_BOARD_NO)}'
			# self._logger.debug(f'  parsing {td_index=}: {info}')
			info_list.append(info)

		self._logger.info(f'parsed info count = {len(info_list)}')
		return 0


	def run(self) -> int:
		""" yamoon 자목 게시판 자료를 수집 처리합니다. """
		ret = self.init()
		if (ret != 0):
			print(f'Internal Error (init): {ret=}')
		# self.setLocalMode()

		page_count = get_dict_value(self._conf, const.JKEY_LIMIT_PAGE_COUNT, const.DEF_LIMIT_PAGE_COUNT)
		page_count = 46
		# for page_no in range(1, page_count + 1):
		for page_no in range(page_count, 0, -1):
			self._logger.info(f'게시판 수집 시작 : {page_no=}')
			html = self.fetchListHtmlSource(page_no)
			if (html == ''):
				self._logger.info(f'게시판 HTML 소스 가져오기 실패')
				break

			info_list = list()
			ret = self.parseScriptList(info_list, html)
			if (ret != 0):
				self._logger.error(f'Internal Error (parseScriptList): {ret=}')
				return ret

			info_count = len(info_list)
			for info_index in range(info_count):
				info = info_list[info_index]
				html = self.fetchDetailHtmlSource(info.get(const.CN_YAMOON_BOARD_NO))
				if (html == ''):
					self._logger.info(f'게시글 HTML 소스 가져오기 실패')
					break

				script_info_list = list()
				ret = self.parseDetailInfo(script_info_list, info, html)
				if (ret != 0):
					self._logger.error(f'Internal Error (parseDetailInfo): {ret=}')
					return ret

				if (len(script_info_list) == 0):
					continue

				inserted_count = 0
				for script_info in script_info_list:
					yamoon_no = self._db.insertYamoonScript(script_info)
					if (yamoon_no > 0):
						inserted_count += 1
						to_file = f'./scripts/{script_info.get(const.CN_SCRIPT_NAME)}'
						self.downloadScriptFile(to_file, script_info)

				if (inserted_count == 0):
					self._logger.info(f'crawling end.')
					return 0

			sleep(300 + page_no)


	def setLocalMode(self) -> None:
		""" 디버깅 모드로 설정합니다. """
		self._is_local = True



def main() -> int:
	""" 실행 부 """
	ysc = YamoonScriptCrawler()
	ret = ysc.run()

	return ret



if __name__ == '__main__':

	main()
