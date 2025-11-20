# -*- coding: utf-8 -*-
# 파일명 변환 프로그램
# made : hbesthee@naver.com
# date : 2025-11-20
#
# requirements: pip install beautifulsoup4 requests

# Original Packages
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from typing import Final, Optional
from urllib.parse import quote

import logging
import re
import shutil
import sys
import time


# Third-party Packages
from bs4 import BeautifulSoup

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






# 전역 logger 설정
logger: logging.Logger = None



class FilenameKey:
	"""
	파일명 분석에 사용되는 키 상수 클래스
	"""
	AUTHOR: Final[str] = "author"
	TITLE: Final[str] = "title"
	START_NUM: Final[str] = "start_num"
	END_NUM: Final[str] = "end_num"
	IS_ADULT: Final[str] = "is_adult"



class FilenameDef:
	"""
	파일명 변환에 사용되는 기본값 상수 클래스
	"""
	ADULT_TAG: Final[str] = "[19N]"
	ADULT_SUFFIX: Final[str] = "+19"
	COMPLETE_TAG: Final[str] = "완"
	EXTENSION: Final[str] = ".txt"
	CONVERTED_FOLDER: Final[str] = "converted"
	HIGH_SCORE_THRESHOLD: Final[float] = 9.0



class NaverApiKey:
	"""
	네이버 API 관련 키 상수 클래스
	"""
	BASE_URL: Final[str] = "https://series.naver.com/search/search.series"
	PARAM_TYPE: Final[str] = "t"
	PARAM_QUERY: Final[str] = "q"
	TYPE_NOVEL: Final[str] = "novel"
	CLASS_TITLE: Final[str] = "N=a:nov.title"
	CLASS_SCORE: Final[str] = "score_num"
	CLASS_AUTHOR: Final[str] = "author"



class SearchResult:
	"""
	검색 결과를 저장하는 클래스
	"""

	def __init__(self, title: str, author: str, score: float):
		"""
		SearchResult 초기화

		Args:
			title (str): 작품 제목
			author (str): 작가명
			score (float): 평점
		"""
		self.title = title
		self.author = author
		self.score = score



class FilenameParser:
	"""
	파일명을 분석하는 클래스
	"""

	@staticmethod
	def parse(filename: str) -> Optional[dict[str, str]]:
		"""
		파일명을 분석하여 구성 요소를 추출

		Args:
			filename (str): 분석할 파일명

		Returns:
			Optional[dict[str, str]]: 분석 결과 딕셔너리 또는 None
				- author: 지은이
				- title: 제목
				- start_num: 시작 번호
				- end_num: 끝 번호
				- is_adult: 성인물 여부
		"""
		# [19N] 태그 확인
		is_adult = FilenameDef.ADULT_TAG in filename

		# 첫 번째 대괄호로 둘러싸인 부분 추출 (지은이)
		author_match = re.match(r'^\[([^\]]+)\]', filename)
		if (not author_match):
			return None

		author = author_match.group(1)

		# 모든 대괄호로 둘러싸인 부분 제거
		filename_without_brackets = re.sub(r'\[[^\]]*\]', '', filename).strip()

		# 시작번호-끝번호화 패턴 추출
		episode_pattern = r'(\d+)-(\d+)화'
		episode_match = re.search(episode_pattern, filename_without_brackets)

		if (not episode_match):
			return None

		start_num = episode_match.group(1)
		end_num = episode_match.group(2)

		# 제목 추출 (에피소드 정보 앞까지)
		title = filename_without_brackets[:episode_match.start()].strip()

		return {
			FilenameKey.AUTHOR: author,
			FilenameKey.TITLE: title,
			FilenameKey.START_NUM: start_num,
			FilenameKey.END_NUM: end_num,
			FilenameKey.IS_ADULT: str(is_adult)
		}


class FilenameConverter:
	"""
	파일명을 새로운 형식으로 변환하는 클래스
	"""

	@staticmethod
	def convert(parse_result: dict[str, str]) -> str:
		"""
		분석 결과를 기반으로 새로운 파일명 생성

		Args:
			parse_result (dict[str, str]): 파일명 분석 결과

		Returns:
			str: 변환된 파일명
		"""
		title = parse_result[FilenameKey.TITLE]
		author = parse_result[FilenameKey.AUTHOR]
		start_num = parse_result[FilenameKey.START_NUM]
		end_num = parse_result[FilenameKey.END_NUM]
		is_adult = parse_result[FilenameKey.IS_ADULT] == "True"

		# 변환 후 파일명 생성
		if (is_adult):
			new_filename = f"{title} [{author}] ({start_num}~{end_num}, {FilenameDef.COMPLETE_TAG}{FilenameDef.ADULT_SUFFIX}){FilenameDef.EXTENSION}"
		else:
			new_filename = f"{title} [{author}] ({start_num}~{end_num}, {FilenameDef.COMPLETE_TAG}){FilenameDef.EXTENSION}"

		return new_filename


class NaverSeriesSearcher:
	"""
	네이버 시리즈 검색을 수행하는 클래스
	"""

	def __init__(self):
		"""
		NaverSeriesSearcher 초기화
		"""
		self.session = requests.Session()
		self.session.headers.update({
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
		})


	def search(self, title: str) -> list[SearchResult]:
		"""
		네이버 시리즈에서 작품을 검색

		Args:
			title (str): 검색할 작품 제목

		Returns:
			list[SearchResult]: 검색 결과 리스트
		"""
		try:
			# URL 파라미터 구성
			params = {
				NaverApiKey.PARAM_TYPE: NaverApiKey.TYPE_NOVEL,
				NaverApiKey.PARAM_QUERY: title
			}

			# API 호출
			response = self.session.get(NaverApiKey.BASE_URL, params=params, timeout=10)
			response.raise_for_status()

			# HTML 파싱
			soup = BeautifulSoup(response.text, 'html.parser')

			results = []

			# 검색 결과 항목들 찾기
			title_elements = soup.find_all(class_=NaverApiKey.CLASS_TITLE)

			for title_elem in title_elements:
				# 제목 추출 및 '\n' 이후 내용 제거
				search_title = title_elem.get_text(strip=True)
				search_title = search_title.split('\n')[0].strip()

				# 부모 요소에서 점수와 작가 찾기
				parent = title_elem.find_parent('li') or title_elem.find_parent('div')
				if (not parent):
					continue

				# 점수 추출
				score_elem = parent.find(class_=NaverApiKey.CLASS_SCORE)
				if (not score_elem):
					continue

				try:
					score = float(score_elem.get_text(strip=True))
				except ValueError:
					continue

				# 작가 추출
				author_elem = parent.find(class_=NaverApiKey.CLASS_AUTHOR)
				if (not author_elem):
					continue

				search_author = author_elem.get_text(strip=True)

				results.append(SearchResult(search_title, search_author, score))

			return results

		except Exception as e:
			logger.error(f"검색 오류: {str(e)}", exc_info=True)
			return []


	def find_matching_result(
		self,
		results: list[SearchResult],
		title: str,
		author: str
	) -> Optional[SearchResult]:
		"""
		검색 결과에서 제목과 작가가 일치하는 항목 찾기

		Args:
			results (list[SearchResult]): 검색 결과 리스트
			title (str): 찾을 제목
			author (str): 찾을 작가명

		Returns:
			Optional[SearchResult]: 일치하는 결과 또는 None
		"""
		for result in results:
			if (result.title == title and result.author == author):
				return result

		return None


class FileRenamer:
	"""
	파일명 변환을 실행하는 클래스
	"""

	def __init__(self, folder_path: str):
		"""
		FileRenamer 초기화

		Args:
			folder_path (str): 파일들이 위치한 폴더 경로
		"""
		self.folder_path = Path(folder_path)
		self.searcher = NaverSeriesSearcher()


	def _create_converted_folder(self) -> Path:
		"""
		converted 폴더 생성

		Returns:
			Path: converted 폴더 경로
		"""
		converted_path = self.folder_path / FilenameDef.CONVERTED_FOLDER
		converted_path.mkdir(exist_ok=True)
		return converted_path


	def rename_files(self) -> None:
		"""
		폴더 내의 모든 .txt 파일의 이름을 변환
		"""
		if (not self.folder_path.exists()):
			logger.error(f"폴더를 찾을 수 없습니다 - {self.folder_path}")
			return

		if (not self.folder_path.is_dir()):
			logger.error(f"지정된 경로가 폴더가 아닙니다 - {self.folder_path}")
			return

		# .txt 파일 목록 가져오기
		txt_files = list(self.folder_path.glob("*.txt"))

		if (not txt_files):
			logger.warning(f"변환할 .txt 파일이 없습니다 - {self.folder_path}")
			return

		# converted 폴더 생성
		converted_folder = self._create_converted_folder()

		success_count = 0
		fail_count = 0
		high_score_count = 0

		for file_path in txt_files:
			original_filename = file_path.name

			# 파일명 분석
			parse_result = FilenameParser.parse(original_filename)

			if (parse_result is None):
				logger.warning(f"건너뜀: {original_filename} (분석 실패)")
				fail_count += 1
				continue

			title = parse_result[FilenameKey.TITLE]
			author = parse_result[FilenameKey.AUTHOR]

			# 네이버 시리즈 검색
			logger.info(f"검색 중: {title} by {author}")
			search_results = self.searcher.search(title)

			# 일치하는 결과 찾기
			matching_result = self.searcher.find_matching_result(
				search_results,
				title,
				author
			)

			if (matching_result is None):
				logger.warning(f"건너뜀: {original_filename} (검색 결과 없음)")
				fail_count += 1
				time.sleep(1)  # API 호출 간격 조절
				continue

			logger.info(f"검색 완료: 평점 {matching_result.score}")

			# 파일명 변환
			new_filename = FilenameConverter.convert(parse_result)

			# 파일명 변경 및 이동
			try:
				# 평점이 9.0 이상이면 converted 폴더로 이동
				if (matching_result.score >= FilenameDef.HIGH_SCORE_THRESHOLD):
					new_file_path = converted_folder / new_filename
					shutil.move(str(file_path), str(new_file_path))
					logger.info(f"변환 및 이동 완료: {original_filename} -> {new_filename} (평점 {matching_result.score})")
					high_score_count += 1
				else:
					new_file_path = file_path.parent / new_filename
					file_path.rename(new_file_path)
					logger.info(f"변환 완료: {original_filename} -> {new_filename} (평점 {matching_result.score})")

				success_count += 1
			except Exception as e:
				logger.error(f"{original_filename} 변환 실패 - {str(e)}")
				fail_count += 1

			time.sleep(1)  # API 호출 간격 조절

		logger.info(f"\n변환 완료: {success_count}개, 실패: {fail_count}개")
		logger.info(f"고평점 작품(9.0 이상): {high_score_count}개")



def main():
	"""
	메인 함수 - 명령행 인자를 처리하고 파일명 변환을 실행
	"""
	# 로거 설정
	global logger

	logger = createLogger(log_level=logging.DEBUG
						, log_filename="file_converter"
						, logger_name="file_converter"
		)

	parser = ArgumentParser(description="파일명을 지정된 형식으로 변환합니다.")
	parser.add_argument(
		"--folder",
		type=str,
		required=True,
		help="변환할 파일이 있는 폴더 경로"
	)

	args = parser.parse_args()

	logger.info(f"파일명 변환 시작 - 폴더: {args.folder}")

	# 파일명 변환 실행
	renamer = FileRenamer(args.folder)
	renamer.rename_files()

	logger.info("파일명 변환 종료")


if __name__ == "__main__":
	main()