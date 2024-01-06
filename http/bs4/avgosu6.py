# gather AVGOSU sample 6
# make hbesthee@naver.com
# date 2023-10-18

from bs4 import BeautifulSoup, PageElement, Tag
from datetime import datetime
from logging import getLogger, Logger
from mysql.connector.errors import IntegrityError
from os import path, makedirs, remove
from re import compile
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
LOGGER_NAME: Final						= 'avgosu'
URL_HOST_AVGOSU: Final					= 'avgosu5.com'

HEADER_USER_AGENT: Final				= "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

DOM_PATH_AV_LIST: Final					= '#fboardlist > div.list-container'
DOM_PATH_SUB_INFO: Final				= 'body > div.wrapper > div.container.content > div:nth-child(1) > div.col-md-3.col-sm-12 > div.panel.panel-default'


DEF_AVGOSU_CONF_FILE: Final				= '../../conf/avgosu.json'
DEF_CONF_AVGOSU: Final					= {
	const.JSON_DB: {
		const.JKEY_DB_HOST: 'localhost'
		, const.JKEY_DB_PORT: '3306'
		, const.JKEY_DB_NAME: 'MyDB'
		, const.JKEY_DB_ENCODING: const.DEF_DB_ENCODING
		, const.JKEY_USERNAME: 'username'
		, const.JKEY_PASSWORD: 'password'
	}
	, const.JKEY_HOST: URL_HOST_AVGOSU
	, const.JKEY_LIMIT_PAGE_COUNT: const.DEF_LIMIT_PAGE_COUNT
	, const.JKEY_MAX_DUPLICATED_COUNT: const.DEF_MAX_DUPLICATED_COUNT
	, const.JKEY_START_PAGE_NO: 1
}





class AVGosuCrawler(BaseBoardCrawler):

	def __init__(self) -> None:
		""" 수집기 기본 생성자 """
		super(AVGosuCrawler, self).__init__()

		self._duplicated_count = 0
		self._headers: dict = None
		self._host = URL_HOST_AVGOSU

		make_init_folders(('../../logs', '../../db', '../../conf'))
		self._logger: Logger = createLogger(log_path = '../../logs', log_filename = LOGGER_NAME, log_level = LOGGER_LEVEL_DEBUG)


	def getDefaultHeaders(self) -> dict:
		""" AVGOSU 요청을 위한 기본 HEADER 정보를 반환합니다.

		Returns:
			dict: 기본 헤더 정보
		"""
		headers = {
			'authority': f'{self._host}'
			, 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
			, 'accept-language': 'ko-KR,ko;q=0.9'
			, 'cache-control': 'no-cache'
			, 'content-type': 'application/x-www-form-urlencoded'
			, 'origin': f'https://{self._host}'
			, 'pragma': 'no-cache'
			, 'referer': f'https://{self._host}'
			, 'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"'
			, 'sec-ch-ua-mobile': '?0'
			, 'sec-ch-ua-platform': '"Windows"'
			, 'sec-fetch-dest': 'document'
			, 'sec-fetch-mode': 'navigate'
			, 'sec-fetch-site': 'same-origin'
			, 'sec-fetch-user': '?1'
			, 'upgrade-insecure-requests': '1'
			, 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
		}
		return headers


	def getDetailInfo(self, info: dict) -> bool:
		""" AVGOSU에서 수집한 기본 정보를 바탕으로 보다 상세한 정보를 추출합니다.

		Args:
			info (dict): AVGOSU에서 수집한 기본 정보가 담겨있는 객체

		Returns:
			bool: 정보 획득 성공 여부. 필수 항목들을 모두 가져왔는가?
		"""
		avgosu_board_no = info[const.CN_AVGOSU_BOARD_NO]
		url: str = f'https://{self._host}/torrent/etc/{avgosu_board_no}.html'
		if ( (url == None) or (url.strip() == '') ):
			self._logger.warning(f'URL info fail! : {info}')
			return False

		for _ in range(const.DEF_RETRY_COUNT):
			response = requests.get(url, headers = self._headers)
			if (response.status_code == 200):
				html = response.text
				soup = BeautifulSoup(html, 'html.parser')
				if (soup == None):
					self._logger.warning(f'html.parser fail ({avgosu_board_no}) : {url=}')
					return False
				
				view_img = soup.find('div', 'view-img')
				if (view_img == None):
					self._logger.warning(f'"view-img" div tag not found ({avgosu_board_no}) : {url=}')
					return False
				
				img_tag = view_img.next_element
				# img_tag = next(view_img)
				img_url = img_tag.get('src')
				cover_url: str = img_url[img_url.find('/', 8):] if (img_url != None) else None
				if (cover_url is not None):
					cover_url = cover_url.replace('/uploads/images', '')
				info[const.CN_COVER_IMAGE_URL] = cover_url
				img_tag = img_tag.next_element
				img_url = img_tag.get('src')
				thumb_url: str = img_url[img_url.find('/', 8):] if (img_url != None) else None
				if (thumb_url is not None):
					thumb_url = cover_url.replace('/uploads/images', '')
				info[const.CN_THUMBNAIL_URL] = thumb_url
				

				magnet_tag = soup.find('a', 'btn btn-magnet')
				magnet_addr = self.getMagnetAddr(magnet_tag)
				if ((len(magnet_addr) % 2) != 0):
					self._logger.warning(f'magnet_addr is wrong ({avgosu_board_no}) : {magnet_addr=}')
					info[const.CN_MAGNET_INFO] = None
				else:
					info[const.CN_MAGNET_INFO] = bytes.fromhex(magnet_addr[20:])

				torrent_tag = soup.find('div', 'view-torrent')
				if (torrent_tag.text.find('-HD.torrent') > 0):
					info[const.CN_RESOLUTION] = 'H'
				else:
					info[const.CN_RESOLUTION] = 'F'
				return True
			else:
				self._logger.warning(f'detail info request fail ({avgosu_board_no}) {_ + 1} : {response.status_code=}')
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
				magnet_url = f'https://{self._host}{onclick[pos1:pos2]}'

		url = magnet_url
		if ( (url == None) or (url.strip() == '') ):
			self._logger.warning(f'not found magnet_url')
			return None

		for _ in range(const.DEF_RETRY_COUNT):
			response = requests.get(url, headers = self._headers)
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
		self.initConf(DEF_AVGOSU_CONF_FILE, DEF_CONF_AVGOSU)

		self._host = get_dict_value(self._conf, const.JKEY_HOST, URL_HOST_AVGOSU)

		self._db = AvdbDataModel()
		self._db.setLogger(self._logger)
		self._db.connectDatabase(self._conf.get(const.JSON_DB))

		try:
			headers = self.loadHeader('avgosu-header.txt')
			if (headers == None):
				self._logger.error(f'Header loading fail!')
				self._headers = self.getDefaultHeaders()
				# return const.ERR_HEADER_LOADING
			else:
				self._headers = headers
		except Exception as e:
			self._logger.error(f'Header loading error : {e}')
			self._headers = self.getDefaultHeaders()
			# return const.ERR_HEADER_LOADING2

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

		# 목록 정보 파싱
		av_list = soup.select_one(DOM_PATH_AV_LIST)
		if (av_list == None):
			self._logger.error(f'not found info list element.')
			return const.ERR_BS4_ELM_NOT_FOUND

		for item_index, av_list_item in enumerate(av_list.children, start = 1):
			# 기본 정보 가져오기
			info = dict()
			a_tag = av_list_item.find('a')
			url = a_tag.get('href')
			board_no = compile(r"etc\/\d+\.htm").findall(url)
			if (len(board_no) > 0):
				avgosu_board_no = board_no[0][4:-4]
				info[const.CN_AVGOSU_BOARD_NO] = avgosu_board_no
			else:
				self._logger.warning(f'Fetch fail of board_no : {url=}')
				continue
			# info[const.CN_DETAIL_URL] = url[url.find('/', 8):url.find('?', 8)]
			title: str = a_tag.get('title')
			first_space = title.find(' ')
			if (first_space >= 0):
				info[const.CN_FILM_ID] = title[:first_space].upper()
			else:
				info[const.CN_FILM_ID] = title.upper()
			info[const.CN_TITLE] = title[first_space + 1:]
			list_details_tag = av_list_item.find(class_ = 'list-details text-muted ellipsis')
			size_info_tag = list_details_tag.find('span') if (list_details_tag) else None
			info[const.CN_FILE_SIZE] = size_info_tag.text if (size_info_tag) else None
			date_info_tag = size_info_tag.next_sibling if (size_info_tag) else None
			date_info: str = date_info_tag.text if (date_info_tag) else None
			if (date_info.find(':') < 0):
				date_info = f'{datetime.now().year}-{date_info}'
			else:
				today = datetime.now().strftime("%Y-%m-%d")
				date_info = f'{today} {date_info}'
			info[const.CN_AVGOSU_DATE] = date_info

			self._logger.info(f'getDetailInfo ({avgosu_board_no}) : {info[const.CN_FILM_ID]} / {info[const.CN_FILE_SIZE]} / {info[const.CN_AVGOSU_DATE]}')
			if (self.getDetailInfo(info)):
				ret = self._db.insertAvgosu(info)
				# ret = self.insert(connection, cursor, info)
				if (ret == const.ERR_DB_INTEGRITY):
					self._duplicated_count += 1
					if (self._duplicated_count > self._max_duplicated_count):
						return const.ERR_DB_INTEGRITY
				else:
					self._duplicated_count = 0
				info_list.append(info)
			else:
				self._logger.warning(f'Fetch fail of detail info! ({avgosu_board_no}) : {info}')

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
		for page_no in range(start_page_no, _limit_page_count + 1):
			self._logger.info(f'try parsing {page_no=}')
			url = f'https://{self._host}/torrent/etc.html?&page={page_no}'

			for _ in range(const.DEF_RETRY_COUNT):
				response = requests.get(url, headers = self._headers)
				if (response.status_code == 200):
					html = response.text
					# print(html)
					ret = self.parseAvInfo(info_list, html)
					if (ret == const.ERR_DB_INTEGRITY):
						is_ended = True # 연속으로 3개가 중복이라면, 종료함
					break
				else:
					self._logger.warning(f'detail info reqest fail {_ + 1} : {response.status_code=}')
				sleep(const.DEF_RETRY_WAIT_TIME)

			if (is_ended):
				break
		# for info in info_list:
		# 	insert(connection, cursor, info)
		self._logger.info(f'end: {len(info_list)} info parsed')

		return 0





def main() -> int:
	""" 실행 부 """
	avc = AVGosuCrawler()
	ret = avc.run()

	return ret





if __name__ == '__main__':

	main()
