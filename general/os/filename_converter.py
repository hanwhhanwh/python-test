# -*- coding: utf-8 -*-
# 파일명 변환 프로그램
# made : hbesthee@naver.com
# date : 2025-11-19

# Original Packages
from argparse import ArgumentParser
from pathlib import Path
from typing import Final
import re


"""
파일명 형식을 변환하는 프로그램
변환 전: <제목>[<작가명](1~<마지막화>, 완).txt
변환 후: <제목> [<작가명] (1~<마지막화>, 완).txt
"""


class FileNameConverterDef:
	"""
	FileNameConverter 클래스의 기본 정의
	"""
	PATTERN: Final[str] = r'^(.+?)\[(.+?)\](\(.*?\)\.txt)$'
	REPLACEMENT: Final[str] = r'\1 [\2] \3'



class FileNameConverter:
	"""
	파일명 변환을 수행하는 클래스
	"""

	def __init__(self, folder_path: str):
		"""
		FileNameConverter 초기화

		Args:
			folder_path (str): 변환할 파일들이 있는 폴더 경로
		"""
		self.folder_path = Path(folder_path)
		self.pattern = re.compile(FileNameConverterDef.PATTERN)


	def validate_folder(self) -> bool:
		"""
		폴더 경로 유효성 검사

		Returns:
			bool: 폴더가 존재하고 유효하면 True, 아니면 False
		"""
		if (not self.folder_path.exists()):
			print(f"오류: 폴더가 존재하지 않습니다 - {self.folder_path}")
			return False

		if (not self.folder_path.is_dir()):
			print(f"오류: 지정된 경로가 폴더가 아닙니다 - {self.folder_path}")
			return False

		return True


	def convert_filename(self, old_name: str) -> str:
		"""
		파일명을 새로운 형식으로 변환

		Args:
			old_name (str): 기존 파일명

		Returns:
			str: 변환된 파일명
		"""
		match = self.pattern.match(old_name)

		if (match):
			new_name = self.pattern.sub(FileNameConverterDef.REPLACEMENT, old_name)
			return new_name

		return old_name


	def process_files(self) -> None:
		"""
		폴더 내의 모든 파일에 대해 파일명 변환 수행

		Returns:
			None
		"""
		if (not self.validate_folder()):
			return

		txt_files = list(self.folder_path.glob("*.txt"))

		if (not txt_files):
			print(f"변환할 .txt 파일이 없습니다: {self.folder_path}")
			return

		converted_count = 0
		skipped_count = 0

		for file_path in txt_files:
			old_name = file_path.name
			new_name = self.convert_filename(old_name)

			if (old_name != new_name):
				new_path = file_path.parent / new_name

				try:
					file_path.rename(new_path)
					print(f"변환 완료: {old_name} -> {new_name}")
					converted_count += 1
				except Exception as e:
					print(f"오류 발생: {old_name} - {str(e)}")
			else:
				skipped_count += 1

		print(f"\n변환 완료: {converted_count}개 파일")
		print(f"건너뜀: {skipped_count}개 파일")


def main() -> None:
	"""
	프로그램의 메인 진입점

	Returns:
		None
	"""
	parser = ArgumentParser(description="파일명 변환 프로그램")
	parser.add_argument(
		"--folder",
		required=True,
		help="변환할 파일들이 들어 있는 폴더"
	)

	args = parser.parse_args()

	converter = FileNameConverter(args.folder)
	converter.process_files()


if (__name__ == "__main__"):
	main()