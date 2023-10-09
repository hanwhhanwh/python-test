# gather YA-MOON sample 1
# make hbesthee@naver.com
# date 2023-10-03

from bs4 import BeautifulSoup, PageElement, Tag
from datetime import datetime
from logging import getLogger, Logger
from os import path, makedirs, remove
from time import sleep
from typing import Final
from urllib.parse import urlparse
from urllib3 import request

import requests


from avdb_data_model import AvdbDataModel
import avdb_constants as const

import sys
sys.path.append( path.abspath('../..') )
from lib.file_logger import createLogger
from lib.json_util import get_dict_value, init_conf_files, make_init_folders, load_json_conf, save_json_conf


LOGGER_LEVEL_DEBUG: Final				= 10
LOGGER_NAME: Final						= 'yamoon'

URL_HOST_YAMOON: Final					= 'ya-moon.com'

DOM_PATH_AV_LIST: Final					= '#fboardlist > div.list-container'
DOM_PATH_SUB_INFO: Final				= 'body > div.wrapper > div.container.content > div:nth-child(1) > div.col-md-3.col-sm-12 > div.panel.panel-default'

DEFAULT_HEADERS: Final					= {
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
	, 'Accept-Language': 'ko-KR,ko;q=0.9'
	, 'Cache-Control': 'no-cache'
	, 'Connection': 'keep-alive'
	, 'Cookie': '_ga=GA1.1.485726505.1696248254; filemanagercookie=hbesthee; member%5Finfo=grade=333&membercolor=lightskyblue&username=hbesthee&regtext=%EC%9D%BC%EB%B0%98&regcolor=btn%2Du%2Dblue&getetc=0&gradepoint=&loginsave=off&readok=no; ASPSESSIONIDCWATTCBA=AACENJCBPHINEEDPCGBJNNGM; _ga_N6N5N6RS06=GS1.1.1696318895.4.1.1696321601.2.0.0'
	, 'Pragma': 'no-cache'
	, 'Sec-Fetch-Dest': 'document'
	, 'Sec-Fetch-Mode': 'navigate'
	, 'Sec-Fetch-Site': 'none'
	, 'Sec-Fetch-User': '?1'
	, 'Upgrade-Insecure-Requests': '1'
	, 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
	, 'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"'
	, 'sec-ch-ua-mobile': '?0'
	, 'sec-ch-ua-platform': '"Windows"'
}

DEF_YAMOON_CONF_FILE: Final				= '../../conf/yamoon_script.json'







def getMagnetAddr(magnet_tag: Tag) -> str:
	""" 주어진 주소로부터 마그넷 다운로드 정보를 받아와 반환합니다.

	Args:
		url (str): 마그넷 다운로드 정보를 받을 URL

	Returns:
		str: 마그넷 다운로드 정보. 찾지 못한 경우에는 None을 반환합니다.
	"""
	if (magnet_tag == None):
		_logger.warning(f'not found btn-magnet')
		return None

	magnet_url = None
	onclick: str = magnet_tag.get('onclick')
	# print(onclick)
	pos1 = onclick.find("'")
	if (pos1 >= 0):
		pos1 += 1
		pos2 = onclick.find("'", pos1)
		if (pos2 >= 0):
			magnet_url = f'https://{URL_HOST_AVGOSU}{onclick[pos1:pos2]}'

	url = magnet_url
	if ( (url == None) or (url.strip() == '') ):
		_logger.warning(f'not found magnet_url')
		return None

	for _ in range(DEF_RETRY_COUNT):
		response = requests.get(url, headers = DEFAULT_HEADERS)
		if (response.status_code == 200):
			html = response.text
			pos1 = html.find('magnet:?')
			if (pos1 >= 0):
				pos2 = html.find('"', pos1)
				if (pos2 >= 0):
					magnet_addr = html[pos1:pos2]
					return (magnet_addr)
		else:
			_logger.warning(f'magnet_url requests fail! {_ + 1} ; {response.status_code=}')
		sleep(DEF_RETRY_WAIT_TIME)
	_logger.warning(f'retry fail!')
	return None




class YamoonScriptCrawler:
	""" Yamoon script crawler """

	def __init__(self) -> None:
		""" 수집기 기본 생성자 """
		self._header = DEFAULT_HEADERS
		self._is_local = False

		make_init_folders(('../../logs', '../../db', '../../conf'))
		self._logger: Logger = createLogger(log_path = '../../logs', log_filename = LOGGER_NAME, log_level = LOGGER_LEVEL_DEBUG)


	def getChildCount(self, a_tag) -> int:
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


	def fetchHtmlSource(self, url: str) -> str:
		""" 주어진 URL에서 HTML 소스를 받아 반환합니다.

		Args:
			url (str): HTML 정보를 받아올 URL 주소

		Returns:
			str: URL에서 가져온 HTML 소스 문자열
		"""
		html = ''
		for _ in range(const.DEF_RETRY_COUNT):
			response = requests.get(url, headers = self._header)
			if (response.status_code == 200):
				html = response.text
				break
			else:
				self._logger.warning(f'fetch HTML fail {_ + 1} : {response.status_code=} : {url}')

			sleep(const.DEF_RETRY_WAIT_TIME)

		self._logger.debug(f'HTML source {len(html)=}')
		return html


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
			url = f'https://www.ya-moon.com/newboard/yamoonboard/board-read.asp?fullboardname=yamoonmemberboard&mtablename=subtitled&num={board_no}'

			html = self.fetchHtmlSource(url)

		return html.replace('\r\n', '').replace('\n', '')


	def fetchListHtmlSource(self, page_no: int = 1) -> str:
		""" 목록 부분에 대한 HTML 소스를 얻어오기

		Args:
			page_no (int): 목록의 페이지 번호

		Returns:
			str: _description_
		"""
		html: str = ''
		if (self._is_local):
			# with open('./ym/list.html', encoding = 'UTF-8', newline = '\n') as f:
			with open('./ym/list.html', encoding = 'UTF-8') as f:
				html = f.read()
		else:
			url = f'https://www.ya-moon.com/newboard/yamoonboard/board-list.asp?fullboardname=yamoonmemberboard&mtablename=subtitled&page={page_no}'

			html = self.fetchHtmlSource(url)

		return html.replace('\r\n', '').replace('\n', '')


	def init(self) -> int:
		try:
			headers, error_message = load_json_conf('../../conf/yamoon_header.json')
			if (error_message != None):
				self._logger.error(f'Header loading fail! : {error_message}')
				return const.ERR_HEADER_LOADING
			else:
				self._header = headers
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

			script_info[const.CN_SCRIPT_NAME] = a_tag.text.strip()
			script_info[const.CN_SCRIPT_FILE_URL] = f'https://{URL_HOST_YAMOON}{a_tag.get('href')}'
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
			# self._logger.debug(f'  parsing {td_index=}: {info}')
			info_list.append(info)

		self._logger.info(f'parsed info count = {len(info_list)}')
		return 0
		connection, cursor, error_code = connect_database(_conf.get(JSON_DB))
		if (error_code != 0):
			self._logger.error(f'database connection fail : {error_code}')
			sys.exit(error_code)

		for item_index, av_list_item in enumerate(table_tag.children, start = 1):
			# 기본 정보 가져오기
			info = dict()
			a_tag = av_list_item.find('a')
			info[const.CN_DETAIL_URL] = a_tag.get('href')
			title: str = a_tag.get('title')
			first_space = title.index(' ')
			info[const.CN_FILM_ID] = title[:first_space]
			info[const.CN_TITLE] = title[first_space + 1:]
			size_info_tag = av_list_item.find('span')
			info[const.CN_FILE_SIZE] = size_info_tag.text
			date_info_tag = size_info_tag.next_sibling
			date_info: str = date_info_tag.text
			if (date_info.find(':') < 0):
				date_info = f'{datetime.now().year}-{date_info}'
			else:
				today = datetime.now().strftime("%Y-%m-%d")
				date_info = f'{today} {date_info}'
			info[const.CN_DATE] = date_info

			self._logger.info(f'getDetailInfo : {info[const.CN_FILM_ID]} / {info[const.CN_FILE_SIZE]} / {info[const.CN_DATE]}')
			if (getDetailInfo(info)):
				ret = insert(connection, cursor, info)
				if (ret == const.ERR_DB_INTEGRITY):
					return const.ERR_DB_INTEGRITY
				info_list.append(info)
			else:
				self._logger.warning(f'Fetch fail of detail info! : {info}')

		self._logger.info(f'parsed info count = {len(info_list)}')
		return 0


	def setLocalMode(self) -> None:
		""" 디버깅 모드로 설정합니다. """
		self._is_local = True



def main() -> None:
	""" 실행 부 """


	ysc = YamoonScriptCrawler()
	ret = ysc.init()
	if (ret != 0):
		print(f'Internal Error (init): {ret=}')
	ysc.setLocalMode()

	page_no = 1
	html = ysc.fetchListHtmlSource(page_no)
	print(f'list HTML {len(html)=}')

	info_list = list()
	ret = ysc.parseScriptList(info_list, html)
	if (ret != 0):
		print(f'Internal Error (parseScriptList): {ret=}')
		return ret

	info = info_list.pop()
	html = ysc.fetchDetailHtmlSource(info.get(const.CN_YAMOON_BOARD_NO))
	print(f'detail HTML {len(html)=}')

	script_info_list = list()
	ret = ysc.parseDetailInfo(script_info_list, info, html)
	if (ret != 0):
		print(f'Internal Error (parseDetailInfo): {ret=}')
		return ret


	return 0


	if (False):
		_conf, error_msg = load_json_conf(DEF_YAMOON_CONF_FILE)
		if (_conf == None):
			_logger.warning(error_msg)
			_conf = DEF_CONF_AVGOSU
			save_json_conf(DEF_YAMOON_CONF_FILE, _conf)
		# print(_conf)

		# connection, cursor, error_code = connect_database(_conf.get(JSON_DB))
		# if (error_code != 0):
		# 	sys.exit(error_code)

		is_ended = False
		info_list = list()
		# _limit_page_count = get_dict_value(_conf, JKEY_LIMIT_PAGE_COUNT, DEF_LIMIT_PAGE_COUNT)
		_limit_page_count = 1
		for page_no in range(_limit_page_count):
			page_no += 1
			_logger.info(f'try parsing {page_no=}')
			url = f'https://www.ya-moon.com/newboard/yamoonboard/board-list.asp?fullboardname=yamoonmemberboard&mtablename=subtitled&page={page_no}'

			for _ in range(DEF_RETRY_COUNT):
				response = requests.get(url, headers = DEFAULT_HEADERS)
				if (response.status_code == 200):
					html = response.text
					# print(html)
					ret = parseScriptList(info_list, html)
					if (ret == ERR_DB_INTEGRITY):
						is_ended = True
					break
				else:
					_logger.warning(f'detail info reqest fail {_ + 1} : {response.status_code=}')
				sleep(DEF_RETRY_WAIT_TIME)

			if (is_ended):
				break
		# for info in info_list:
		# 	insert(connection, cursor, info)
		_logger.info(f'end: {len(info_list)} info parsed')


if __name__ == '__main__':

	main()
