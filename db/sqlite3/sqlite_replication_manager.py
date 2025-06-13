# -*- coding: utf-8 -*-
# SqliteReplicationManager 클래스
# made : hbesthee@naver.com
# date : 2025-06-12

# Original Packages
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from sqlite3 import connect, Connection, Cursor, _Parameters
from typing import Optional, Union, Dict, Any, List

import gzip
import logging
import queue
import sqlite3
import shutil
import threading
import time



# Third-party Packages



# User's Package




class RetentionPolicy(Enum):
	"""데이터 보존 정책"""
	UNLIMITED = "unlimited"
	YEARLY = "yearly"
	MONTHLY = "monthly"



class SqliteReplicationManager:
	"""SQLite 데이터베이스 이중화 및 백업 관리 클래스"""

	def __init__(self,
				db_name: str,
				db_folder: str,
				backup_folder: str,
				retention_policy: Union[str, RetentionPolicy] = RetentionPolicy.MONTHLY,
				table_schema: Optional[str] = None):
		"""
		SQLite 이중화 관리자 초기화

		Args:
			db_name (str): 데이터베이스 파일명 (확장자 제외)
			db_folder (str): 메인 DB 저장 폴더 경로
			backup_folder (str): 백업 DB 저장 폴더 경로
			retention_policy (RetentionPolicy): 보존 정책 (UNLIMITED, YEARLY, MONTHLY)
			table_schema (str): 테이블 생성 SQL (None일 경우 기본 로그 테이블 사용)
		"""
		self.db_name = db_name
		self.db_folder = Path(db_folder)
		self.backup_folder = Path(backup_folder)

		# 보존 정책 설정
		if isinstance(retention_policy, str):
			self.retention_policy = RetentionPolicy(retention_policy.lower())
		else:
			self.retention_policy = retention_policy

		# 폴더 생성
		self.db_folder.mkdir(parents=True, exist_ok=True)
		self.backup_folder.mkdir(parents=True, exist_ok=True)

		# 파일 경로 설정
		self.main_db_path = self.db_folder / f"{self.db_name}.db"
		self.backup_db_path = self.backup_folder / f"{self.db_name}.db"

		# 스레드 안전성을 위한 락과 큐
		self._lock = threading.RLock()
		self._write_queue = queue.Queue()
		self._shutdown_event = threading.Event()

		# 백그라운드 작업자 스레드
		self._worker_thread = threading.Thread(target=self._worker, daemon=True)
		self._worker_thread.start()

		# 로깅 설정
		self._setup_logging()

		# 초기 데이터베이스 설정
		self._initialize_databases()

		# 로테이션 체크
		if self.retention_policy != RetentionPolicy.UNLIMITED:
			self._check_rotation()


	def _setup_logging(self):
		"""내부 로깅 설정"""
		self.logger = logging.getLogger(f"SqliteReplicationManager_{self.db_name}")
		self.logger.setLevel(logging.INFO)

		if not self.logger.handlers:
			handler = logging.StreamHandler()
			formatter = logging.Formatter(
				'%(asctime)s - %(name)s - %(levelname)s - %(message)s'
			)
			handler.setFormatter(formatter)
			self.logger.addHandler(handler)


	def _initialize_databases(self):
		"""데이터베이스 초기화"""
		try:
			# 메인 DB 초기화
			with sqlite3.connect(str(self.main_db_path)) as conn:
				conn.execute(self.table_schema)
				conn.commit()

			# 백업 DB 초기화
			with sqlite3.connect(str(self.backup_db_path)) as conn:
				conn.execute(self.table_schema)
				conn.commit()

			self.logger.info("데이터베이스 초기화 완료")

		except Exception as e:
			self.logger.error(f"데이터베이스 초기화 실패: {e}")
			raise


	def _worker(self):
		"""백그라운드 작업자 스레드"""
		while not self._shutdown_event.is_set():
			try:
				# 큐에서 작업 가져오기 (타임아웃 1초)
				task = self._write_queue.get(timeout=1.0)

				if task is None:  # 종료 신호
					break

				operation, data = task

				if operation == "insert":
					self._execute_insert(data)
				elif operation == "rotate":
					self._perform_rotation()

				self._write_queue.task_done()

			except queue.Empty:
				continue
			except Exception as e:
				self.logger.error(f"작업자 스레드 오류: {e}")


	def _execute_insert(self, data: Dict[str, Any]):
		"""실제 데이터 삽입 수행"""
		try:
			with self._lock:
				# 메인 DB에 삽입
				with sqlite3.connect(str(self.main_db_path)) as conn:
					placeholders = ', '.join(['?' for _ in data.values()])
					columns = ', '.join(data.keys())
					sql = f"INSERT INTO logs ({columns}) VALUES ({placeholders})"
					conn.execute(sql, list(data.values()))
					conn.commit()

				# 백업 DB에 삽입
				with sqlite3.connect(str(self.backup_db_path)) as conn:
					conn.execute(sql, list(data.values()))
					conn.commit()

		except Exception as e:
			self.logger.error(f"데이터 삽입 실패: {e}")


	def execute(self, sql: str, parameters: _Parameters = ..., /) -> Cursor:
		"""실제 명령을 이중화하여 수행"""
		try:
			with self._lock:
				# 메인 DB에 삽입
				with sqlite3.connect(str(self.main_db_path)) as conn:
					placeholders = ', '.join(['?' for _ in data.values()])
					columns = ', '.join(data.keys())
					sql = f"INSERT INTO logs ({columns}) VALUES ({placeholders})"
					conn.execute(sql, list(data.values()))
					conn.commit()

				# 백업 DB에 삽입
				with sqlite3.connect(str(self.backup_db_path)) as conn:
					conn.execute(sql, list(data.values()))
					conn.commit()

		except Exception as e:
			self.logger.error(f"데이터 삽입 실패: {e}")


	def query(self, sql: str, parameters: _Parameters = ..., /) -> Cursor:
		""" 조회는 메인 DB에서만 수행합니다. sqlite3.Connection.execute() 함수와 동일합니다.
			sqlite3.Connection.execute() 함수에서 발생하는 오류가 그대로 전달됩니다.
			외부에서 오류 처리가 필요합니다.
		"""
		with self._lock:
			# 메인 DB에서 조회
			with connect(str(self.main_db_path)) as conn:
				cursor = conn.execute(sql, _Parameters or ())
				return cursor.fetchall()


	def insert_log(self, level: str, message: str, data: Optional[str] = None):
		"""로그 데이터 삽입 (비동기)"""
		log_data = {
			'timestamp': datetime.now().isoformat(),
			'level': level,
			'message': message,
			'data': data or ''
		}

		# 큐에 삽입 작업 추가
		self._write_queue.put(("insert", log_data))

	def insert_data(self, **kwargs):
		"""일반 데이터 삽입 (비동기)"""
		# 큐에 삽입 작업 추가
		self._write_queue.put(("insert", kwargs))


	def query(self, sql: str, params: Optional[tuple] = None) -> List[tuple]:
		"""데이터 조회 (메인 DB에서만 조회)"""
		try:
			with sqlite3.connect(str(self.main_db_path)) as conn:
				cursor = conn.execute(sql, params or ())
				return cursor.fetchall()
		except Exception as e:
			self.logger.error(f"데이터 조회 실패: {e}")
			return []


	def query_dict(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
		"""데이터 조회 (딕셔너리 형태로 반환)"""
		try:
			with sqlite3.connect(str(self.main_db_path)) as conn:
				conn.row_factory = sqlite3.Row
				cursor = conn.execute(sql, params or ())
				return [dict(row) for row in cursor.fetchall()]
		except Exception as e:
			self.logger.error(f"데이터 조회 실패: {e}")
			return []


	def _check_rotation(self):
		"""로테이션 필요성 체크"""
		if self.retention_policy == RetentionPolicy.UNLIMITED:
			return

		now = datetime.now()

		# 매월 1일에 로테이션 수행
		if now.day == 1:
			self._write_queue.put(("rotate", None))


	def _perform_rotation(self):
		"""데이터베이스 파일 로테이션 수행"""
		try:
			with self._lock:
				now = datetime.now()
				current_month = now.strftime("%Y%m")

				# 이전 달 계산
				if now.month == 1:
					prev_month = f"{now.year - 1}12"
				else:
					prev_month = f"{now.year}{now.month - 1:02d}"

				# 파일 경로들
				current_backup = self.backup_folder / f"{self.db_name}-{current_month}.db"
				prev_backup = self.backup_folder / f"{self.db_name}-{prev_month}.db"
				prev_compressed = self.backup_folder / f"{self.db_name}-{prev_month}.db.gz"

				self.logger.info("데이터베이스 로테이션 시작")

				# 1. 메인 DB 파일 삭제
				if self.main_db_path.exists():
					self.main_db_path.unlink()
					self.logger.info("메인 DB 파일 삭제 완료")

				# 2. 이전 달 백업을 메인 DB로 복사 (존재하는 경우)
				if prev_backup.exists():
					shutil.copy2(prev_backup, self.main_db_path)
					self.logger.info("이전 달 백업을 메인 DB로 복사 완료")
				else:
					# 백업이 없으면 새로 초기화
					self._initialize_databases()

				# 3. 현재 달 백업 파일 생성
				if not current_backup.exists():
					with sqlite3.connect(str(current_backup)) as conn:
						conn.execute(self.table_schema)
						conn.commit()
					self.logger.info("현재 달 백업 파일 생성 완료")

				# 4. 이전 달 백업 압축
				if prev_backup.exists() and not prev_compressed.exists():
					self._compress_file(prev_backup, prev_compressed)
					prev_backup.unlink()  # 원본 삭제
					self.logger.info("이전 달 백업 파일 압축 완료")

				# 5. 보존 기간에 따른 오래된 파일 정리
				self._cleanup_old_files()

				self.logger.info("데이터베이스 로테이션 완료")

		except Exception as e:
			self.logger.error(f"로테이션 실패: {e}")


	def _compress_file(self, source: Path, target: Path):
		"""파일 gzip 압축"""
		with open(source, 'rb') as f_in:
			with gzip.open(target, 'wb') as f_out:
				shutil.copyfileobj(f_in, f_out)


	def _cleanup_old_files(self):
		"""보존 기간에 따른 오래된 파일 정리"""
		now = datetime.now()

		# 보존 기간 계산
		if self.retention_policy == RetentionPolicy.YEARLY:
			cutoff_date = now - timedelta(days=365)
		elif self.retention_policy == RetentionPolicy.MONTHLY:
			cutoff_date = now - timedelta(days=30)
		else:
			return

		# 백업 폴더의 압축 파일들 체크
		pattern = f"{self.db_name}-*.db.gz"
		for file_path in self.backup_folder.glob(pattern):
			try:
				# 파일명에서 날짜 추출
				date_str = file_path.stem.split('-')[-1]  # YYYYMM
				if len(date_str) == 6:
					file_date = datetime.strptime(date_str, "%Y%m")

					if file_date < cutoff_date:
						file_path.unlink()
						self.logger.info(f"오래된 백업 파일 삭제: {file_path}")

			except (ValueError, IndexError) as e:
				self.logger.warning(f"파일 날짜 파싱 실패: {file_path}, {e}")


	def force_rotation(self):
		"""강제 로테이션 수행"""
		if self.retention_policy != RetentionPolicy.UNLIMITED:
			self._write_queue.put(("rotate", None))
			self.logger.info("강제 로테이션 요청됨")


	def get_stats(self) -> Dict[str, Any]:
		"""통계 정보 반환"""
		stats = {}

		try:
			# 메인 DB 통계
			with sqlite3.connect(str(self.main_db_path)) as conn:
				cursor = conn.execute("SELECT COUNT(*) FROM logs")
				stats['main_db_records'] = cursor.fetchone()[0]

			# 백업 DB 통계
			with sqlite3.connect(str(self.backup_db_path)) as conn:
				cursor = conn.execute("SELECT COUNT(*) FROM logs")
				stats['backup_db_records'] = cursor.fetchone()[0]

			# 파일 크기 정보
			stats['main_db_size'] = self.main_db_path.stat().st_size if self.main_db_path.exists() else 0
			stats['backup_db_size'] = self.backup_db_path.stat().st_size if self.backup_db_path.exists() else 0

			# 백업 파일 수
			backup_files = list(self.backup_folder.glob(f"{self.db_name}-*.db*"))
			stats['backup_files_count'] = len(backup_files)

			# 큐 크기
			stats['queue_size'] = self._write_queue.qsize()

		except Exception as e:
			self.logger.error(f"통계 정보 수집 실패: {e}")

		return stats


	def close(self):
		"""리소스 정리 및 종료"""
		self.logger.info("SqliteReplicationManager 종료 시작")

		# 종료 신호 설정
		self._shutdown_event.set()

		# 큐의 모든 작업 완료 대기
		self._write_queue.put(None)  # 종료 신호

		try:
			self._worker_thread.join(timeout=5.0)
		except Exception as e:
			self.logger.warning(f"작업자 스레드 종료 대기 중 오류: {e}")

		self.logger.info("SqliteReplicationManager 종료 완료")


	def __enter__(self):
		return self


	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()



# 사용 예제
if __name__ == "__main__":
	from os import makedirs, path
	from tempfile import TemporaryDirectory


	# 기본 테이블 스키마
	table_schema = """
	CREATE TABLE IF NOT EXISTS logs (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
		level TEXT,
		message TEXT,
		data TEXT
	)
	"""


	with TemporaryDirectory() as temp_dir:

		# 기본 사용법
		db_folder = path.join(temp_dir, "db")
		backup_folder = path.join(temp_dir, "backup")
		makedirs(db_folder, exist_ok=True)
		makedirs(backup_folder, exist_ok=True)
		print(f'{db_folder=} / {backup_folder=}')
		with SqliteReplicationManager(
			db_name="application_log",
			db_folder=db_folder,
			backup_folder=backup_folder,
			retention_policy=RetentionPolicy.MONTHLY
		) as manager:

			# 로그 데이터 삽입
			manager.insert_log("INFO", "애플리케이션 시작", "{'version': '1.0.0'}")
			manager.insert_log("ERROR", "데이터베이스 연결 실패", "{'error_code': 500}")

			# 일반 데이터 삽입
			manager.insert_data(
				level="DEBUG",
				message="사용자 로그인",
				data="{'user_id': 'user123'}"
			)

			# 잠시 대기 (비동기 처리 완료를 위해)
			time.sleep(1)

			# 데이터 조회
			logs = manager.query("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 10")
			print("최근 로그 10개:")
			for log in logs:
				print(log)

			# 딕셔너리 형태로 조회
			recent_logs = manager.query_dict(
				"SELECT level, message, timestamp FROM logs WHERE level = ? ORDER BY timestamp DESC",
				("ERROR",)
			)
			print("\n에러 로그:")
			for log in recent_logs:
				print(f"{log['timestamp']}: {log['message']}")

			# 통계 정보
			stats = manager.get_stats()
			print(f"\n통계 정보: {stats}")

			# 강제 로테이션 테스트 (주의: 실제 환경에서는 신중히 사용)
			# manager.force_rotation()