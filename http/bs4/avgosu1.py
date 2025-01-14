# gather AVGOSU sample 1
# make hbesthee@naver.com
# date 2023-10-01

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


CN_AV_DETAIL_URL: Final					= 'detail_info_url'
CN_AV_TITLE: Final						= 'title'



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

	# 번호판 주요 정보
	av_list = soup.select_one(DOM_PATH_AV_LIST)
	if (av_list == None):
		return False

	av_list_item = av_list.find('div', "list-row")
	while (av_list_item != None):
		info = dict()
		a_tag = av_list_item.find('a')
		info[CN_AV_DETAIL_URL] = a_tag.get('href')
		info[CN_AV_TITLE] = a_tag.get('title')
		info_list.append(info)
		av_list_item = av_list_item.find_next('div', "list-row")

	print(f'{len(info_list)=}')
	# print(info_list)
	return True

	av_list_item = av_list.select_one('a')
	if (av_list_item != None):
		info[CN_AV_DETAIL_URL] = av_list_item.get('href')
		info[CN_AV_TITLE] = av_list_item.get('title')
	else:
		result = False

	return result




if __name__ == '__main__':

	_logger = createLogger(log_path = '../../logs', log_filename = LOGGER_NAME, log_level = LOGGER_LEVEL_DEBUG)


	_page_no = 1
	url = f'https://{URL_HOST_AVGOSU}/torrent/etc.html?&page={_page_no}'


	# headers = {"User-Agent": HEADER_USER_AGENT}
	# response = requests.get(url, headers = headers)
	response = requests.get(url, headers = DEFAULT_HEADERS)

	info_list = list()
	if (response.status_code == 200):
		html = response.text
		# print(html)
		parseAvInfo(info_list, html)

