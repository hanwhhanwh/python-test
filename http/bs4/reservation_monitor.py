# -*- coding: utf-8 -*-
# 객실 예약정보 모니터링 클래스
# made : hbesthee@naver.com
# date : 2025-06-23

# Original Packages
from copy import deepcopy
from datetime import datetime, timedelta
from locale import LC_TIME, setlocale
from random import uniform
from time import sleep, time
from typing import List, Dict, Final, Tuple, Optional

import re



# Third-party Packages
from bs4 import BeautifulSoup
# from PyKakao import Message

import requests



# User's Package 들을 포함시키기 위한 sys.path에 프로젝트 폴더 추가하기
from os import getcwd
from sys import path as sys_path
project_folder = getcwd()
# print(f'{project_folder=}')
if (not project_folder in sys_path):
	sys_path.append(str(project_folder))


# User's Package
from lib.file_logger import createLogger
from lib.json_util import load_json_conf
from lib.kakao_message import KakaoMessage, KakaoMessageDef



class ReservationMonitorKey:
	"""객실 예약 모니터링 관련 각종 키 상수 문자열 정의 클래스"""
	LOG_LEVEL: Final							= 'log_level'
	FILTER_WEEKDAY: Final						= 'filter_weekday'
	SURELY_CHECK_DAY: Final						= 'surely_check_day'
	RESERVATION_DAY: Final[str]					= "reservation_day"
	EXCLUDE_ROOM: Final							= 'exclude_room'
	TARGET_LIST: Final							= 'target_list'
	TARGET: Final								= 'target'
	NAME: Final[str]							= 'name'
	URL: Final[str]								= 'url'
	IS_ACTIVE: Final[str]						= 'is_active'
	MONITOR_NEXT_MONTH: Final					= 'monitor_next_month'
	MONITORING_CYCLE: Final						= 'monitoring_cycle'
	APP_ID: Final								= 'app_id'
	APP_NAME: Final								= 'app_name'
	REST_API_KEY: Final							= 'rest_api_key'
	REFRESH_TOKEN: Final						= 'refresh_token'
	REFRESH_TOKEN_EXPIRES_AT: Final				= 'refresh_token_expires_at'
	TELEGRAM_BOT_TOKEN: Final					= 'telegram_bot_token'
	TELEGRAM_CHAT_ID: Final						= 'telegram_chat_id'
	DND_START_HOUR: Final						= 'DND_start_hour'
	DND_DURATION_HOURS: Final					= 'DND_duration_hours'
	USER_AGENT: Final							= 'User-Agent'

	URL_NO: Final[str]							= 'url_no'
	DATE: Final[str]							= 'date'
	DAY: Final[str]								= 'day'
	WEEKDAY: Final[str]							= 'weekday'
	AVAILABLE_ROOMS: Final[str]					= 'available_rooms'



class ReservationMonitorDef:
	"""객실 예약 모니터링 관련 각종 기본값 상수 정의 클래스"""
	LOG_LEVEL: Final							= 20
	FILTER_WEEKDAY: Final						= [0, 1, 2, 3, 4, 5, 6]
	SURELY_CHECK_DAY: Final						= []
	RESERVATION_DAY: Final[Dict]				= {}
	EXCLUDE_ROOM: Final							= ["^우", "^캠핑", "^글램"]
	TARGET_LIST: Final								= []
	MONITOR_NEXT_MONTH: Final					= 0
	MONITORING_CYCLE: Final						= 150
	APP_ID: Final								= ''
	APP_NAME: Final								= ''
	REST_API_KEY: Final							= ''
	REFRESH_TOKEN: Final						= ''
	TELEGRAM_BOT_TOKEN: Final					= ''
	TELEGRAM_CHAT_ID: Final						= 0
	DND_START_HOUR: Final						= 21
	DND_DURATION_HOURS: Final					= 11
	USER_AGENT: Final							= "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"



class ReservationMonitor:
	"""
	객실 예약정보 모니터링 클래스
	"""

	def __init__(self, config_path: str='conf/reservation_monitor.json'):
		"""
		ReservationMonitor 초기화

		reservation_monitor.json sample

			{
				"log_level":20
				, "filter_weekday":[4,5]
				, "surely_check_day":[]
				, "reservation_day":{}
				, "monitor_next_month":1
				, "monitoring_cycle":600
				, "DND_start_hour":21
				, "DND_duration_hours":11
				, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
				, "target_list":[
					{"name":"target1","url":"https://target1.url/cal/%Y/%m","is_active":true},
					{"name":"target2","url":"https://target2.url/cal/%Y/%m","is_active":true},
				]
				, "telegram_bot_token":6198598:eVK8a62hbf_c
				, "telegram_chat_id":-198598
				, "app_id":"1234"
				, "app_name":"my_app-name"
				, "rest_api_key":"my_app-rest_api_key"
				, "token_key":"my_app-token_key"
				, "refresh_token_expires_at":1756198598
			}

		Args:
			config_path (str): 설정 파일 경로
		"""
		self.config_path = config_path
		self.config = None

		self.log_level				= ReservationMonitorDef.LOG_LEVEL
		self.filter_weekday			= ReservationMonitorDef.FILTER_WEEKDAY
		self.surely_check_day		= ReservationMonitorDef.SURELY_CHECK_DAY
		self.reservation_day		= ReservationMonitorDef.RESERVATION_DAY
		self.exclude_rooms			= ReservationMonitorDef.EXCLUDE_ROOM
		self.is_monitor_next_month	= ReservationMonitorDef.MONITOR_NEXT_MONTH == 1
		self.minitoring_cycle		= ReservationMonitorDef.MONITORING_CYCLE
		self.DND_start_hour			= ReservationMonitorDef.DND_START_HOUR
		self.DND_duration_hours		= ReservationMonitorDef.DND_DURATION_HOURS
		self.user_agent				= ReservationMonitorDef.USER_AGENT
		self.target_list			= ReservationMonitorDef.TARGET_LIST
		self.telegram_bot_token		= ReservationMonitorDef.TELEGRAM_BOT_TOKEN
		self.telegram_chat_id		= ReservationMonitorDef.TELEGRAM_CHAT_ID
		self.app_id					= ReservationMonitorDef.APP_ID
		self.app_name				= ReservationMonitorDef.APP_NAME
		self.rest_api_key			= ReservationMonitorDef.REST_API_KEY
		self.refresh_token			= ReservationMonitorDef.REFRESH_TOKEN
		self.logger					= createLogger(
				log_filename='reservation_monitor'
				, log_level=self.log_level
				, log_console=True
				, log_format='%(asctime)s %(levelname)s %(lineno)d] %(message)s'
			)

		setlocale(LC_TIME, 'ko_KR.UTF-8')


	def _extract_available_rooms(self, cell) -> List[str]:
		"""
		셀에서 예약 가능한 객실 정보 추출

		Args:
			cell: BeautifulSoup 날짜 셀 객체

		Returns:
			List[str]: 예약 가능한 객실 리스트
		"""
		available_rooms = []
		room_types = cell.find('ul', class_='room-type')

		if room_types:
			room_items = room_types.find_all('li')

			compiled_exclude_rooms = [re.compile(p) for p in self.exclude_rooms]

			for room in room_items:
				# 예약 가능한 객실 찾기 (resY 클래스)
				if room.find('span', class_='resY'):
					room_link = room.find('a')
					if room_link:
						room_text = room_link.get_text().strip()
						if any(p.match(room_text) for p in compiled_exclude_rooms):
							continue
						# 대괄호 안의 숫자 추출 (가능한 객실 수)
						bracket_match = re.search(r'\[(\d+)\]', room.get_text())
						available_count = bracket_match.group(1) if bracket_match else "N/A"
						available_rooms.append(f"{room_text} [{available_count}개]")

		return available_rooms


	def _extract_year_month(self, calendar_table) -> Tuple[int, int]:
		"""
		캘린더 테이블에서 년도와 월 정보 추출

		Args:
			calendar_table: BeautifulSoup 캘린더 테이블 객체

		Returns:
			Tuple[int, int]: (년도, 월)
		"""
		year_month_link = calendar_table.find('a', href=re.compile(r'reservRoom$'))
		if year_month_link:
			year_month_text = year_month_link.get_text()
			# "2025년 6월" 형태에서 년도와 월 추출
			year_match = re.search(r'(\d{4})년', year_month_text)
			month_match = re.search(r'(\d{1,2})월', year_month_text)

			if year_match and month_match:
				return int(year_match.group(1)), int(month_match.group(1))

		# 현재 날짜 기준으로 설정
		now = datetime.now()
		return now.year, now.month


	def _init_kakao_msg(self) -> bool:
		"""
		Kakao 메시지 보내기 위한 초기화

		Returns:
			bool: 초기화 성공 여부
		"""
		# 메시지 API 인스턴스 생성
		self.MSG = KakaoMessage(service_key=self.rest_api_key)
		self.MSG.refresh_token = self.refresh_token
		self.MSG.refresh_token_expires_at = self.refresh_token_expires_at


	def _load_config(self) -> bool:
		"""
		설정 파일 로드

		Returns:
			bool: 로드 성공 여부
		"""
		try:
			self.config, err_msg = load_json_conf(self.config_path)
			if err_msg != '':
				self.logger.error(f'conf load fail!: {err_msg}')
				return False

			self.log_level				= self.config.get(ReservationMonitorKey.LOG_LEVEL,			ReservationMonitorDef.LOG_LEVEL)
			self.filter_weekday			= self.config.get(ReservationMonitorKey.FILTER_WEEKDAY,		ReservationMonitorDef.FILTER_WEEKDAY)
			self.reservation_day		= self.config.get(ReservationMonitorKey.RESERVATION_DAY,	ReservationMonitorDef.RESERVATION_DAY)
			self.surely_check_day		= self.config.get(ReservationMonitorKey.SURELY_CHECK_DAY,	ReservationMonitorDef.SURELY_CHECK_DAY)
			self.exclude_rooms			= self.config.get(ReservationMonitorKey.EXCLUDE_ROOM,		ReservationMonitorDef.EXCLUDE_ROOM)
			self.is_monitor_next_month	= self.config.get(ReservationMonitorKey.MONITOR_NEXT_MONTH,	ReservationMonitorDef.MONITOR_NEXT_MONTH) == 1
			self.minitoring_cycle		= self.config.get(ReservationMonitorKey.MONITORING_CYCLE,	ReservationMonitorDef.MONITORING_CYCLE)
			self.DND_start_hour			= self.config.get(ReservationMonitorKey.DND_START_HOUR,		ReservationMonitorDef.DND_START_HOUR)
			self.DND_duration_hours		= self.config.get(ReservationMonitorKey.DND_DURATION_HOURS,	ReservationMonitorDef.DND_DURATION_HOURS)
			self.user_agent				= self.config.get(ReservationMonitorKey.USER_AGENT,			ReservationMonitorDef.USER_AGENT)
			self.target_list			= self.config.get(ReservationMonitorKey.TARGET_LIST,		ReservationMonitorDef.TARGET_LIST)
			self.telegram_bot_token		= self.config.get(ReservationMonitorKey.TELEGRAM_BOT_TOKEN,	ReservationMonitorDef.TELEGRAM_BOT_TOKEN)
			self.telegram_chat_id		= self.config.get(ReservationMonitorKey.TELEGRAM_CHAT_ID,	ReservationMonitorDef.TELEGRAM_CHAT_ID)
			self.app_id					= self.config.get(ReservationMonitorKey.APP_ID,				ReservationMonitorDef.APP_ID)
			self.app_name				= self.config.get(ReservationMonitorKey.APP_NAME,			ReservationMonitorDef.APP_NAME)
			self.rest_api_key			= self.config.get(ReservationMonitorKey.REST_API_KEY,		ReservationMonitorDef.REST_API_KEY)
			self.refresh_token			= self.config.get(ReservationMonitorKey.REFRESH_TOKEN,		ReservationMonitorDef.REFRESH_TOKEN)
			self.refresh_token_expires_at = self.config.get(ReservationMonitorKey.REFRESH_TOKEN_EXPIRES_AT, 0)

			self.logger.setLevel(self.log_level)
			return True
		except Exception as e:
			self.logger.error(f'Config load error: {e}')
			return False


	def _process_date_cell(self, cell, year: int, month: int) -> Optional[Dict]:
		"""
		날짜 셀을 처리하여 예약 가능 정보 추출

		Args:
			cell: BeautifulSoup 날짜 셀 객체
			year (int): 년도
			month (int): 월

		Returns:
			Optional[Dict]: 날짜 정보 또는 None
		"""
		try:
			day = int(cell.get('day'))
			date_obj = datetime(year, month, day)
			weekday = date_obj.weekday()  # 0=월요일, 6=일요일

			is_surely_day = date_obj.strftime('%Y-%m-%d') in self.surely_check_day
			# 요일 필터링 처리
			if ((not is_surely_day) and (weekday not in self.filter_weekday)):
				return None

			weekday_name = date_obj.strftime('%a').encode('utf-8', 'surrogateescape').decode('utf-8', 'surrogateescape')

			# 휴원일 확인
			if (cell.find('span', string='휴원일')):
				return None

			# 객실 정보 확인
			available_rooms = self._extract_available_rooms(cell)

			if (available_rooms):
				return {
					ReservationMonitorKey.DATE: date_obj.strftime('%Y-%m-%d'),
					ReservationMonitorKey.WEEKDAY: weekday_name,
					ReservationMonitorKey.DAY: day,
					ReservationMonitorKey.AVAILABLE_ROOMS: available_rooms
				}

		except ValueError:
			# 잘못된 날짜는 건너뛰기
			pass

		return None


	def _send_kakao_message_to_me(self, reservation_info: dict) -> None:
		"""
		나에게 카카오 메시지 보내기

		Args:
			reservation_info (dict): 예약 가능한 날짜 정보 목록
		"""
		if (len(reservation_info) == 0):
			return

		message_type = "text" # 메시지 유형 - 텍스트
		for url, reservation_list in reservation_info.items():
			message = ''
			for date_info in reservation_list:
				message += (f"\n📅 {date_info.get(ReservationMonitorKey.DATE)} ({date_info.get(ReservationMonitorKey.WEEKDAY)})")
				avilable_rooms = date_info.get(ReservationMonitorKey.AVAILABLE_ROOMS, {})
				for room in avilable_rooms:
					message += (f"\n   • {room}")

			if (message == ''):
				continue

			text = message
			link = {
				"web_url": url,
				"mobile_web_url": url,
			}
			button_title = "바로 확인" # 버튼 타이틀

			self.MSG.send_message_to_me(
				message_type=message_type, 
				text=text,
				link=link,
				button_title=button_title,
			)


	def _send_telegram_chat_group(self, reservation_info: dict) -> None:
		"""
		이미 예약된 날짜의 방 정보를 텔레그림 그룹으로 메시지를 보냅니다.

		Args:
			reservation_info (dict): 예약 가능한 날짜 정보 목록

		Returns:
			bool: 예약된 날짜의 동일한 방 정보가 삭제(필터링) 여부
		"""
		if (len(reservation_info) == 0):
			return

		for url, reservation_list in reservation_info.items():
			message = ''
			for date_info in reservation_list:
				reserveAgreement_url = url
				target = date_info.get(ReservationMonitorKey.TARGET)
				if isinstance(url, str):
					pos = url.find('reservRoom/')
					if (pos > 1):
						reserveAgreement_url = f"{url[:pos]}reservRoom/reserveAgreement/{date_info.get(ReservationMonitorKey.DATE).replace('-', '')}/I"
				message += (f"{target.get(ReservationMonitorKey.NAME)}: <a href='{reserveAgreement_url}'>📅 {date_info.get(ReservationMonitorKey.DATE)} ({date_info.get(ReservationMonitorKey.WEEKDAY)})</a>\n")
				avilable_rooms = date_info.get(ReservationMonitorKey.AVAILABLE_ROOMS, {})
				for room in avilable_rooms:
					message += (f"   • {room}\n")

			if (message == ''):
				continue

			headers = {
				ReservationMonitorKey.USER_AGENT: self.user_agent
			}
			telegram_api = f'https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage'
			payload = {
				'chat_id': self.telegram_chat_id,
				'text': message,
				'parse_mode': 'HTML',
				'disable_web_page_preview': True,  # 링크 미리보기 비활성화
			}
			response = requests.post(telegram_api, data=payload, headers=headers)
			response.encoding = 'utf-8'
			self.logger.debug(f"telegram: {response=}")


	def check_resevation_day(self, room_results: dict) -> bool:
		"""
		이미 예약된 날짜의 방 정보를 삭제(필터링) 합니다.

		Args:
			room_results (dict): 예약가능한 방에 대한 정보 Dict

		Returns:
			bool: 예약된 날짜의 동일한 방 정보가 삭제(필터링) 여부
		"""
		if ( (self.reservation_day == {}) or (room_results == {}) ):
			return False

		is_filtered = False

		del_urls = []
		for url, room_list in room_results.items():
			for room_index in range(len(room_list) - 1, -1, -1):
				room_info = room_list[room_index]
				reserved_date = room_info.get(ReservationMonitorKey.DATE)
				reserved_info = self.reservation_day.get(reserved_date)
				if (reserved_info is None):
					continue # 예약 가능한 객실의 날짜에 이미 예약된 정보가 없음

				# target = room_info.get(ReservationMonitorKey.TARGET)
				exclude_rooms = reserved_info.get(ReservationMonitorKey.EXCLUDE_ROOM, [])
				if (exclude_rooms == []):
					# 이미 예약된 방이 있어서 더 이상 모든 형태의 방에 대한 정보를 알라지 않음 => 방 정보 삭제해야 함
					is_filtered = True
					self.logger.debug(f"삭제할 방정보: {room_info}")
					del room_list[room_index]
					continue
				else:
					compiled_exclude_rooms = [re.compile(p) for p in exclude_rooms]
					#TODO: 미리 컴파일해 놓는 것이 필요할 수 있으나, 매번 새로 json 설정을 읽는 것도 고려해야 함
					#컴파일을 매번 처리하지 않도록 하려면, json 설정 정보가 변경되었는지 검사하는 부분을 추가해야 함

					room_texts = room_info.get(ReservationMonitorKey.AVAILABLE_ROOMS, [])
					room_texts_org = room_texts.copy() # 삭제를 대비하여 원본 복사해 두기
					for text_index in range(len(room_texts) - 1, -1, -1):
						room_text = room_texts[text_index]
						if any(p.match(room_text) for p in compiled_exclude_rooms):
							del room_texts[text_index]
							continue
					if (len(room_texts) == 0):
						is_filtered = True
						room_info[ReservationMonitorKey.AVAILABLE_ROOMS] = room_texts_org
						self.logger.debug(f"삭제할 방정보: {room_info}")
						del room_list[room_index]

			if (len(room_list) == 0):
				self.logger.debug(f"삭제할 주소 정보: {url}")
				del_urls.append(url)

		for url in del_urls:
			del room_results[url]

		return is_filtered


	def display_results(self, reservation_info: dict) -> None:
		"""
		결과를 보기 좋게 출력합니다.

		Args:
			reservation_info (dict): 예약 가능한 날짜 정보 목록
		"""
		if (len(reservation_info) == 0):
			self.logger.info("예약 가능한 날짜가 없습니다.")
			return

		for url, reservation_list in reservation_info.items():
			if (len(reservation_list) < 1):
				continue
			date_info = reservation_list[0]
			target = date_info.get(ReservationMonitorKey.TARGET)
			reservation_list_str = f"\n{'=' * 22}\n  {target.get(ReservationMonitorKey.NAME, 'name fail')} {url[-7:]}\n{'=' * 22}"

			for date_info in reservation_list:
				reservation_list_str += f"\n📅 {date_info.get(ReservationMonitorKey.DATE)} ({date_info.get(ReservationMonitorKey.WEEKDAY)})"
				available_rooms = date_info.get(ReservationMonitorKey.AVAILABLE_ROOMS, {})
				for room in available_rooms:
					reservation_list_str += f"\n   • {room}"
				self.logger.info(reservation_list_str)


	def get_reservation_data(self, url: str) -> Optional[str]:
		"""
		객실 예약 웹사이트에서 HTML 데이터를 가져옵니다.

		Args:
			url (str): 요청할 URL

		Returns:
			Optional[str]: HTML 내용 또는 None
		"""
		try:
			headers = {
				ReservationMonitorKey.USER_AGENT: self.user_agent
			}
			response = requests.get(url, headers=headers)
			response.encoding = 'utf-8'
			response.raise_for_status()
			return response.text
		except Exception as e:
			self.logger.warning(f"웹사이트 접근 오류: {e}")
			return None


	def monitor_all_target(self) -> Dict[str, List[Dict]]:
		"""
		모든 대상 URL에 대한 모니터링 수행

		Returns:
			Dict[str, List[Dict]]: URL별 예약 가능한 날짜 정보
		"""
		results = {}
		year = datetime.now().year
		month = datetime.now().month
		current_month = datetime(year, month, 1)
		next_month = datetime(year, month + 1, 1) if (month != 12) else datetime(year + 1, month, 1)

		target_list_len = len(self.target_list)
		for target_index, target in enumerate(self.target_list):
			if (not target.get(ReservationMonitorKey.IS_ACTIVE, False)):
				continue

			self.logger.info(f"{target.get(ReservationMonitorKey.NAME, '')} 모니터링 중... ({target_index + 1}/{target_list_len})")

			self.monitor_target(results, target, current_month)

			if ( (self.is_monitor_next_month) and (datetime.now().day >= 14) ):
				self.monitor_target(results, target, next_month)

		if ( (self.reservation_day.keys() != []) and (results != {}) ):
			self.logger.debug(f"이미 예약된 날짜 확인중...")
			try:
				is_filtered = self.check_resevation_day(results)
				if (is_filtered):
					self.logger.debug(f"이미 예약된 날짜에 대한 예약 가능한 방 정보가 삭제되었습니다.")
			except Exception as e:
				self.logger.warning(f"check_resevation_day() error: {e}", exc_info=True)

		return results


	def monitor_target(self, results: dict, target: dict, monitor_month: datetime) -> int:
		"""
		단일 URL에 대한 모니터링 수행

		Args:
			results (dict): 예약 가능한 객실 정보를 담을 dict 객체
			target (dict): 감시 대상에 대한 세부 정보 객체
			monitor_month (datetime): 감시할 월정보

		Returns:
			int: 예약 가능한 날짜 수
		"""
		target_url = target.get(ReservationMonitorKey.URL)
		url = monitor_month.strftime(target_url)
		# 웹사이트에서 데이터 가져오기
		html_content = self.get_reservation_data(url)

		if (html_content is None):
			self.logger.warning(f"'{url}'에서 데이터를 가져올 수 없습니다.")
			return []

		# HTML 파싱 및 분석
		reservation_list = self.parse_room_availability(html_content, target)
		if (reservation_list != []):
			results[url] = reservation_list # url로 하는 것이 맞나?
		return len(reservation_list)


	def parse_room_availability(self, html_content: str, target: dict) -> List[Dict]:
		"""
		HTML 내용을 파싱하여 객실 예약 정보를 분석합니다.

		Args:
			html_content (str): 파싱할 HTML 내용
			target (dict): 감시 대상에 대한 세부 정보 객체

		Returns:
			List[Dict]: 예약 가능한 날짜 정보 리스트
		"""
		soup = BeautifulSoup(html_content, 'html.parser')

		# 캘린더 테이블 찾기
		calendar_table = soup.find('table', class_='calendar')
		if not calendar_table:
			self.logger.warning(f"캘린더 테이블을 찾을 수 없습니다.")
			return []

		# 년도와 월 정보 추출
		year, month = self._extract_year_month(calendar_table)

		available_dates = []

		# 모든 날짜 셀 찾기
		date_cells = calendar_table.find_all('div', attrs={'day': True})

		for cell in date_cells:
			date_info = self._process_date_cell(cell, year, month)
			if date_info:
				date_info[ReservationMonitorKey.TARGET] = target
				available_dates.append(date_info)

		return available_dates


	def run(self) -> int:
		"""
		메인 실행 함수

		Returns:
			int: 실행 결과 코드 (0: 성공, -1: 데이터 가져오기 실패, -2: 설정 로드 실패)
		"""
		self._load_config() # 모니터링 주기별로 설정을 다시 읽어들임
		if self.config is None:
			return -2

		# self._init_kakao_msg()

		self.logger.info("객실 예약 정보 분석 중...")

		is_dnd = False
		while (True):
			now = datetime.now()
			if ( (is_dnd == False) and (now.hour >= self.DND_start_hour) ):
				is_dnd = True
				dnd_end_time = now + timedelta(hours = self.DND_duration_hours)
				self.logger.info(f"start DND: ~ {dnd_end_time.isoformat()}")

			if (is_dnd and (now < dnd_end_time)):
				sleep(self.minitoring_cycle + uniform(0, self.minitoring_cycle))
				continue

			is_dnd = False
			try:
				self._load_config() # 모니터링 주기별로 설정을 다시 읽어들임
				if self.config is None:
					return -2

				# self.MSG.refresh_token = self.refresh_token
				# self.MSG.refresh_token_expires_at = self.refresh_token_expires_at

				results = self.monitor_all_target()

				# 결과 출력
				if (len(results) > 0):
					self.display_results(results)

					# current_time = time()
					# if (current_time > self.MSG.access_token_expires_at):
					# 	self.MSG.refresh_access_token()
					# 	self.logger.info(f'KAKAO token refreshed.')

					# self._send_kakao_message_to_me(results)
					self._send_telegram_chat_group(results)
			except Exception as e:
				self.logger.error(f"모니터링 중 오류 발생: {e}", exc_info=True)
				return -1

			sleep(self.minitoring_cycle + uniform(0, self.minitoring_cycle))


def main() -> int:
	"""
	스크립트 직접 실행 시 호출되는 함수

	Returns:
		int: 실행 결과 코드 (0: 성공, -1: 데이터 가져오기 실패, -2: 설정 로드 실패)
	"""
	monitor = ReservationMonitor()
	return monitor.run()



if __name__ == "__main__":
	exit_code = main()
	exit(exit_code)
