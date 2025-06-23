# -*- coding: utf-8 -*-
# 객실 예약정보 모니터링 예제
# made : hbesthee@naver.com
# date : 2025-06-23

# Original Packages
from datetime import datetime, timedelta
from locale import LC_TIME, setlocale

import re



# Third-party Packages
from bs4 import BeautifulSoup

import requests



# User's Package
from os import getcwd
from sys import path as sys_path
sys_path.append(getcwd())

from lib.json_util import load_json_conf



def get_reservation_data(url):
	"""
	객실 예약 웹사이트에서 HTML 데이터를 가져옵니다.
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


def parse_room_availability(html_content, filter_weekday):
	"""
	HTML 내용을 파싱하여 객실 예약 정보를 분석합니다.
	"""
	soup = BeautifulSoup(html_content, 'html.parser')

	# 캘린더 테이블 찾기
	calendar_table = soup.find('table', class_='calendar')
	if not calendar_table:
		print(f"캘린더 테이블을 찾을 수 없습니다.")
		return []

	# 년도와 월 정보 추출
	year_month_link = calendar_table.find('a', href=re.compile(r'reservRoom$'))
	if year_month_link:
		year_month_text = year_month_link.get_text()
		# "2025년 6월" 형태에서 년도와 월 추출
		year_match = re.search(r'(\d{4})년', year_month_text)
		month_match = re.search(r'(\d{1,2})월', year_month_text)

		if year_match and month_match:
			year = int(year_match.group(1))
			month = int(month_match.group(1))
		else:
			# 현재 날짜 기준으로 설정
			now = datetime.now()
			year, month = now.year, now.month
	else:
		now = datetime.now()
		year, month = now.year, now.month

	available_dates = []

	# 모든 날짜 셀 찾기
	date_cells = calendar_table.find_all('div', attrs={'day': True})

	for cell in date_cells:
		# 해당 날짜 객체 생성
		try:
			day = int(cell.get('day'))
			date_obj = datetime(year, month, day)
			weekday = date_obj.weekday()  # 0=월요일, 6=일요일

			# 요일 필터링 처리 : 금요일(4) / 토요일(5)
			if (not (weekday in filter_weekday)):
				continue

			# weekday_name = (date_obj.strftime('%A'))
			weekday_name = date_obj.strftime('%A').encode('utf-8', 'surrogateescape').decode('utf-8', 'surrogateescape')

			# 휴원일 확인
			if cell.find('span', string='휴원일'):
				continue

			# 객실 정보 확인
			room_types = cell.find('ul', class_='room-type')
			if room_types:
				available_rooms = []
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
							available_rooms.append(f"{room_text} ({available_count}개)")

				if available_rooms:
					available_dates.append({
						'date': date_obj.strftime('%Y-%m-%d'),
						'weekday': weekday_name,
						'day': day,
						'available_rooms': available_rooms
					})

		except ValueError:
			# 잘못된 날짜는 건너뛰기
			continue

	return available_dates


def display_results(available_dates):
	"""
	결과를 보기 좋게 출력합니다.
	"""
	if not available_dates:
		print("예약 가능한 날짜가 없습니다.")
		return

	print("=" * 35)
	print("예약 가능한 날짜")
	print("=" * 35)

	for date_info in available_dates:
		print(f"\n📅 {date_info['date']} ({date_info['weekday']})")
		print("   예약 가능한 객실:")
		for room in date_info['available_rooms']:
			print(f"   • {room}")



def main():
	"""
	메인 실행 함수
	"""
	setlocale(LC_TIME, 'ko_KR.UTF-8')
	print("객실 예약 정보를 분석 중...")

	conf, err_msg = load_json_conf('conf/reservation_monitor.json')
	if (err_msg != ''):
		print(f'conf load fail!: {err_msg}')
		return -2

	filter_weekday = conf.get('filter_weekday', [0, 1, 2, 3, 4, 5, 6])
	target_urls = conf.get('target', [])
	target_count = len(target_urls)
	for target_index in range(target_count):
		url, is_monitoring = target_urls[target_index]
		if (is_monitoring != 1):
			continue

		# 실제 웹사이트에서 데이터 가져오기
		url = datetime.now().strftime(url)
		html_content = get_reservation_data(url)

		if html_content is None:
			print(f"'{url}'에서 데이터를 가져올 수 없습니다.")
			return -1

		# HTML 파싱 및 분석
		available_dates = parse_room_availability(html_content, filter_weekday)

		# 결과 출력
		display_results(available_dates)



if (__name__ == "__main__"):
	main()
