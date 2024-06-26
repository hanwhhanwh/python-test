# gather hellven sample 1
# make hbesthee@naver.com
# date 2024-01-04

from bs4 import BeautifulSoup, PageElement, Tag
from cloudscraper import create_scraper
from datetime import datetime
from logging import getLogger, Logger
from mysql.connector.errors import IntegrityError
from os import path, makedirs, remove
from re import compile as reg_compile
from sqlalchemy import create_engine
from time import sleep
from typing import Final
from urllib.parse import urlparse
from urllib3 import request

import requests

from avdb_data_model import AvdbDataModel
from base_crawler import BaseBoardCrawler
import avdb_constants as const

import sys
sys.path.append( path.abspath('../..') )
from lib.file_logger import createLogger
from lib.json_util import get_dict_value, init_conf_files, make_init_folders, load_json_conf, save_json_conf


LOGGER_LEVEL_DEBUG: Final				= 10
LOGGER_NAME: Final						= 'hellven'

URL_HOST_HELLVEN: Final					= 'hellven.net'

DOM_PATH_AV_LIST: Final					= '#fboardlist > div.list-container'
DOM_PATH_SUB_INFO: Final				= 'body > div.wrapper > div.container.content > div:nth-child(1) > div.col-md-3.col-sm-12 > div.panel.panel-default'




DEF_HELLVEN_CONF_FILE: Final			= '../../conf/hellven.json'
DEF_CONF_HELLVEN: Final					= {
	const.JSON_DB: {
		const.JKEY_DB_HOST: 'localhost'
		, const.JKEY_DB_PORT: '3306'
		, const.JKEY_DB_NAME: 'MyDB'
		, const.JKEY_DB_ENCODING: const.DEF_DB_ENCODING
		, const.JKEY_USERNAME: 'username'
		, const.JKEY_PASSWORD: 'password'
	}
	, const.JKEY_HOST: URL_HOST_HELLVEN
	, const.JKEY_LIMIT_PAGE_COUNT: const.DEF_LIMIT_PAGE_COUNT
	, const.JKEY_MAX_DUPLICATED_COUNT: const.DEF_MAX_DUPLICATED_COUNT
	, const.JKEY_START_PAGE_NO: 1
}





class HellvenCrawler(BaseBoardCrawler):

	def __init__(self) -> None:
		""" 수집기 기본 생성자 """
		super(HellvenCrawler, self).__init__()

		self._duplicated_count = 0
		self._headers = dict()

		make_init_folders(('../../logs', '../../db', '../../conf'))
		self._logger: Logger = createLogger(log_path = '../../logs', log_filename = LOGGER_NAME, log_level = LOGGER_LEVEL_DEBUG)


	def getDetailInfo(self, info: dict) -> bool:
		""" hellven에서 수집한 기본 정보를 바탕으로 보다 상세한 정보를 추출합니다.

		Args:
			info (dict): hellven에서 수집한 기본 정보가 담겨있는 객체

		Returns:
			bool: 정보 획득 성공 여부. 필수 항목들을 모두 가져왔는가?
		"""
		url: str = f'https://{URL_HOST_HELLVEN}/bbs/board.php?bo_table=ydsmi&wr_id={info[const.CN_HELLVEN_BOARD_NO]}'
		if ( (url == None) or (url.strip() == '') ):
			self._logger.warning(f'URL info fail! : {info}')
			return False

		for _ in range(const.DEF_RETRY_COUNT):
			# response = requests.get(url, headers = self._headers)
			response = self._scraper.get(url, headers = self._headers)
			if (response.status_code == 200):
				html = response.text
				f = open('html/hellven-detail.html', "wt", encoding = "utf-8", newline = "\n")
				f.write(html)
				f.close()
				soup = BeautifulSoup(html, 'html.parser')
				if (soup == None):
					self._logger.warning(f'html.parser fail : {url=}')
					return False
				
				view_img = soup.find(class_ = "view-img")
				if (view_img == None):
					self._logger.warning(f'"view-img" div tag not found : {url=}')
					info[const.CN_COVER_IMAGE_URL] = None
				else:
					img_tag = view_img.find('img')
					if (img_tag is not None):
						img_url = img_tag.get("src")
						info[const.CN_COVER_IMAGE_URL] = img_url[img_url.find('/', 8):] if (img_url != None) else None

				a_tag = soup.find(class_ = "list-group-item break-word view_file_download at-tip")
				if (a_tag is None):
					self._logger.warning(f'script file info tag not found : {url=}')
					return False
				script_url = a_tag.get('href')
				info[const.CN_SCRIPT_FILE_URL] = script_url[script_url.find('/', 8):] if (script_url is not None) else None
				file_size = reg_compile(r'\(\S+\)').findall(a_tag.text.strip())
				if ( len(file_size) > 0):
					info[const.CN_FILE_SIZE] = file_size[0][1:-1] # 괄호 제거
				else:
					info[const.CN_FILE_SIZE] = None

				file_name = reg_compile(r'\S+').findall(a_tag.text.strip())
				if ( len(file_name) > 0):
					info[const.CN_SCRIPT_NAME] = file_name[1]
				else:
					info[const.CN_SCRIPT_NAME] = None

				tag_tag = soup.find(class_ = "view-tag font-12")
				info[const.CN_TAGS] = tag_tag.text.strip()

				content_tag = soup.find(class_ = 'view-content')
				if (content_tag is not None):
					info[const.CN_CONTENT] = content_tag.text.strip().replace('\r', '\n').replace('\n\n', '\n')
				else:
					info[const.CN_CONTENT] = None
				return True
			else:
				self._logger.warning(f'detail info request fail {_ + 1} {url=} : {response.status_code=}')
			sleep(const.DEF_RETRY_WAIT_TIME)

		return False



	def getMagnetAddr(self, magnet_tag: Tag) -> str:
		""" 주어진 주소로부터 마그넷 다운로드 정보를 받아와 반환합니다.

		Args:
			url (str): 마그넷 다운로드 정보를 받을 URL

		Returns:
			str: 마그넷 다운로드 정보. 찾지 못한 경우에는 None을 반환합니다.
		"""
		if (magnet_tag == None):
			self._logger.warning(f'not found btn-magnet')
			return None

		magnet_url = None
		onclick: str = magnet_tag.get('onclick')
		# print(onclick)
		pos1 = onclick.find("'")
		if (pos1 >= 0):
			pos1 += 1
			pos2 = onclick.find("'", pos1)
			if (pos2 >= 0):
				magnet_url = f'https://{URL_HOST_HELLVEN}{onclick[pos1:pos2]}'

		url = magnet_url
		if ( (url == None) or (url.strip() == '') ):
			self._logger.warning(f'not found magnet_url')
			return None

		for _ in range(const.DEF_RETRY_COUNT):
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
				self._logger.warning(f'magnet_url requests fail! {_ + 1} ; {response.status_code=}')
			sleep(const.DEF_RETRY_WAIT_TIME)
		self._logger.warning(f'retry fail!')
		return None


	def init(self) -> int:
		self.initConf(DEF_HELLVEN_CONF_FILE, DEF_CONF_HELLVEN)

		try:
			self._scraper = create_scraper(delay = 10, browser = 'chrome') # cloudflare bypass
			if (self._scraper == None):
				self._logger.error(f'cloudscraper creation error : {e}')
				return const.ERR_CLOUDSCRAPER_CREATION
			headers = self.loadHeader('hellven-header.txt')
			if (headers is None):
				return const.ERR_HEADER_LOADING
			else:
				self._scraper.headers = headers
		except Exception as e:
			self._logger.exception(e)
			return const.ERR_CLOUDSCRAPER_CREATION

		try:
			self._db = AvdbDataModel()
			self._db.setLogger(self._logger)
			self._db.connectDatabase(self._conf.get(const.JSON_DB))
			pass
		except Exception as e:
			self._logger.error(f'Database connection error : {e}')
			return const.ERR_DB_CONNECTION

		try:
			headers = self.loadHeader('hellven-header.txt')
			if (headers == None):
				self._logger.error(f'Header loading fail!')
				return const.ERR_HEADER_LOADING
			else:
				self._headers = headers
		except Exception as e:
			self._logger.error(f'Header loading error : {e}')
			return const.ERR_HEADER_LOADING2

		return 0


	def parseAvInfo(self, info_list: list, html: str) -> int:
		""" 주어진 HTML 내용을 파싱히여 AV 정보를 가져옵니다.

		Args:
			info_list (list): AV 정보가 저장될 list 객체
			html (str): 파싱할 HTML 내용

		Returns:
			int: 파싱 성공 여부. 필수 항목들을 모두 가져왔는가?
		"""
		soup = BeautifulSoup(html, 'html.parser')
		if (soup == None):
			self._logger.error(f'html.parser error')
			return const.ERR_BS4_PARSER_FAIL

		# 자막 정보 파싱
		av_list = soup.find_all(class_ = 'list-item')
		# av_list = soup.select_one(DOM_PATH_AV_LIST)
		if (av_list == None):
			self._logger.error(f"not found 'list-item' elements.")
			return const.ERR_BS4_ELM_NOT_FOUND

		for item_index, av_list_item in enumerate(av_list, start = 1):
			sleep(3)
			# 기본 정보 가져오기
			info = dict()
			a_tag = av_list_item.find('a')
			url = a_tag.get('href')
			board_no = reg_compile(r'&wr_id=\d+').findall(url)
			if (len(board_no) > 0):
				info[const.CN_HELLVEN_BOARD_NO] = board_no[0][7:]
			else:
				info[const.CN_HELLVEN_BOARD_NO] = None
			strong_tag = av_list_item.find('strong')
			title: str = strong_tag.text
			first_space = title.find('\n\t\t\t\t\t\t\t\t\t')
			if (first_space >= 0):
				title = title[first_space + 10:].rstrip().upper()
				first_space = title.find(' ')
				if (first_space >= 0):
					title = title[:first_space]
				info[const.CN_FILM_ID] = title
			else:
				info[const.CN_FILM_ID] = title.strip().upper()
			time_tag = av_list_item.find('time')
			date_info = time_tag.attrs.get('datetime')
			info[const.CN_BOARD_DATE] = date_info[:-6]
			info_details = av_list_item.find_all(class_ = 'list-details font-12 text-muted')
			if (len(info_details) >= 2):
				info[const.CN_TITLE] = info_details[0].text.strip()
				category = info_details[1].text.strip()
				info[const.CN_CATEGORY] = 'J' if (category == '일본') else 'W' if (category == '서양') else 'C' if (category == '중국') else 'A' if (category == 'A.I 번역') else 'E'

			self._logger.info(f'getDetailInfo : {info[const.CN_FILM_ID]} / {info[const.CN_TITLE]} / {info[const.CN_BOARD_DATE]}')
			if (self.getDetailInfo(info)):
				ret = self._db.insertHellvenScript(info)
				# ret = self.insert(connection, cursor, info)
				if (ret == const.ERR_DB_INTEGRITY):
					self._duplicated_count += 1
					if (self._duplicated_count > self._max_duplicated_count):
						return const.ERR_DB_INTEGRITY
				else:
					self._duplicated_count = 0
				info_list.append(info)
			else:
				self._logger.warning(f'Fetch fail of detail info! : {info}')

		self._logger.info(f'parsed info count = {len(info_list)}')
		return 0


	def run(self) -> int:
		""" 수집기 실행부

		Returns:
			int: 실행 결과 코드값
		"""
		ret = self.init()
		if (ret != 0):
			print(f'Internal Error (init): {ret=}')

		is_ended = False
		info_list = list()
		_limit_page_count = get_dict_value(self._conf, const.JKEY_LIMIT_PAGE_COUNT, const.DEF_LIMIT_PAGE_COUNT)
		self._max_duplicated_count = get_dict_value(self._conf, const.JKEY_MAX_DUPLICATED_COUNT, const.DEF_MAX_DUPLICATED_COUNT)
		start_page_no = get_dict_value(self._conf, const.JKEY_START_PAGE_NO, 1)
		self._logger.info(f'GATHERING started: {start_page_no=}, {self._max_duplicated_count=}, {_limit_page_count=}')
		# for page_no in range(407, 1, -1):
		for page_no in range(1, _limit_page_count):
			self._logger.info(f'try parsing {page_no=}')
			url = f'https://{URL_HOST_HELLVEN}/bbs/board.php?bo_table=ydsmi&page={page_no}'

			for _ in range(const.DEF_RETRY_COUNT):
				# response = requests.get(url, headers = self._headers)
				response = self._scraper.get(url)
				if (response.status_code == 200):
					html = response.text
					f = open('html/hellven-list.html', "wt", encoding = "utf-8", newline = "\n")
					f.write(html)
					f.close()
					# return
					# print(html)
					ret = self.parseAvInfo(info_list, html)
					if (ret == const.ERR_DB_INTEGRITY):
						is_ended = True # 연속으로 3개가 중복이라면, 종료함
					break
				else:
					self._logger.warning(f'detail info reqest fail {_ + 1} : {response.status_code=}')
				sleep(const.DEF_RETRY_WAIT_TIME)

			sleep(10)
			if (is_ended):
				break
		# for info in info_list:
		# 	insert(connection, cursor, info)
		self._logger.info(f'end: {len(info_list)} info parsed')

		return 0





def main() -> int:
	""" 실행 부 """
	hellven = HellvenCrawler()
	ret = hellven.run()

	return ret





if __name__ == '__main__':

	main()
