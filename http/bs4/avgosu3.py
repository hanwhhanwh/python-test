# gather AVGOSU sample 3
# make hbesthee@naver.com
# date 2023-10-01

from datetime import datetime
from bs4 import BeautifulSoup
from logging import getLogger, Logger
from os import path, makedirs, remove
from urllib.parse import urlparse
from urllib3 import request
from typing import Final

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


CN_DETAIL_URL: Final					= 'detail_info_url'
CN_TITLE: Final							= 'title'
CN_FILM_ID: Final						= 'film_id'
CN_DATE: Final							= 'avgosu_date'
CN_FILE_SIZE: Final						= 'file_size'
CN_COVER_IMAGE_URL: Final				= 'cover_image_url'
CN_THUMBNAIL_URL: Final					= 'thumbnail_url'
CN_MAGNET_ADDR: Final					= 'magnet_addr'


JKEY_LIMIT_PAGE_COUNT: Final			= 'limit_page_count'

DEF_LIMIT_PAGE_COUNT: Final				= 10


CONF_DEF_AVGOSU: Final					= {
	JKEY_LIMIT_PAGE_COUNT: DEF_LIMIT_PAGE_COUNT
}


def getDetailInfo(info: dict):
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
		
		img_tag = next(view_img.children)
		info[CN_COVER_IMAGE_URL] = img_tag.get('src')
		# img_tag = next(view_img.children)
		img_tag = img_tag.next_element
		info[CN_THUMBNAIL_URL] = img_tag.get('src')

	else:
		_logger.warning(f'URL get error {url=} : {response.status_code=}')
		return False

	return True


def parseAvInfo(info_list: list, html: str) -> bool:
	""" 주어진 HTML 내용을 파싱히여 AV 정보를 가져옵니다.

	Args:
		info_list (list): AV 정보가 저장될 list 객체
		html (str): 파싱할 HTML 내용

	Returns:
		bool: 파싱 성공 여부. 필수 항목들을 모두 가져왔는가?
	"""
	soup = BeautifulSoup(html, 'html.parser')
	if (soup == None):
		return False
	result = True

	# 주요 목록 정보
	av_list = soup.select_one(DOM_PATH_AV_LIST)
	if (av_list == None):
		return False

	for av_list_item in av_list.children:
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
		if (date_info.find(':')):
			today = datetime.now().strftime("%Y-%m-%d")
			date_info = f'{today} {date_info}'
		else:
			date_info = f'{datetime.year}-{date_info}'
		info[CN_DATE] = date_info

		if (getDetailInfo(info)):
			info_list.append(info)
		else:
			_logger.warning(f'Fetch fail of detail info! : {info}')

	_logger.info(f'parsed info count = {len(info_list)}')
	return True




if __name__ == '__main__':

	make_init_folders(('../../logs', '../../db', '../../conf'))
	_logger = createLogger(log_path = '../../logs', log_filename = LOGGER_NAME, log_level = LOGGER_LEVEL_DEBUG)

	# get magnet button info 
	url = 'https://avgosu1.com/torrent/etc/1184599.html'
	magnet_url = None
	response = requests.get(url, headers = DEFAULT_HEADERS)
	if (response.status_code == 200):
		html = response.text
		soup = BeautifulSoup(html, 'html.parser')
		if (soup != None):
			magnet_tag = soup.find('a', 'btn btn-magnet')
			onclick: str = magnet_tag.get('onclick')
			print(onclick)
			pos1 = onclick.find("'")
			if (pos1 >= 0):
				pos1 += 1
				pos2 = onclick.find("'", pos1)
				if (pos2 >= 0):
					magnet_url = f'https://{URL_HOST_AVGOSU}{onclick[pos1:pos2]}'
					print(f'{magnet_url=}')


	# parsing magnet address
	if (magnet_url != None):
		# url = 'https://avgosu1.com/torrent/magnet/772183'
		url = magnet_url
		response = requests.get(url, headers = DEFAULT_HEADERS)
		if (response.status_code == 200):
			html = response.text
			print(html)
			pos1 = html.find('magnet:?')
			if (pos1 >= 0):
				pos2 = html.find('"', pos1)
				if (pos2 >= 0):
					magnet_addr = html[pos1:pos2]
					print(magnet_addr)


	info_list = list()
	_limit_page_count = 1 # MAX = 165
	for page_no in range(_limit_page_count):
		page_no += 1
		_logger.info(f'try parsing {page_no=}')
		url = f'https://{URL_HOST_AVGOSU}/torrent/etc.html?&page={page_no}'
		response = requests.get(url, headers = DEFAULT_HEADERS)

		info_list = list()
		if (response.status_code == 200):
			html = response.text
			# print(html)
			parseAvInfo(info_list, html)
