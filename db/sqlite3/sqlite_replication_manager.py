# -*- coding: utf-8 -*-
# SqliteReplicationManager 클래스
# made : hbesthee@naver.com
# date : 2025-06-12

# Original Packages
from contextlib import contextmanager
from datetime import datetime, date
from enum import Enum
from os import listdir, makedirs, path, remove
from queue import Empty, Full, Queue
from shutil import copy2, copyfileobj
from threading import Event, local as thread_local, RLock, Thread
from time import time
from typing import Optional, Tuple, Any, Generator
from gzip import open as gzip_open

import logging
import sqlite3



# Third-party Packages



# User's Package




class RetentionPeriod(Enum):
	UNLIMITED = "unlimited"
	ONE_YEAR = "1year"
	ONE_MONTH = "1month"



class SqliteReplicationManager:
	def __init__(self, db_name: str, db_folder: str, backup_folder: str,
				retention_period: RetentionPeriod = RetentionPeriod.UNLIMITED):
		"""
		SQLite 이중화 매니저 초기화

		Args:
			db_name: 데이터베이스 이름 (확장자 제외)
			db_folder: 메인 DB 폴더 경로
			backup_folder: 백업 DB 폴더 경로
			retention_period: 데이터 보존 기간
		"""
		self._execute_queue_timeout = 15
		self._prev_check_time = time()

		self.db_name = db_name
		self.db_folder = db_folder
		self.backup_folder = backup_folder
		self.retention_period = retention_period

		# 폴더 생성
		makedirs(db_folder, exist_ok=True)
		makedirs(backup_folder, exist_ok=True)

		# 파일 경로 설정
		self.main_db_path = path.join(db_folder, f"{db_name}.db")
		current_month = datetime.now().strftime("%Y%m")
		self.backup_db_path = path.join(backup_folder, f"{db_name}-{current_month}.db")

		# 스레드 안전성을 위한 락
		self._lock = RLock()
		self._connection_lock = RLock()

		# 로깅 설정
		logging.basicConfig(level=logging.INFO)
		self.logger = logging.getLogger(__name__)

		# 백그라운드 작업을 위한 큐와 스레드
		self._execute_queue = Queue()
		self._shutdown_event = Event()
		self._worker_thread = Thread(target=self._background_worker, daemon=True)
		self._worker_thread.start()

		# 연결 관리
		self._thread_local = thread_local()

		# 초기 연결 설정
		self._initialize_connections()

		# 월별 로테이션 체크
		# self._check_monthly_rotation()


	def _background_worker(self):
		"""백그라운드 워커 스레드"""
		self.logger.info("Background worker started.")

		while (not self._shutdown_event.is_set()):
			try:
				# 큐에서 DDL 작업 가져오기 (타임아웃 1초)
				task = self._execute_queue.get(timeout=1.0)
				self._execute_ddl(task['sql'], task['parameters']) # DDL 실행
				self._execute_queue.task_done()

				# 월별 로테이션 체크
				self._check_monthly_rotation()

			except Empty:
				continue
			except Exception as e:
				self.logger.error(f"Background worker error: {e}")
				continue

		self._close_connections()
		self.logger.info("Background worker stopped.")


	def _check_monthly_rotation(self):
		"""월별 로테이션 체크 및 실행: 10초에 한번씩 수행행"""
		if (self.retention_period == RetentionPeriod.UNLIMITED):
			return

		if (self._prev_check_time < (time() - 10)):
			return

		self._prev_check_time = time()
		current_date = date.today()
		current_month = current_date.strftime("%Y%m")
		expected_backup_path = path.join(self.backup_folder, f"{self.db_name}-{current_month}.db")

		# 현재 백업 파일이 이번 달 파일이 아니면 로테이션 수행
		if (self.backup_db_path != expected_backup_path):
			self._perform_monthly_rotation(current_month)


	def _cleanup_old_backups(self):
		"""보존 기간에 따른 오래된 백업 파일 정리"""
		if self.retention_period == RetentionPeriod.UNLIMITED:
			return

		current_date = date.today()
		cutoff_months = 12 if (self.retention_period == RetentionPeriod.ONE_YEAR) else 1

		try:
			for filename in listdir(self.backup_folder):
				if (filename.startswith(f"{self.db_name}-") and filename.endswith(".db.gz")):
					# 파일명에서 날짜 추출
					date_part = filename.replace(f"{self.db_name}-", "").replace(".db.gz", "")

					try:
						file_date = datetime.strptime(date_part, "%Y%m").date()

						# 보존 기간 계산
						months_diff = (current_date.year - file_date.year) * 12 + (current_date.month - file_date.month)

						if months_diff > cutoff_months:
							file_path = path.join(self.backup_folder, filename)
							remove(file_path)
							self.logger.info(f"Removed old backup: {filename}")

					except ValueError:
						continue

		except Exception as e:
			self.logger.error(f"Failed to cleanup old backups: {e}")


	def _close_connections(self):
		"""모든 연결 종료"""
		with self._connection_lock:
			if (hasattr(self._thread_local, 'main_conn')):
				self._thread_local.main_conn.close()
				delattr(self._thread_local, 'main_conn')

			if (hasattr(self._thread_local, 'backup_conn')):
				self._thread_local.backup_conn.close()
				delattr(self._thread_local, 'backup_conn')


	def _compress_previous_backup(self):
		"""이전 백업 파일 압축"""
		if not path.exists(self.backup_db_path):
			return

		compressed_path = f"{self.backup_db_path}.gz"

		try:
			with open(self.backup_db_path, 'rb') as f_in:
				with gzip_open(compressed_path, 'wb') as f_out:
					copyfileobj(f_in, f_out)

			self.logger.info(f"Backup compressed: {compressed_path}")

		except Exception as e:
			self.logger.error(f"Failed to compress backup: {e}")


	def __enter__(self):
		return self


	def _execute_ddl(self, sql: str, parameters: Tuple):
		"""실제 DDL 실행"""
		main_conn, backup_conn = self._get_thread_connections()

		try:
			with self._lock:
				# 메인 DB에 실행
				main_conn.execute(sql, parameters)
				main_conn.commit()

				# 백업 DB에 실행
				backup_conn.execute(sql, parameters)
				backup_conn.commit()

				self.logger.debug(f"DDL executed successfully: {sql[:50]}...")

		except Exception as e:
			self.logger.error(f"Failed to execute DDL: {e}")
			# 롤백 시도
			try:
				main_conn.rollback()
				backup_conn.rollback()
			except:
				pass
			raise


	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()


	def _get_thread_connections(self) -> Tuple[sqlite3.Connection, sqlite3.Connection]:
		"""스레드별 연결 반환"""
		if not hasattr(self._thread_local, 'main_conn'):
			self._thread_local.main_conn = sqlite3.connect(
				self.main_db_path,
				timeout=30.0
			)
			self._thread_local.main_conn.execute("PRAGMA journal_mode=WAL")
			self._thread_local.main_conn.execute("PRAGMA synchronous=NORMAL")

		if not hasattr(self._thread_local, 'backup_conn'):
			self._thread_local.backup_conn = sqlite3.connect(
				self.backup_db_path,
				timeout=30.0
			)
			self._thread_local.backup_conn.execute("PRAGMA journal_mode=WAL")
			self._thread_local.backup_conn.execute("PRAGMA synchronous=NORMAL")

		return self._thread_local.main_conn, self._thread_local.backup_conn


	def _initialize_connections(self):
		"""데이터베이스 연결 초기화"""
		with self._connection_lock:
			try:
				self._get_thread_connections()
				self._close_connections()

				self.logger.info(f"Database connections initialized: {self.main_db_path}, {self.backup_db_path}")

			except Exception as e:
				self.logger.error(f"Failed to initialize connections: {e}")
				raise


	def _perform_monthly_rotation(self, current_month: str):
		"""월별 로테이션 수행"""
		with self._lock:
			try:
				self.logger.info("Starting monthly rotation...")

				# 기존 연결 종료
				self._close_connections()

				# 이전 달 백업 파일 압축
				self._compress_previous_backup()

				# 메인 DB 파일 삭제
				if path.exists(self.main_db_path):
					remove(self.main_db_path)

				# 이전 달 백업을 메인으로 복사
				if path.exists(self.backup_db_path):
					copy2(self.backup_db_path, self.main_db_path)

				# 새로운 백업 파일 경로 설정
				self.backup_db_path = path.join(self.backup_folder, f"{self.db_name}-{current_month}.db")

				# 연결 재초기화
				self._initialize_connections()

				# 오래된 백업 파일 정리
				self._cleanup_old_backups()

				self.logger.info("Monthly rotation completed successfully")

			except Exception as e:
				self.logger.error(f"Monthly rotation failed: {e}")
				raise


	def close(self):
		"""매니저 종료"""
		self.logger.info("Shutting down SqliteReplicationManager...")

		# 백그라운드 워커 종료
		self._shutdown_event.set()

		# 워커 스레드 종료 대기
		if self._worker_thread.is_alive():
			self._worker_thread.join(timeout=5.0)

		# 큐의 남은 작업 처리
		try:
			while not self._execute_queue.empty():
				task = self._execute_queue.get_nowait()
				self._execute_ddl(task['sql'], task['parameters'])
				self._execute_queue.task_done()
		except Empty:
			pass

		# 연결 종료
		self._close_connections()

		self.logger.info("SqliteReplicationManager shutdown completed")


	def execute(self, sql: str, parameters: Tuple = ()):
		"""
		DDL 실행 (백그라운드에서 처리)

		Args:
			sql: 실행할 SQL 문
			parameters: SQL 파라미터
		"""
		task = {
			'sql': sql,
			'parameters': parameters,
			'timestamp': datetime.now()
		}

		try:
			self._execute_queue.put(task, timeout=self._execute_queue_timeout)
			self.logger.debug(f"Queued DDL task: {sql[:50]}...")
		except Full:
			self.logger.error("Execute queue is full, task rejected")
			raise RuntimeError("Execute queue is full")


	@contextmanager
	def query(self, sql: str) -> Generator[sqlite3.Cursor, None, None]:
		"""
		DML 실행 (메인 DB에서만 조회)

		Args:
			sql: 실행할 SQL 문

		Yields:
			sqlite3.Cursor: 쿼리 결과 커서
		"""
		main_conn, _ = self._get_thread_connections()
		cursor = None

		try:
			with self._lock:
				cursor = main_conn.execute(sql)
				yield cursor

		except Exception as e:
			self.logger.error(f"Query execution failed: {e}")
			raise
		finally:
			if cursor:
				cursor.close()



# 사용 예제
if __name__ == "__main__":
	from tempfile import TemporaryDirectory
	from time import sleep

	# 기본 테이블 스키마
	table_schema = """
			CREATE TABLE IF NOT EXISTS logs (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				timestamp TEXT NOT NULL,
				level TEXT NOT NULL,
				message TEXT NOT NULL
			)
		"""

	with TemporaryDirectory() as temp_dir:
		db_folder = path.join(temp_dir, "db")
		backup_folder = path.join(temp_dir, "backup")
		makedirs(db_folder, exist_ok=True)
		makedirs(backup_folder, exist_ok=True)
		print(f'{db_folder=} / {backup_folder=}')

		# 매니저 생성
		with SqliteReplicationManager(
			db_name="test_log",
			db_folder=db_folder,
			backup_folder=backup_folder,
			retention_period=RetentionPeriod.ONE_MONTH
		) as manager:

			# 테이블 생성 (DDL)
			manager.execute(table_schema)

			# # 데이터 삽입 (DDL)
			manager.execute(
				"INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)",
				(datetime.now().isoformat(), "INFO", "Test log message")
			)

			sleep(0.1) # DDL이 적용되도록 약간의 지연 추가

			# # 데이터 조회 (DML)
			with manager.query("SELECT * FROM logs ORDER BY id DESC LIMIT 10") as cursor:
				results = cursor.fetchall()
				for row in results:
					print(row)

			pass

		print(f'=====----------=====')
