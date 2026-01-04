# -*- coding: utf-8 -*-
# 자막 변환 프로그램 (smi -> srt) ; v1.1
# made : hbesthee@naver.com
# date : 2025-11-24

# Original Packages
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Final, List, Optional

import argparse
import json
import os
import re
import shutil



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
	BACKUP_FOLDERS: Final[str] = "backup_folders"



class ConfigDef:
	"""설정 기본값 정의"""
	LOGGING_LEVEL: Final[int] = 20  # INFO
	BLANK_TIME_SECONDS: Final[int] = 30  # 단위: 초
	BLANK_GAP_MS: Final[int] = 300  # 단위: 밀리초
	OUTPUT_FOLDER: Final[str] = "./subtitles/output"
	BACKUP_FOLDERS: Final[str] = "./subtitles/backup"
	CONFIG_PATH: Final[str] = "conf/subtitle_converter.json"
	LOG_PATH: Final[str] = "logs/subtitle_converter.log"



@dataclass
class ConfigManager:
	"""
	설정 관리 클래스 (DataClass)
	"""
	logging_level: int = 20
	blank_time_seconds: int = 300
	output_folder: str = "./subtitles/output"
	backup_folders: str = ""

	CONFIG_PATH: str = field(default="conf/subtitle_converter.json", init=False)
	LOG_PATH: str = field(default="logs/subtitle_converter.log", init=False)


	@classmethod
	def load_from_file(cls, config_path: str = "conf/subtitle_converter.json"):
		"""
		설정 파일에서 로드

		Args:
			config_path: 설정 파일 경로

		Returns:
			ConfigManager: 설정 관리자 인스턴스
		"""
		if (not os.path.exists(config_path)):
			cls._create_default_config(config_path)

		try:
			with open(config_path, 'r', encoding='utf-8') as f:
				config_data = json.load(f)

			instance = cls(**config_data)
			instance.CONFIG_PATH = config_path
			return instance
		except Exception as e:
			print(f"설정 파일 로드 실패: {e}")
			print("기본 설정을 사용합니다.")
			instance = cls()
			instance.CONFIG_PATH = config_path
			return instance


	@staticmethod
	def _create_default_config(config_path: str) -> None:
		"""
		기본 설정 파일 생성

		Args:
			config_path: 설정 파일 경로
		"""
		Path(config_path).parent.mkdir(parents=True, exist_ok=True)

		default_config = {
			"logging_level": 20,
			"blank_time_seconds": 300,
			"output_folder": "./subtitles/output",
			"backup_folders": ""
		}

		with open(config_path, 'w', encoding='utf-8') as f:
			json.dump(default_config, f, indent=4, ensure_ascii=False)

		print(f"기본 설정 파일 생성: {config_path}")


	def update_from_args(self, args: argparse.Namespace) -> None:
		"""
		명령행 인수로 설정 업데이트

		Args:
			args: 파싱된 명령행 인수
		"""
		field_names = {f.name for f in fields(self) if f.init}

		for field_name in field_names:
			arg_value = getattr(args, field_name, None)
			if (arg_value is not None):
				setattr(self, field_name, arg_value)


	def parse_backup_folders(self) -> List[str]:
		"""
		백업 폴더 문자열을 리스트로 변환

		Returns:
			List[str]: 백업 폴더 리스트
		"""
		if (not self.backup_folders):
			return []

		folders = [f.strip() for f in self.backup_folders.split(',')]
		return [f for f in folders if f]



class SubtitleConverter:
	"""
	자막 파일 변환 클래스
	"""

	def __init__(self):
		"""
		자막 변환기 초기화
		"""
		self.config = None
		self.logger = None
		self.gap_threshold_ms = 0


	def run(self, args: argparse.Namespace) -> None:
		"""
		지정된 폴더의 자막 파일 일괄 변환

		Args:
			args: 파싱된 명령행 인수
		"""
		self.config = ConfigManager.load_from_file()
		self.config.update_from_args(args)
		self._backup_folders = self.config.parse_backup_folders()

		self.logger = createLogger(
			self.config.LOG_PATH,
			self.config.logging_level
		)
		self.gap_threshold_ms = self.config.blank_time_seconds * 1000

		self.logger.info("=" * 50)
		self.logger.info("자막 자동 변환 프로그램 시작")
		self.logger.info("=" * 50)
		self.logger.info(f"설정 파일: {self.config.CONFIG_PATH}")
		self.logger.info(f"로그 파일: {self.config.LOG_PATH}")
		self.logger.info(f"입력 폴더: {os.path.abspath(args.folder)}")
		self.logger.info(f"출력 폴더: {os.path.abspath(self.config.output_folder)}")
		self.logger.info(f"빈 자막 간격 임계값: {self.config.blank_time_seconds}초")
		self.logger.info(f"백업 폴더: {self._backup_folders if self._backup_folders else '없음'}")
		self.logger.info(f"로깅 레벨: {self.config.logging_level}")
		self.logger.info("지원 형식: SMI, SRT")
		self.logger.info("=" * 50)

		if (not os.path.exists(args.folder)):
			self.logger.error(f"입력 폴더가 존재하지 않습니다: {args.folder}")
			return

		subtitle_files = []
		for ext in ['.smi', '.srt']:
			subtitle_files.extend(Path(args.folder).glob(f"*{ext}"))

		if (not subtitle_files):
			self.logger.warning(f"처리할 자막 파일이 없습니다: {args.folder}")
			return

		self.logger.info(f"발견된 자막 파일 수: {len(subtitle_files)}")

		success_count = 0
		skip_count = 0
		fail_count = 0

		for file_path in subtitle_files:
			result = self._convert_file(
				str(file_path),
				self.config.output_folder
			)

			if (result is True):
				success_count += 1
			elif (result is False):
				skip_count += 1
			else:
				fail_count += 1

		self.logger.info("=" * 50)
		self.logger.info(
			f"처리 완료: 성공 {success_count}개, "
			f"건너뜀 {skip_count}개, 실패 {fail_count}개"
		)
		self.logger.info("=" * 50)


	def _convert_file(self, file_path: str, output_folder: str) -> Optional[bool]:
		"""
		자막 파일 변환 메인 함수

		Args:
			file_path: 입력 파일 경로
			output_folder: 출력 폴더 경로

		Returns:
			Optional[bool]: 변환 성공 여부 (True: 성공, False: 건너뜀, None: 실패)
		"""
		self.logger.info(f"처리 시작: {file_path}")

		file_name = Path(file_path).stem

		output_filename = SubtitleConverter.extract_output_filename(file_name)

		if (output_filename is None):
			self.logger.warning(
				f"파일명 패턴(<문자6개 이하>-<숫자5개 이하>) 불일치로 파일명 변환은 건너뜀: {file_name}"
			)
			output_filename = file_name

		try:
			with open(file_path, 'rb') as f:
				raw_content = f.read()
				content = self.convert_to_utf8(raw_content)

			if (content is None):
				self.logger.error("인코딩 변환 실패")
				return None

			file_ext = Path(file_path).suffix.lower()
			if (file_ext == '.smi'):
				self.logger.info("SMI → SRT 변환")
				subtitles = SubtitleConverter.parse_smi(content)
			elif (file_ext == '.srt'):
				self.logger.info("SRT 형식 처리")
				subtitles = SubtitleConverter.parse_srt(content)
			else:
				self.logger.warning(f"지원하지 않는 형식: {file_ext}")
				return False

			subtitles = self.insert_blank_subtitles(subtitles)

			srt_content = SubtitleConverter.generate_srt(subtitles)

			Path(output_folder).mkdir(parents=True, exist_ok=True)

			output_path = os.path.join(output_folder, f"{output_filename}.srt")

			with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
				f.write(srt_content)

			self._backup_file(output_path, f"{output_filename}.srt")

			self.logger.info(f"처리 완료: {output_path}")
			self.logger.info(f"총 자막 줄 수: {len(subtitles)}")
			return True

		except Exception as e:
			self.logger.error(f"처리 중 오류 발생: {e}", exc_info=True)
			return None


	def convert_to_utf8(self, raw_content: bytes) -> str:
		"""
		UTF-8로 인코딩 변환

		Args:
			raw_content (bytes): 파일로부터 읽어들인 원시 binary 내용

		Returns:
			str: utf-8로 변환된 파일 내용
		"""
		content = None
		is_utf8 = False
		try:
			try:
				content = raw_content.decode('utf-8')
				is_utf8 = True
			except UnicodeDecodeError:
				try:
					zero_char_count = 0
					for char in raw_content:
						zero_char_count += 0 if (char != 0) else 1
						if (zero_char_count > 100):
							content = raw_content.decode('utf-16')
							return content

					content = raw_content.decode('euc-kr')
					is_utf8 = False
				except Exception as e:
					self.logger.warning('"euc-kr" decoding fail!', exc_info=True)
					return None

			if (all(b < 0x80 for b in raw_content)):
				return content

			if (is_utf8):
				ko_chars = sum(0xAC00 <= ord(ch) <= 0xD7A3 for ch in content)
				if (ko_chars == 0):
					content = raw_content.decode('euc-kr')

			return content
		except Exception:
			return None


	@staticmethod
	def extract_output_filename(original_filename: str) -> Optional[str]:
		"""
		파일명에서 출력 파일명 추출

		Args:
			original_filename: 원본 파일명

		Returns:
			Optional[str]: 추출된 파일명 (실패 시 None)
		"""
		pattern = re.compile(r'^[A-Za-z]{1,6}-\d{1,5}')
		match = pattern.search(original_filename)

		if (match):
			return match.group().upper()
		return None


	@staticmethod
	def parse_smi(content: str) -> List[dict]:
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


	@staticmethod
	def parse_srt(content: str) -> List[dict]:
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
				r'(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})',
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


	def insert_blank_subtitles(self, subtitles: List[dict]) -> List[dict]:
		"""
		빈 자막 삽입

		Args:
			subtitles: 자막 리스트

		Returns:
			List[dict]: 빈 자막이 삽입된 자막 리스트
		"""
		result = []

		for i, sub in enumerate(subtitles):
			result.append(sub)

			if (i + 1 < len(subtitles)):
				gap = subtitles[i + 1]['start'] - sub['end']

				if (gap > self.gap_threshold_ms):
					blank_start = sub['end'] + 1000
					blank_end = blank_start + 2000
					result.append({
						'start': blank_start,
						'end': blank_end,
						'text': ''
					})
					self.logger.info(
						f"빈 자막 삽입: {gap/1000:.1f}초 간격 발견"
					)

		return result


	@staticmethod
	def _format_srt_time(ms: int) -> str:
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


	@staticmethod
	def generate_srt(subtitles: List[dict]) -> str:
		"""
		SRT 형식 생성

		Args:
			subtitles: 자막 리스트

		Returns:
			str: SRT 형식 문자열
		"""
		srt_content = []

		for i, sub in enumerate(subtitles, 1):
			start_time = SubtitleConverter._format_srt_time(sub['start'])
			end_time = SubtitleConverter._format_srt_time(sub['end'])

			srt_content.append(f"{i}")
			srt_content.append(f"{start_time} --> {end_time}")
			srt_content.append(sub['text'])
			srt_content.append("")

		return '\n'.join(srt_content)


	def _backup_file(self, source_path: str, filename: str) -> None:
		"""
		백업 폴더에 파일 복사

		Args:
			source_path: 원본 파일 경로
			filename: 파일명
		"""
		if (not self._backup_folders):
			return

		for backup_folder in self._backup_folders:
			try:
				Path(backup_folder).mkdir(parents=True, exist_ok=True)
				backup_path = os.path.join(backup_folder, filename)
				shutil.copy2(source_path, backup_path)
			except Exception as e:
				self.logger.error(
					f"백업 실패: {backup_folder} - {e}",
					exc_info=True
				)
		self.logger.info(f"백업 완료: {backup_path}")


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
		'--output_folder',
		type=str,
		help='변환된 파일을 저장할 폴더 경로 (기본값: 설정 파일 참조)'
	)

	parser.add_argument(
		'--blank_time_seconds',
		type=int,
		help='빈 자막을 추가할 시간 간격 (초 단위, 기본값: 설정 파일 참조)'
	)

	parser.add_argument(
		'--backup_folders',
		type=str,
		help='백업 폴더 목록 (쉼표로 구분, 기본값: 설정 파일 참조)'
	)

	return parser.parse_args()


def main():
	"""
	메인 함수
	"""
	args = parse_arguments()

	converter = SubtitleConverter()
	converter.run(args)



if (__name__ == "__main__"):
	main()