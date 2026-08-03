# -*- coding: utf-8 -*-
# 지정 폴더 아래의 특정 패턴 파일들을 하나의 마크다운 파일로 모으는 CLI 도구
#
#	외부 패키지 없이 표준 라이브러리만으로 구현되었으며, 대상 폴더 내에서
#	패턴에 일치하는 파일을 재귀적으로 탐색하여 하나의 마크다운 문서로
#	조립한 뒤 대상 폴더 내부에 저장합니다.
#
# made : hbesthee@naver.com
# date : 2026-08-01

# Original Packages
import argparse
import fnmatch
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final


LOGGER = logging.getLogger(__name__)


class SourceToMarkdownDef:
	"""도구 전반에서 사용하는 공통 리터럴 상수 클래스입니다.

	Attributes:
		DEFAULT_PATH (Final[str]): 대상 폴더 기본값입니다.
		DEFAULT_FILTER (Final[str]): 파일 필터 패턴 기본값입니다.
		MD_FILE_SUFFIX (Final[str]): 결과 파일명 기본 접미사입니다.
		ENCODING (Final[str]): 파일 입출력에 사용할 인코딩입니다.
		HIDDEN_PREFIX (Final[str]): 숨김 파일/폴더 판별 접두사입니다.
		TIMESTAMP_FORMAT (Final[str]): 생성 시각 표기 형식입니다.
		TIMESTAMP_FILE_FORMAT (Final[str]): 파일에 대한 생성 시각 표기 형식입니다.
		HEADING_LEVEL_TITLE (Final[str]): 문서 제목 헤딩 레벨입니다.
		HEADING_LEVEL_FILE (Final[str]): 파일 섹션 헤딩 레벨입니다.
		DEFAULT_CODE_BLOCK_LANG (Final[str]): 확장자 미매핑 시 코드 블록 언어입니다.
		EXTENSION_LANGUAGE_MAP (Final[dict[str, str]]): 확장자별 코드 블록 언어 매핑입니다.
	"""

	DEFAULT_PATH: Final[str] = "."
	DEFAULT_FILTER: Final[str] = "*.py"
	MD_FILE_SUFFIX: Final[str] = "_source.md"
	ENCODING: Final[str] = "utf-8"
	HIDDEN_PREFIX: Final[str] = "."
	TIMESTAMP_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
	TIMESTAMP_FILE_FORMAT: Final[str] = "%Y%m%d_%H%M"
	HEADING_LEVEL_TITLE: Final[str] = "#"
	HEADING_LEVEL_FILE: Final[str] = "##"
	DEFAULT_CODE_BLOCK_LANG: Final[str] = "text"
	EXTENSION_LANGUAGE_MAP: Final[dict[str, str]] = {
		".py": "python",
		".js": "javascript",
		".ts": "typescript",
		".json": "json",
		".md": "markdown",
		".yaml": "yaml",
		".yml": "yaml",
		".sh": "bash",
		".cpp": "cpp",
		".c": "c",
		".h": "c",
		".hpp": "cpp",
		".java": "java",
		".go": "go",
		".rs": "rust",
		".txt": "text",
	}



@dataclass
class CollectorConfig:
	"""파일 수집 및 마크다운 생성에 필요한 설정값을 보관하는 데이터 클래스입니다.

	Attributes:
		target_path (Path): 탐색 대상 폴더 경로입니다.
		filter_pattern (str): 파일 확장자 필터 패턴입니다.
		exclude_patterns (list[str]): 제외할 파일명 패턴 목록입니다.
		ignore_hidden (bool): 숨김 파일/폴더 제외 여부입니다.
		output_filename (str): 결과 마크다운 파일명입니다.
	"""

	target_path: Path
	filter_pattern: str
	exclude_patterns: list[str]
	ignore_hidden: bool
	output_filename: str


	@classmethod
	def from_namespace(cls, args: argparse.Namespace) -> "CollectorConfig":
		"""argparse 파싱 결과를 CollectorConfig로 변환합니다.

		Args:
			args (argparse.Namespace): 파싱된 CLI 인자입니다.

		Returns:
			CollectorConfig: 변환된 설정값입니다.
		"""
		target_path = Path(args.path)
		output_filename = args.md or f"{target_path.resolve().name}{SourceToMarkdownDef.MD_FILE_SUFFIX}"
		generated_at = datetime.now().strftime(SourceToMarkdownDef.TIMESTAMP_FILE_FORMAT)
		output_filename = f"{output_filename[:-3]}-{generated_at}{output_filename[-3:]}"
		return cls(
			target_path=target_path,
			filter_pattern=args.filter,
			exclude_patterns=list(args.exclude),
			ignore_hidden=args.ignore_hidden,
			output_filename=output_filename,
		)


	@classmethod
	def from_json(cls, json_path: Path) -> "CollectorConfig":
		"""JSON 파일로부터 설정값을 읽어 CollectorConfig로 변환합니다.

		CLI 인자보다 JSON 설정값을 우선 반영해야 하는 경우 이 메서드로 생성한
		CollectorConfig를 최종 설정값으로 사용합니다.

		Args:
			json_path (Path): 설정값이 담긴 JSON 파일 경로입니다.

		Returns:
			CollectorConfig: JSON 데이터로 구성된 설정값입니다.
		"""
		json_data = json.loads(json_path.read_text(encoding=SourceToMarkdownDef.ENCODING))
		return cls(
			target_path=Path(json_data.get("target_path", SourceToMarkdownDef.DEFAULT_PATH)),
			filter_pattern=json_data.get("filter_pattern", SourceToMarkdownDef.DEFAULT_FILTER),
			exclude_patterns=list(json_data.get("exclude_patterns", [])),
			ignore_hidden=bool(json_data.get("ignore_hidden", False)),
			output_filename=json_data.get("output_filename", ""),
		)



class HiddenPathChecker:
	"""경로가 숨김 파일 또는 숨김 폴더에 해당하는지 판별하는 클래스입니다."""

	def is_hidden(self, path: Path) -> bool:
		"""경로를 구성하는 각 요소 중 숨김 항목이 포함되어 있는지 확인합니다.

		Args:
			path (Path): 검사할 경로입니다.

		Returns:
			bool: 숨김 항목이 하나라도 포함되어 있으면 True입니다.
		"""
		for part in path.parts:
			if (part.startswith(SourceToMarkdownDef.HIDDEN_PREFIX) and part not in (".", "..")):
				return True
		return False



class PathExcluder:
	"""제외 패턴에 해당하는 파일인지 판별하는 클래스입니다."""

	def is_excluded(self, path: Path, patterns: list[str]) -> bool:
		"""파일명이 제외 패턴 목록 중 하나와 일치하는지 확인합니다.

		Args:
			path (Path): 검사할 파일 경로입니다.
			patterns (list[str]): fnmatch 형식의 제외 패턴 목록입니다.

		Returns:
			bool: 파일명이 패턴 중 하나와 일치하면 True입니다.
		"""
		for pattern in patterns:
			if (fnmatch.fnmatch(path.name, pattern)):
				return True
		return False



class FileCollector:
	"""대상 폴더에서 조건에 맞는 파일 목록을 탐색하는 클래스입니다."""

	def __init__(self, hidden_checker: HiddenPathChecker, path_excluder: PathExcluder) -> None:
		"""FileCollector를 초기화합니다.

		Args:
			hidden_checker (HiddenPathChecker): 숨김 여부 판별기입니다.
			path_excluder (PathExcluder): 제외 패턴 판별기입니다.
		"""
		self._hidden_checker = hidden_checker
		self._path_excluder = path_excluder


	def collect(self, config: CollectorConfig) -> list[Path]:
		"""설정값에 따라 대상 파일 목록을 정렬하여 반환합니다.

		Args:
			config (CollectorConfig): 탐색 조건이 담긴 설정값입니다.

		Returns:
			list[Path]: 조건에 맞는 파일 경로 목록(정렬됨)입니다.
		"""
		collected_files: list[Path] = []
		for file_path in config.target_path.rglob(config.filter_pattern):
			if (not file_path.is_file()):
				continue
			if (config.ignore_hidden and self._hidden_checker.is_hidden(file_path)):
				continue
			if (self._path_excluder.is_excluded(file_path, config.exclude_patterns)):
				continue
			collected_files.append(file_path)
		return sorted(collected_files)



class MarkdownContentBuilder:
	"""개별 파일을 마크다운 섹션 문자열로 변환하는 클래스입니다."""

	def build_file_section(self, file_path: Path, base_path: Path) -> str:
		"""단일 파일을 헤딩과 코드 블록으로 구성된 마크다운 섹션으로 변환합니다.

		Args:
			file_path (Path): 변환할 파일의 경로입니다.
			base_path (Path): 상대 경로 계산 기준이 되는 폴더 경로입니다.

		Returns:
			str: 헤딩과 코드 블록이 포함된 마크다운 섹션 문자열입니다.
		"""
		relative_path = file_path.relative_to(base_path)
		code_lang = self._resolve_code_lang(file_path)
		try:
			file_content = file_path.read_text(encoding=SourceToMarkdownDef.ENCODING)
		except (UnicodeDecodeError, OSError) as error:
			LOGGER.warning("Failed to read file: %s (%s)", file_path, error)
			file_content = f"[읽기 실패: {error}]"
		section_lines = [
			f"{SourceToMarkdownDef.HEADING_LEVEL_FILE} {relative_path}",
			"",
			f"```{code_lang}",
			file_content,
			"```",
			"",
		]
		return "\n".join(section_lines)


	def _resolve_code_lang(self, file_path: Path) -> str:
		"""파일 확장자에 대응하는 코드 블록 언어 태그를 반환합니다.

		Args:
			file_path (Path): 언어를 판별할 파일 경로입니다.

		Returns:
			str: 코드 블록에 사용할 언어 태그입니다.
		"""
		return SourceToMarkdownDef.EXTENSION_LANGUAGE_MAP.get(
			file_path.suffix.lower(), SourceToMarkdownDef.DEFAULT_CODE_BLOCK_LANG
		)



class MarkdownDocumentBuilder:
	"""전체 마크다운 문서를 조립하는 클래스입니다."""

	def __init__(self, content_builder: MarkdownContentBuilder) -> None:
		"""MarkdownDocumentBuilder를 초기화합니다.

		Args:
			content_builder (MarkdownContentBuilder): 파일별 섹션 생성기입니다.
		"""
		self._content_builder = content_builder


	def build_document(self, config: CollectorConfig, files: list[Path]) -> str:
		"""헤더와 각 파일 섹션을 결합하여 전체 마크다운 문서를 생성합니다.

		Args:
			config (CollectorConfig): 문서 생성에 사용할 설정값입니다.
			files (list[Path]): 문서에 포함할 파일 경로 목록입니다.

		Returns:
			str: 완성된 마크다운 문서 문자열입니다.
		"""
		document_parts = [self._build_header(config, len(files))]
		for file_path in files:
			document_parts.append(self._content_builder.build_file_section(file_path, config.target_path))
		return "\n".join(document_parts)


	def _build_header(self, config: CollectorConfig, file_count: int) -> str:
		"""문서 최상단에 위치할 제목과 생성 정보를 작성합니다.

		Args:
			config (CollectorConfig): 대상 폴더 정보가 담긴 설정값입니다.
			file_count (int): 수집된 파일 개수입니다.

		Returns:
			str: 헤더 마크다운 문자열입니다.
		"""
		generated_at = datetime.now().strftime(SourceToMarkdownDef.TIMESTAMP_FORMAT)
		header_lines = [
			f"{SourceToMarkdownDef.HEADING_LEVEL_TITLE} {config.target_path.resolve().name} 소스 코드 모음",
			"",
			f"- 생성 시각: {generated_at}",
			f"- 대상 경로: {config.target_path.resolve()}",
			f"- 파일 개수: {file_count}",
			"",
		]
		return "\n".join(header_lines)



class MarkdownFileWriter:
	"""마크다운 문서를 파일로 저장하는 클래스입니다."""

	def write(self, content: str, output_path: Path) -> None:
		"""마크다운 문자열을 UTF-8 인코딩으로 파일에 저장합니다.

		Args:
			content (str): 저장할 마크다운 문자열입니다.
			output_path (Path): 저장 대상 파일 경로입니다.

		Returns:
			None: 반환값이 없습니다.
		"""
		output_path.write_text(content, encoding=SourceToMarkdownDef.ENCODING)
		LOGGER.info("Markdown file saved: %s", output_path)



class CliArgumentParser:
	"""명령행 인자를 정의하고 파싱하여 설정값으로 변환하는 클래스입니다."""

	def build_parser(self) -> argparse.ArgumentParser:
		"""CLI 인자 파서를 구성합니다.

		Returns:
			argparse.ArgumentParser: 구성이 완료된 인자 파서입니다.
		"""
		parser = argparse.ArgumentParser(
			description="지정 폴더 아래의 지정 패턴 파일들을 하나의 마크다운 파일로 모읍니다."
		)
		parser.add_argument(
			"-p", "--path", default=SourceToMarkdownDef.DEFAULT_PATH, help="파일 목록 경로 (기본값: 현재 폴더)"
		)
		parser.add_argument(
			"-f", "--filter", default=SourceToMarkdownDef.DEFAULT_FILTER, help="파일 확장자 필터 (기본값: *.py)"
		)
		parser.add_argument(
			"-m", "--md", default=None, help="마크다운 파일명 (기본값: <폴더 이름>_source.md)"
		)
		parser.add_argument(
			"--exclude", nargs="*", default=[], help="제외할 파일명 패턴 목록 (예: *.pyc __pycache__)"
		)
		parser.add_argument(
			"--ignore-hidden", action="store_true", help="숨김 파일/폴더 제외 여부"
		)
		return parser


	def parse(self, argv: list[str] | None = None) -> CollectorConfig:
		"""CLI 인자를 파싱하여 CollectorConfig로 변환합니다.

		Args:
			argv (list[str] | None): 파싱할 인자 목록입니다. None이면 sys.argv를 사용합니다.

		Returns:
			CollectorConfig: 파싱 결과가 반영된 설정값입니다.
		"""
		parser = self.build_parser()
		args = parser.parse_args(argv)
		return CollectorConfig.from_namespace(args)



class SourceMarkdownExporter:
	"""전체 처리 흐름을 조율하는 오케스트레이터 클래스입니다."""

	def __init__(self, config: CollectorConfig) -> None:
		"""SourceMarkdownExporter를 초기화합니다.

		Args:
			config (CollectorConfig): 실행에 사용할 설정값입니다.
		"""
		self._config = config
		self._file_collector = FileCollector(HiddenPathChecker(), PathExcluder())
		self._document_builder = MarkdownDocumentBuilder(MarkdownContentBuilder())
		self._file_writer = MarkdownFileWriter()


	def run(self) -> Path:
		"""파일 탐색부터 마크다운 저장까지 전체 과정을 실행합니다.

		결과 파일은 대상 폴더(target_path) 내부에 저장됩니다.

		Returns:
			Path: 생성된 마크다운 파일의 경로입니다.
		"""
		self._validate_target_path()
		LOGGER.info("Start collecting files under: %s", self._config.target_path)
		collected_files = self._file_collector.collect(self._config)
		LOGGER.info("Collected %d file(s)", len(collected_files))
		document_content = self._document_builder.build_document(self._config, collected_files)
		output_path = self._config.target_path / self._config.output_filename
		self._file_writer.write(document_content, output_path)
		return output_path


	def _validate_target_path(self) -> None:
		"""대상 경로의 존재 여부와 디렉터리 여부를 검증합니다.

		Raises:
			FileNotFoundError: 대상 경로가 존재하지 않는 경우 발생합니다.
			NotADirectoryError: 대상 경로가 디렉터리가 아닌 경우 발생합니다.
		"""
		if (not self._config.target_path.exists()):
			raise FileNotFoundError(f"Target path does not exist: {self._config.target_path}")
		if (not self._config.target_path.is_dir()):
			raise NotADirectoryError(f"Target path is not a directory: {self._config.target_path}")



if (__name__ == "__main__"):
	logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
	config = CliArgumentParser().parse(sys.argv[1:])
	exporter = SourceMarkdownExporter(config)
	result_path = exporter.run()
	LOGGER.info("Done. Output file: %s", result_path)