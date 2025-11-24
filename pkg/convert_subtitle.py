# -*- coding: utf-8 -*-
# 자막 변환 프로그램 (smi -> srt)
# made : hbesthee@naver.com
# date : 2025-11-24

# Original Packages
from pathlib import Path
from typing import Dict, Final, List, Optional

import argparse
import json
import logging
import os
import re



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





class ConfigKey:
	"""설정 파일 키 정의"""
	LOGGING_LEVEL: Final[str] = "logging_level"
	BLANK_TIME_SECONDS: Final[str] = "blank_time_seconds"
	OUTPUT_FOLDER: Final[str] = "output_folder"



class ConfigDef:
	"""설정 기본값 정의"""
	LOGGING_LEVEL: Final[int] = 20  # INFO
	BLANK_TIME_SECONDS: Final[int] = 300  # 5분
	OUTPUT_FOLDER: Final[str] = "./subtitles/output"
	CONFIG_PATH: Final[str] = "conf/subtitle_converter.json"
	LOG_PATH: Final[str] = "logs/subtitle_converter.log"



class ConfigManager:
	"""
	설정 관리 클래스
	"""
	def __init__(self, config_path: str=ConfigDef.CONFIG_PATH):
		"""
		설정 관리자 초기화

		Args:
			config_path: 설정 파일 경로
		"""
		self.config_path = config_path
		self.config = self._load_config()


	def _create_default_config(self) -> None:
		"""기본 설정 파일 생성"""
		Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)

		config = self._get_default_config()

		with open(self.config_path, 'w', encoding='utf-8') as f:
			json.dump(config, f, indent=4, ensure_ascii=False)

		print(f"기본 설정 파일 생성: {self.config_path}")


	def _get_default_config(self) -> Dict:
		"""
		기본 설정 반환

		Returns:
			Dict: 기본 설정 딕셔너리
		"""
		return {
			ConfigKey.LOGGING_LEVEL: ConfigDef.LOGGING_LEVEL,
			ConfigKey.BLANK_TIME_SECONDS: ConfigDef.BLANK_TIME_SECONDS,
			ConfigKey.OUTPUT_FOLDER: ConfigDef.OUTPUT_FOLDER
		}


	def _load_config(self) -> Dict:
		"""
		설정 파일 로드

		Returns:
			Dict: 설정 딕셔너리
		"""
		if (not os.path.exists(self.config_path)):
			self._create_default_config()

		try:
			with open(self.config_path, 'r', encoding='utf-8') as f:
				config = json.load(f)
			return config
		except Exception as e:
			print(f"설정 파일 로드 실패: {e}")
			print("기본 설정을 사용합니다.")
			return self._get_default_config()


	def get(self, key: str, default=None):
		"""
		설정 값 가져오기

		Args:
			key: 설정 키
			default: 기본값

		Returns:
			설정 값
		"""
		return self.config.get(key, default)



class SubtitleConverter:
	"""자막 파일 변환 클래스"""

	def __init__(self, logger: logging.Logger, gap_threshold_ms: int):
		"""
		자막 변환기 초기화

		Args:
			logger: 로거 인스턴스
			gap_threshold_ms: 빈 자막 삽입 임계값 (밀리초)
		"""
		self.logger = logger
		self.gap_threshold_ms = gap_threshold_ms


	def convert_file(self, file_path: str, output_folder: str) -> None:
		"""
		자막 파일 변환 메인 함수

		Args:
			file_path: 입력 파일 경로
			output_folder: 출력 폴더 경로
		"""
		self.logger.info(f"처리 시작: {file_path}")

		try:
			self.convert_to_utf8(file_path)

			with open(file_path, 'r', encoding='utf-8') as f:
				content = f.read()

			file_ext = Path(file_path).suffix.lower()
			file_name = Path(file_path).stem

			if (file_ext == '.smi'):
				self.logger.info("SMI → SRT 변환")
				subtitles = self.parse_smi(content)
				output_name = f"{file_name}.srt"
			elif (file_ext == '.srt'):
				self.logger.info("SRT 형식 처리")
				subtitles = self.parse_srt(content)
				output_name = f"{file_name}.srt"
			else:
				self.logger.warning(f"지원하지 않는 형식: {file_ext}")
				return

			subtitles = self.insert_blank_subtitles(subtitles)

			srt_content = self.generate_srt(subtitles)

			Path(output_folder).mkdir(parents=True, exist_ok=True)

			output_path = os.path.join(output_folder, output_name)

			with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
				f.write(srt_content)

			self.logger.info(f"처리 완료: {output_path}")
			self.logger.info(f"총 자막 수: {len(subtitles)}")

		except Exception as e:
			self.logger.error(f"처리 중 오류 발생: {e}", exc_info=True)


	def convert_to_utf8(self, file_path: str) -> bool:
		"""
		UTF-8로 인코딩 변환

		Args:
			file_path: 파일 경로

		Returns:
			bool: 변환 여부
		"""
		encoding = self.detect_encoding(file_path)

		if (encoding and encoding.lower() != 'utf-8'):
			self.logger.info(f"인코딩 변환: {encoding} → UTF-8")
			with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
				content = f.read()

			with open(file_path, 'w', encoding='utf-8') as f:
				f.write(content)
			return True
		return False


	@staticmethod
	def detect_encoding(file_path: str) -> Optional[str]:
		"""
		파일 인코딩 감지

		Args:
			file_path: 파일 경로

		Returns:
			Optional[str]: 감지된 인코딩
		"""
		try:
			with open(file_path, 'rb') as f:
				data = f.read()
				# 1단계: UTF-8로 디코딩 시도
				try:
					text = data.decode('utf-8')
				except UnicodeDecodeError:
					return 'euc-kr'   # UTF-8로 안 풀리면 euc-kr로 가정

				# 2단계: 전부 ASCII면 애매하지만, 그냥 UTF-8로 두는 편이 일반적
				if all(b < 0x80 for b in data):
					return 'utf-8'

				# 3단계: UTF-8로 풀렸더라도 한글이 거의 없고,
				#        0x80 이상 바이트 패턴이 "수상한" 경우를 euc-kr로 의심할 수 있다.
				#   예: 연속된 2바이트가 euc-kr 유효 범위(0xA1–0xFE, 0xA1–0xFE)에 많이 등장하면 euc-kr로 보는 식의 휴리스틱
				#   (아래는 매우 단순한 예)
				ko_chars = sum(0xAC00 <= ord(ch) <= 0xD7A3 for ch in text)
				if ko_chars >= 1:
					return 'utf-8'
				else:
					return 'euc-kr'
		except ImportError:
			return 'utf-8'


	@staticmethod
	def format_srt_time(ms: int) -> str:
		"""
		밀리초를 SRT 시간 형식으로 변환

		Args:
			ms: 밀리초

		Returns:
			str: SRT 시간 형식 문자열
		"""
		hours = ms // 3600000
		minutes = (ms % 3600000) // 60000
		seconds = (ms % 60000) // 1000
		milliseconds = ms % 1000
		return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


	def generate_srt(self, subtitles: List[Dict]) -> str:
		"""
		SRT 형식으로 자막파일 생성

		Args:
			subtitles: 자막 리스트

		Returns:
			str: SRT 형식 문자열
		"""
		srt_content = []

		for i, sub in enumerate(subtitles, 1):
			start_time = self.format_srt_time(sub['start'])
			end_time = self.format_srt_time(sub['end'])

			srt_content.append(f"{i}")
			srt_content.append(f"{start_time} --> {end_time}")
			srt_content.append(sub['text'])
			srt_content.append("")

		return '\n'.join(srt_content)


	def insert_blank_subtitles(self, subtitles: List[Dict]) -> List[Dict]:
		"""
		빈 자막 삽입

		Args:
			subtitles: 자막 리스트

		Returns:
			List[Dict]: 빈 자막이 삽입된 자막 리스트
		"""
		result = []

		for i, sub in enumerate(subtitles):
			result.append(sub)

			if (i + 1 < len(subtitles)):
				gap = subtitles[i + 1]['start'] - sub['end']

				if (gap > self.gap_threshold_ms):
					blank_start = sub['end'] + 500
					blank_end = subtitles[i + 1]['start'] - 500
					result.append({
						'start': blank_start,
						'end': blank_end,
						'text': ''
					})
					self.logger.info(
						f"빈 자막 삽입: {gap/1000:.1f}초 간격 발견"
					)

		return result


	def parse_smi(self, content: str) -> List[Dict]:
		"""
		SMI 파일 파싱

		Args:
			content: SMI 파일 내용

		Returns:
			List[Dict]: 자막 리스트
		"""
		sync_pattern = re.compile(
			r'<SYNC Start=(\d+)>\s*<P Class=\w+>(.*?)(?=<SYNC|$)',
			re.IGNORECASE | re.DOTALL
		)

		subtitles = []
		matches = sync_pattern.findall(content)

		for i, (start_time, text) in enumerate(matches):
			text = re.sub(r'<[^>]+>', '', text)
			text = text.replace('&nbsp;', ' ').strip()

			if (text):
				start_ms = int(start_time)
				if (i + 1 < len(matches)):
					end_ms = int(matches[i + 1][0])
				else:
					end_ms = start_ms + 2000

				subtitles.append({
					'start': start_ms,
					'end': end_ms,
					'text': text
				})

		return subtitles


	def parse_srt(self, content: str) -> List[Dict]:
		"""
		SRT 파일 파싱

		Args:
			content: SRT 파일 내용

		Returns:
			List[Dict]: 자막 리스트
		"""
		subtitles = []
		blocks = re.split(r'\n\s*\n', content.strip())

		for block in blocks:
			lines = block.strip().split('\n')
			if (len(lines) < 3):
				continue

			time_match = re.match(
				r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
				lines[1]
			)

			if (time_match):
				h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, time_match.groups())
				start_ms = (h1 * 3600 + m1 * 60 + s1) * 1000 + ms1
				end_ms = (h2 * 3600 + m2 * 60 + s2) * 1000 + ms2
				text = '\n'.join(lines[2:])

				subtitles.append({
					'start': start_ms,
					'end': end_ms,
					'text': text
				})

		return subtitles



class SubtitleBatchProcessor:
	"""자막 일괄 처리 클래스"""

	def __init__(
		self,
		converter: SubtitleConverter,
		logger: logging.Logger
	):
		"""
		일괄 처리기 초기화

		Args:
			converter: 자막 변환기 인스턴스
			logger: 로거 인스턴스
		"""
		self.converter = converter
		self.logger = logger


	def process_folder(self, input_folder: str, output_folder: str) -> None:
		"""
		폴더 내 모든 자막 파일 처리

		Args:
			input_folder: 입력 폴더 경로
			output_folder: 출력 폴더 경로
		"""
		if (not os.path.exists(input_folder)):
			self.logger.error(f"입력 폴더가 존재하지 않습니다: {input_folder}")
			return

		subtitle_files = []
		for ext in ['.smi', '.srt']:
			subtitle_files.extend(Path(input_folder).glob(f"*{ext}"))

		if (not subtitle_files):
			self.logger.warning(f"처리할 자막 파일이 없습니다: {input_folder}")
			return

		self.logger.info(f"발견된 자막 파일 수: {len(subtitle_files)}")

		success_count = 0
		fail_count = 0

		for file_path in subtitle_files:
			try:
				self.converter.convert_file(str(file_path), output_folder)
				success_count += 1
			except Exception as e:
				self.logger.error(f"파일 처리 실패: {file_path} - {e}")
				fail_count += 1

		self.logger.info("=" * 50)
		self.logger.info(f"처리 완료: 성공 {success_count}개, 실패 {fail_count}개")
		self.logger.info("=" * 50)



def parse_arguments() -> argparse.Namespace:
	"""
	명령행 인수 파싱

	Returns:
		argparse.Namespace: 파싱된 인수
	"""
	parser = argparse.ArgumentParser(
		description='자막 파일 자동 변환 프로그램'
	)

	parser.add_argument(
		'--folder',
		type=str,
		required=True,
		help='변환할 자막 파일들이 위치한 폴더 경로'
	)

	parser.add_argument(
		'--output',
		type=str,
		help='변환된 파일을 저장할 폴더 경로 (기본값: 설정 파일 참조)'
	)

	parser.add_argument(
		'--blank_time',
		type=int,
		help='빈 자막을 추가할 시간 간격 (초 단위, 기본값: 설정 파일 참조)'
	)

	return parser.parse_args()


def main():
	"""메인 함수"""
	args = parse_arguments()

	config_manager = ConfigManager(ConfigDef.CONFIG_PATH)

	logging_level = config_manager.get(
		ConfigKey.LOGGING_LEVEL,
		ConfigDef.LOGGING_LEVEL
	)
	blank_time_seconds = args.blank_time or config_manager.get(
		ConfigKey.BLANK_TIME_SECONDS,
		ConfigDef.BLANK_TIME_SECONDS
	)
	output_folder = args.output or config_manager.get(
		ConfigKey.OUTPUT_FOLDER,
		ConfigDef.OUTPUT_FOLDER
	)

	logger = createLogger(log_level=config_manager.get(ConfigKey.LOGGING_LEVEL, ConfigDef.LOGGING_LEVEL)
			, log_filename='subtitle_convert'
			, logger_name='subtitle_convert'
	)

	logger.info("=" * 50)
	logger.info("자막 자동 변환 프로그램 시작")
	logger.info("=" * 50)
	logger.info(f"설정 파일: {ConfigDef.CONFIG_PATH}")
	logger.info(f"로그 파일: {ConfigDef.LOG_PATH}")
	logger.info(f"입력 폴더: {os.path.abspath(args.folder)}")
	logger.info(f"출력 폴더: {os.path.abspath(output_folder)}")
	logger.info(f"빈 자막 간격 임계값: {blank_time_seconds}초")
	logger.info(f"로깅 레벨: {logging_level}")
	logger.info("지원 형식: SMI, SRT")
	logger.info("=" * 50)

	gap_threshold_ms = blank_time_seconds * 1000
	converter = SubtitleConverter(logger, gap_threshold_ms)

	processor = SubtitleBatchProcessor(converter, logger)
	processor.process_folder(args.folder, output_folder)


if (__name__ == "__main__"):
	main()