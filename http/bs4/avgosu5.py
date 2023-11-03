# gather AVGOSU sample 5
# make hbesthee@naver.com
# date 2023-10-02

from bs4 import BeautifulSoup, PageElement, Tag
from datetime import datetime
from logging import getLogger, Logger
from mysql.connector.errors import IntegrityError
from os import path, makedirs, remove
from sqlalchemy import create_engine
from time import sleep
from typing import Final
from urllib.parse import urlparse
from urllib3 import request

import requests


import sys
sys.path.append( path.abspath('../..') )
from lib.file_logger import createLogger
from lib.json_util import get_dict_value, init_conf_files, make_init_folders, load_json_conf, save_json_conf


LOGGER_LEVEL_DEBUG: Final				= 10
LOGGER_NAME: Final						= 'avgosu'

URL_HOST_AVGOSU: Final					= 'avgosu1.com'
HEADER_USER_AGENT: Final				= "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

DOM_PATH_AV_LIST: Final					= '#fboardlist > div.list-container'
DOM_PATH_SUB_INFO: Final				= 'body > div.wrapper > div.container.content > div:nth-child(1) > div.col-md-3.col-sm-12 > div.panel.panel-default'

DEFAULT_HEADERS: Final					= {
	'authority': f'{URL_HOST_AVGOSU}'
	, 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
	, 'accept-language': 'ko-KR,ko;q=0.9'
	, 'cache-control': 'no-cache'
	, 'content-type': 'application/x-www-form-urlencoded'
	, 'origin': f'https://{URL_HOST_AVGOSU}'
	, 'pragma': 'no-cache'
	, 'referer': f'https://{URL_HOST_AVGOSU}'
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

ERR_BS4_PARSER_FAIL: Final				= -101 # 파서 생성 실패
ERR_BS4_ELM_NOT_FOUND: Final			= -102 # 해당 요소를 찾지 못함

ERR_DB_INTERNAL: Final					= -1001 # 내부 오류 발생 ; 상세 오류 내용은 로그 확인 필요
ERR_DB_INTEGRITY: Final					= -1002 # 중복된 데이터를 추가했을 경우 발생 ; 기존에 수집한 자료가 발견되었으므로, 프로그램 종료하기


CN_DETAIL_URL: Final					= 'detail_url'
CN_TITLE: Final							= 'title'
CN_FILM_ID: Final						= 'film_id'
CN_DATE: Final							= 'avgosu_date'
CN_FILE_SIZE: Final						= 'file_size'
CN_COVER_IMAGE_URL: Final				= 'cover_image_url'
CN_THUMBNAIL_URL: Final					= 'thumbnail_url'
CN_MAGNET_ADDR: Final					= 'magnet_addr'


JSON_DB: Final							= 'database'

JKEY_DB_HOST: Final						= 'db_host'
JKEY_DB_PORT: Final						= 'db_port'
JKEY_DB_NAME: Final						= 'db_name'
JKEY_DB_ENCODING: Final					= 'encoding'
JKEY_USERNAME: Final					= 'username'
JKEY_PASSWORD: Final					= 'password'
JKEY_LIMIT_PAGE_COUNT: Final			= 'limit_page_count'

DEF_LIMIT_PAGE_COUNT: Final				= 10
DEF_RETRY_COUNT: Final					= 3 # request를 다시 시도할 회수
DEF_RETRY_WAIT_TIME: Final				= 3 # request를 다시 시도하기 전 대기시간 (초)


DEF_AVGOSU_CONF_FILE: Final				= '../../conf/avgosu.json'
DEF_DB_ENCODING: Final					= 'utf-8'
DEF_CONF_AVGOSU: Final					= {
	JSON_DB: {
		JKEY_DB_HOST: 'localhost'
		, JKEY_DB_PORT: '3306'
		, JKEY_DB_NAME: 'MyDB'
		, JKEY_DB_ENCODING: DEF_DB_ENCODING
		, JKEY_USERNAME: 'username'
		, JKEY_PASSWORD: 'password'
	}
	, JKEY_LIMIT_PAGE_COUNT: DEF_LIMIT_PAGE_COUNT
}


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


def connect_database(conf: dict) -> tuple:
	""" 주어진 DB 연결정보를 바탕으로 데이터베이스 연결을 시도합니다.

	Args:
		conf (dict): 데이터베이스 연결에 필요한 상세 정보가 담겨있는 객체

	Returns:
		tuple: (connection, cursor, result_code) : result_code : 0 = 성공, -1 = 오류 발생 (세부 오류 내용은 로그 파일 확인하기)
	"""
	db_url = f"mysql+mysqlconnector://{conf.get(JKEY_USERNAME)}:{conf.get(JKEY_PASSWORD)}@{conf.get(JKEY_DB_HOST)}:{conf.get(JKEY_DB_PORT)}/{conf.get(JKEY_DB_NAME)}?charset=utf8mb4&collation=utf8mb4_general_ci"
	_logger.debug(f'connecting... : {conf.get(JKEY_DB_HOST)}:{conf.get(JKEY_DB_PORT)}/{conf.get(JKEY_DB_NAME)}')
	engine = create_engine(db_url, encoding = conf.get(JKEY_DB_ENCODING))
	if engine == None:
		# 데이터베이스 연결을 위한 엔진 객체 얻기 실패
		_logger.error(f'database engine fail!')
		return None, None, -1

	try:
		connection = engine.raw_connection()
	except Exception as e: # 데이터베이스 연결 실패
		_logger.error(f'database connection fail! >> {e}')
		return None, None, -1

	try:
		cursor = connection.cursor()  # get Database cursor
	except Exception as e: # Database cursor fail
		_logger.error(f'database cursor fail! >> {e}')
		return None, None, -1

	return connection, cursor, 0


def insert(connection, cursor, info: dict) -> int:
	""" 수집한 정보를 등록합니다.

	Args:
		connection: 데이터베이스 연결 객체
		cursor: 커서 객체
		info (dict): AVGOSU에서 수집한 정보

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
		cursor.execute(query_insert, (info.get(CN_DETAIL_URL), info.get(CN_TITLE), info.get(CN_FILM_ID), info.get(CN_DATE), info.get(CN_FILE_SIZE)
						, info.get(CN_COVER_IMAGE_URL), info.get(CN_THUMBNAIL_URL), info.get(CN_MAGNET_ADDR)))
		avgosu_no = cursor.lastrowid
		if avgosu_no == 0 or avgosu_no == None:
			_logger.error(f'insert execution fail : avgosu info')
		connection.commit()
	except IntegrityError as e:
		_logger.info(f'duplicated info : {info.get(CN_FILM_ID)} / {info.get(CN_FILE_SIZE)} / {info.get(CN_DATE)}')
		return ERR_DB_INTEGRITY
	except Exception as e:
		_logger.error(f'insert execution fail : avgosu info2 >> {e}')
		return ERR_DB_INTERNAL

	return avgosu_no


def parseAvInfo(info_list: list, html: str) -> int:
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
	_limit_page_count = get_dict_value(_conf, JKEY_LIMIT_PAGE_COUNT, DEF_LIMIT_PAGE_COUNT)
	for page_no in range(_limit_page_count):
		page_no += 1
		_logger.info(f'try parsing {page_no=}')
		url = f'https://{URL_HOST_AVGOSU}/torrent/etc.html?&page={page_no}'

		for _ in range(DEF_RETRY_COUNT):
			response = requests.get(url, headers = DEFAULT_HEADERS)
			if (response.status_code == 200):
				html = response.text
				# print(html)
				ret = parseAvInfo(info_list, html)
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
