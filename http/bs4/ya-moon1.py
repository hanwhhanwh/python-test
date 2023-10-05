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

URL_HOST_AVGOSU: Final					= 'ya-moon.com'

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

DEF_AVGOSU_CONF_FILE: Final				= '../../conf/avgosu.json'







def getDetailInfo(info: dict) -> bool:
	""" AVGOSU에서 수집한 기본 정보를 바탕으로 보다 상세한 정보를 추출합니다.

	Args:
		info (dict): AVGOSU에서 수집한 기본 정보가 담겨있는 객체

	Returns:
		bool: 정보 획득 성공 여부. 필수 항목들을 모두 가져왔는가?
	"""
	url: str = info[CN_DETAIL_URL]
	if ( (url == None) or (url.strip() == '') ):
		_logger.warning(f'URL info fail! : {info}')
		return False

	for _ in range(DEF_RETRY_COUNT):
		response = requests.get(url, headers = DEFAULT_HEADERS)
		if (response.status_code == 200):
			html = response.text
			soup = BeautifulSoup(html, 'html.parser')
			if (soup == None):
				_logger.warning(f'html.parser fail : {url=}')
				return False
			
			view_img = soup.find('div', 'view-img')
			if (view_img == None):
				_logger.warning(f'"view-img" div tag not found : {url=}')
				return False
			
			img_tag = view_img.next_element
			# img_tag = next(view_img)
			info[CN_COVER_IMAGE_URL] = img_tag.get('src')
			img_tag = img_tag.next_element
			info[CN_THUMBNAIL_URL] = img_tag.get('src')

			magnet_tag = soup.find('a', 'btn btn-magnet')
			info[CN_MAGNET_ADDR] = getMagnetAddr(magnet_tag)
			return True
		else:
			_logger.warning(f'detail info request fail {_ + 1} {url=} : {response.status_code=}')
		sleep(DEF_RETRY_WAIT_TIME)

	return False



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


def parseScriptList(info_list: list, html: str) -> int:
	""" 주어진 HTML 내용을 파싱히여 AV 정보를 가져옵니다.

	Args:
		info_list (list): AV 정보가 저장될 list 객체
		html (str): 파싱할 HTML 내용

	Returns:
		int: 파싱 성공 여부. 필수 항목들을 모두 가져왔는가?
	"""
	soup = BeautifulSoup(html, 'html.parser')
	if (soup == None):
		_logger.error(f'h함ml.parser error')
		return ERR_BS4_PARSER_FAIL

	# 주요 목록 정보
	av_list = soup.select_one(DOM_PATH_AV_LIST)
	if (av_list == None):
		_logger.error(f'not found info list element.')
		return ERR_BS4_ELM_NOT_FOUND

	connection, cursor, error_code = connect_database(_conf.get(JSON_DB))
	if (error_code != 0):
		_logger.error(f'database connection fail : {error_code}')
		sys.exit(error_code)

	for item_index, av_list_item in enumerate(av_list.children, start = 1):
		# 기본 정보 가져오기
		info = dict()
		a_tag = av_list_item.find('a')
		info[CN_DETAIL_URL] = a_tag.get('href')
		title: str = a_tag.get('title')
		first_space = title.index(' ')
		info[CN_FILM_ID] = title[:first_space]
		info[CN_TITLE] = title[first_space + 1:]
		size_info_tag = av_list_item.find('span')
		info[CN_FILE_SIZE] = size_info_tag.text
		date_info_tag = size_info_tag.next_sibling
		date_info: str = date_info_tag.text
		if (date_info.find(':') < 0):
			date_info = f'{datetime.now().year}-{date_info}'
		else:
			today = datetime.now().strftime("%Y-%m-%d")
			date_info = f'{today} {date_info}'
		info[CN_DATE] = date_info

		_logger.info(f'getDetailInfo : {info[CN_FILM_ID]} / {info[CN_FILE_SIZE]} / {info[CN_DATE]}')
		if (getDetailInfo(info)):
			ret = insert(connection, cursor, info)
			if (ret == ERR_DB_INTEGRITY):
				return ERR_DB_INTEGRITY
			info_list.append(info)
		else:
			_logger.warning(f'Fetch fail of detail info! : {info}')

	_logger.info(f'parsed info count = {len(info_list)}')
	return 0




if __name__ == '__main__':

	make_init_folders(('../../logs', '../../db', '../../conf'))
	_logger = createLogger(log_path = '../../logs', log_filename = LOGGER_NAME, log_level = LOGGER_LEVEL_DEBUG)

	_conf, error_msg = load_json_conf(DEF_AVGOSU_CONF_FILE)
	if (_conf == None):
		_logger.warning(error_msg)
		_conf = DEF_CONF_AVGOSU
		save_json_conf(DEF_AVGOSU_CONF_FILE, _conf)
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
