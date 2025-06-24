# -*- coding: utf-8 -*-
# 객실 예약정보 모니터링 클래스
# made : hbesthee@naver.com
# date : 2025-06-23

# Original Packages
from datetime import datetime, timedelta
from locale import LC_TIME, setlocale
from time import sleep
from typing import List, Dict, Final, Tuple, Optional

import re



# Third-party Packages
from bs4 import BeautifulSoup
from PyKakao import Message

import requests



# User's Package
from os import getcwd
from sys import path as sys_path
sys_path.append(getcwd())

from lib.json_util import load_json_conf



class ReservationMonitorKey:
	"""객실 예약 모니터링 관련 각종 키 상수 문자열 정의 클래스"""
	LOG_LEVEL: Final							= 'log_level'
	FILTER_WEEKDAY: Final						= 'filter_weekday'
	TARGET: Final								= 'target'
	MONITOR_NEXT_MONTH: Final					= 'monitor_next_month'
	MONITORING_CYCLE: Final						= 'monitoring_cycle'
	APP_ID: Final								= 'app_id'
	APP_NAME: Final								= 'app_name'
	REST_API_KEY: Final							= 'rest_api_key'
	TOKEN_KEY: Final							= 'token_key'



class ReservationMonitorDef:
	"""객실 예약 모니터링 관련 각종 기본값 상수 정의 클래스"""
	LOG_LEVEL: Final							= 20
	FILTER_WEEKDAY: Final						= [0, 1, 2, 3, 4, 5, 6]
	TARGET: Final								= []
	MONITOR_NEXT_MONTH: Final					= 0
	MONITORING_CYCLE: Final						= 600
	APP_ID: Final								= ''
	APP_NAME: Final								= ''
	REST_API_KEY: Final							= ''
	TOKEN_KEY: Final							= ''



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
				, "monitor_next_month":1
				, "monitoring_cycle":600
				, "target":[
					["https://target1.url/cal/%Y/%m", 1]
					, ["https://target2.url/cal/%Y/%m", 0]
				]
				, "app_id":"1234"
				, "app_name":"my_app-name"
				, "rest_api_key":"my_app-rest_api_key"
				, "token_key":"my_app-token_key"
			}

		Args:
			config_path (str): 설정 파일 경로
		"""
		self.config_path = config_path
		self.config = None

		self.log_level				= ReservationMonitorDef.LOG_LEVEL
		self.filter_weekday			= ReservationMonitorDef.FILTER_WEEKDAY
		self.is_monitor_next_month	= ReservationMonitorDef.MONITOR_NEXT_MONTH == 1
		self.minitoring_cycle		= ReservationMonitorDef.MONITORING_CYCLE
		self.target_urls			= ReservationMonitorDef.TARGET
		self.app_id					= ReservationMonitorDef.APP_ID
		self.app_name				= ReservationMonitorDef.APP_NAME
		self.rest_api_key			= ReservationMonitorDef.REST_API_KEY
		self.token_key				= ReservationMonitorDef.TOKEN_KEY

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

			for room in room_items:
				# 예약 가능한 객실 찾기 (resY 클래스)
				if room.find('span', class_='resY'):
					room_link = room.find('a')
					if room_link:
						room_text = room_link.get_text().strip()
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
		self.MSG = Message(service_key = self.rest_api_key)

		# 액세스 토큰 설정
		self.MSG.set_access_token(self.token_key)

		pass


	def _load_config(self) -> bool:
		"""
		설정 파일 로드

		Returns:
			bool: 로드 성공 여부
		"""
		try:
			self.config, err_msg = load_json_conf(self.config_path)
			if err_msg != '':
				print(f'conf load fail!: {err_msg}')
				return False

			self.log_level				= self.config.get(ReservationMonitorKey.LOG_LEVEL,			ReservationMonitorDef.LOG_LEVEL)
			self.filter_weekday			= self.config.get(ReservationMonitorKey.FILTER_WEEKDAY,		ReservationMonitorDef.FILTER_WEEKDAY)
			self.is_monitor_next_month	= self.config.get(ReservationMonitorKey.MONITOR_NEXT_MONTH,	ReservationMonitorDef.MONITOR_NEXT_MONTH) == 1
			self.minitoring_cycle		= self.config.get(ReservationMonitorKey.MONITORING_CYCLE,	ReservationMonitorDef.MONITORING_CYCLE)
			self.target_urls			= self.config.get(ReservationMonitorKey.TARGET,				ReservationMonitorDef.TARGET)
			self.app_id					= self.config.get(ReservationMonitorKey.APP_ID,				ReservationMonitorDef.APP_ID)
			self.app_name				= self.config.get(ReservationMonitorKey.APP_NAME,			ReservationMonitorDef.APP_NAME)
			self.rest_api_key			= self.config.get(ReservationMonitorKey.REST_API_KEY,		ReservationMonitorDef.REST_API_KEY)
			self.token_key				= self.config.get(ReservationMonitorKey.TOKEN_KEY,			ReservationMonitorDef.TOKEN_KEY)
			return True
		except Exception as e:
			print(f'Config load error: {e}')
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

			# 요일 필터링 처리
			if (weekday not in self.filter_weekday):
				return None

			weekday_name = date_obj.strftime('%a').encode('utf-8', 'surrogateescape').decode('utf-8', 'surrogateescape')

			# 휴원일 확인
			if (cell.find('span', string='휴원일')):
				return None

			# 객실 정보 확인
			available_rooms = self._extract_available_rooms(cell)

			if (available_rooms):
				return {
					'date': date_obj.strftime('%Y-%m-%d'),
					'weekday': weekday_name,
					'day': day,
					'available_rooms': available_rooms
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
				message += (f"\n📅 {date_info['date']} ({date_info['weekday']})")
				for room in date_info['available_rooms']:
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


	def display_results(self, reservation_info: dict) -> None:
		"""
		결과를 보기 좋게 출력합니다.

		Args:
			reservation_info (dict): 예약 가능한 날짜 정보 목록
		"""
		print(f"{datetime.now().isoformat()=}")
		if (len(reservation_info) == 0):
			print("예약 가능한 날짜가 없습니다.")
			return

		for url, reservation_list in reservation_info.items():
			print("\n")
			print("=" * 80)
			print(f"Target URL = {url}")
			print("=" * 80)

			for date_info in reservation_list:
				print(f"\n📅 {date_info['date']} ({date_info['weekday']})")
				for room in date_info['available_rooms']:
					print(f"   • {room}")


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
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
			}
			response = requests.get(url, headers=headers)
			response.encoding = 'utf-8'
			response.raise_for_status()
			return response.text
		except Exception as e:
			print(f"웹사이트 접근 오류: {e}")
			return None


	def monitor_all_targets(self) -> Dict[str, List[Dict]]:
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

		for target_index, (url, is_monitoring) in enumerate(self.target_urls):
			print(f"모니터링 중... ({target_index + 1}/{len(self.target_urls)})")

			if (is_monitoring != 1):
				continue

			current_month_url = current_month.strftime(url)
			self.monitor_url(results, current_month_url)

			if (self.is_monitor_next_month):
				next_month_url = next_month.strftime(url)
				self.monitor_url(results, next_month_url)

		return results


	def monitor_url(self, results: dict, url: str) -> int:
		"""
		단일 URL에 대한 모니터링 수행

		Args:
			results (dict): 예약 가능한 객실 정보를 담을 dict 객체
			url (str): 모니터링할 URL

		Returns:
			int: 예약 가능한 날짜 수
		"""
		# 웹사이트에서 데이터 가져오기
		html_content = self.get_reservation_data(url)

		if (html_content is None):
			print(f"'{url}'에서 데이터를 가져올 수 없습니다.")
			return []

		# HTML 파싱 및 분석
		reservation_list = self.parse_room_availability(html_content)
		if (reservation_list != []):
			results[url] = reservation_list
		return len(reservation_list)


	def parse_room_availability(self, html_content: str) -> List[Dict]:
		"""
		HTML 내용을 파싱하여 객실 예약 정보를 분석합니다.

		Args:
			html_content (str): 파싱할 HTML 내용

		Returns:
			List[Dict]: 예약 가능한 날짜 정보 리스트
		"""
		soup = BeautifulSoup(html_content, 'html.parser')

		# 캘린더 테이블 찾기
		calendar_table = soup.find('table', class_='calendar')
		if not calendar_table:
			print(f"캘린더 테이블을 찾을 수 없습니다.")
			return []

		# 년도와 월 정보 추출
		year, month = self._extract_year_month(calendar_table)

		available_dates = []

		# 모든 날짜 셀 찾기
		date_cells = calendar_table.find_all('div', attrs={'day': True})

		for cell in date_cells:
			date_info = self._process_date_cell(cell, year, month)
			if date_info:
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

		self._init_kakao_msg()

		print("객실 예약 정보 분석 중...")

		while (True):
			try:
				self._load_config() # 모니터링 주기별로 설정을 다시 읽어들임
				if self.config is None:
					return -2

				results = self.monitor_all_targets()

				# 결과 출력
				self.display_results(results)
				self._send_kakao_message_to_me(results)
			except Exception as e:
				print(f"모니터링 중 오류 발생: {e}")
				return -1

			sleep(self.minitoring_cycle)


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
