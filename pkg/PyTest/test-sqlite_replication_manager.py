# -*- coding: utf-8 -*-
# SqliteReplicationManager 클래스 단위 시험
# made : hbesthee@naver.com
# date : 2025-06-17

# Original Packages
from datetime import datetime, date
from shutil import rmtree
from time import sleep, time
from typing import Final
from unittest.mock import patch, MagicMock

import concurrent.futures
import gzip
import logging
import os
import sqlite3
import tempfile
import threading



# Third-party Packages
import pytest



# User's Package 들을 포함시키기 위한 sys.path에 프로젝트 폴더 추가하기
from pathlib import Path
from sys import path as sys_path
project_folder = str(Path(__file__).parent.parent.parent)
print(f'{project_folder=}')
if (not project_folder in sys_path):
	sys_path.append(str(project_folder))


# User's Package
from lib.sqlite_replication_manager import RetentionPeriod, SqliteReplicationManager



TIME_WAIT_BACKGROUND_WORKING: Final				= 0.1 # 백그라운드 작업이 수행될 때까지 대기하는 시간



class TestSqliteReplicationManager:

	@pytest.fixture
	def temp_dirs(self):
		"""임시 디렉토리 생성"""
		temp_dir = tempfile.mkdtemp()
		db_folder = os.path.join(temp_dir, "db")
		backup_folder = os.path.join(temp_dir, "backup")

		yield db_folder, backup_folder

		# 임시 폴더 정리
		try:
			rmtree(temp_dir)
		except Exception as e:
			print(f'{self.__class__.__name__}: rmtree fail: {e}')


	@pytest.fixture
	def manager(self, temp_dirs):
		"""기본 매니저 인스턴스"""
		db_folder, backup_folder = temp_dirs
		manager = SqliteReplicationManager(
			db_name="test_db",
			db_folder=db_folder,
			backup_folder=backup_folder,
			retention_period=RetentionPeriod.ONE_MONTH
		)
		yield manager

		manager.close()


	def test_initialization(self, temp_dirs):
		"""초기화 테스트"""
		db_folder, backup_folder = temp_dirs

		with SqliteReplicationManager(
			db_name="test_init",
			db_folder=db_folder,
			backup_folder=backup_folder
		) as manager:
			# 폴더 생성 확인
			assert os.path.exists(db_folder)
			assert os.path.exists(backup_folder)

			# DB 파일 생성 확인
			assert os.path.exists(manager.main_db_path)
			assert os.path.exists(manager.backup_db_path)

			# 백업 파일명 형식 확인
			current_month = datetime.now().strftime("%Y%m")
			expected_backup = f"test_init-{current_month}.db"
			assert expected_backup in manager.backup_db_path


	def test_execute_ddl(self, manager):
		"""DDL 실행 테스트"""
		# 테이블 생성
		create_sql = """
			CREATE TABLE IF NOT EXISTS test_table (
				id INTEGER PRIMARY KEY,
				name TEXT NOT NULL,
				created_at TEXT DEFAULT CURRENT_TIMESTAMP
			)
		"""
		manager.execute(create_sql)

		# 백그라운드 작업 완료 대기
		sleep(TIME_WAIT_BACKGROUND_WORKING)

		# 메인 DB에서 테이블 존재 확인
		with manager.query("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'") as cursor:
			result = cursor.fetchone()
			assert result is not None
			assert result[0] == 'test_table'

		# 백업 DB에서도 테이블 존재 확인
		backup_conn = sqlite3.connect(manager.backup_db_path)
		cursor = backup_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
		result = cursor.fetchone()
		backup_conn.close()

		assert result is not None
		assert result[0] == 'test_table'


	def test_execute_with_parameters(self, manager):
		"""파라미터가 있는 DDL 실행 테스트"""
		# 테이블 생성
		manager.execute("""
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY,
				username TEXT UNIQUE,
				email TEXT
			)
		""")

		# 데이터 삽입
		manager.execute(
			"INSERT INTO users (username, email) VALUES (?, ?)",
			("testuser", "test@example.com")
		)

		sleep(TIME_WAIT_BACKGROUND_WORKING)

		# 데이터 확인
		with manager.query("SELECT username, email FROM users WHERE username = 'testuser'") as cursor:
			result = cursor.fetchone()
			assert result is not None
			assert result[0] == "testuser"
			assert result[1] == "test@example.com"


	def test_query_context_manager(self, manager):
		"""쿼리 컨텍스트 매니저 테스트"""
		# 테스트 데이터 준비
		manager.execute("""
			CREATE TABLE IF NOT EXISTS products (
				id INTEGER PRIMARY KEY,
				name TEXT,
				price REAL
			)
		""")

		manager.execute("INSERT INTO products (name, price) VALUES (?, ?)", ("Product1", 10.99))
		manager.execute("INSERT INTO products (name, price) VALUES (?, ?)", ("Product2", 20.99))

		sleep(TIME_WAIT_BACKGROUND_WORKING)

		# 컨텍스트 매니저로 쿼리 실행
		with manager.query("SELECT COUNT(*) FROM products") as cursor:
			count = cursor.fetchone()[0]
			assert count == 2

		# 여러 결과 조회
		with manager.query("SELECT name, price FROM products ORDER BY price") as cursor:
			results = cursor.fetchall()
			assert len(results) == 2
			assert results[0][0] == "Product1"
			assert results[1][0] == "Product2"


	def test_concurrent_execute(self, manager):
		"""동시 실행 테스트"""
		# 테이블 생성
		manager.execute("""
			CREATE TABLE IF NOT EXISTS concurrent_test (
				id INTEGER PRIMARY KEY,
				thread_id TEXT,
				value INTEGER
			)
		""")

		sleep(TIME_WAIT_BACKGROUND_WORKING)

		def insert_data(thread_id, start_value):
			for i in range(10):
				manager.execute(
					"INSERT INTO concurrent_test (thread_id, value) VALUES (?, ?)",
					(f"thread_{thread_id}", start_value + i)
				)

		# 여러 스레드에서 동시 실행
		threads = []
		for i in range(5):
			thread = threading.Thread(target=insert_data, args=(i, i * 10))
			threads.append(thread)
			thread.start()

		for thread in threads:
			thread.join()

		sleep(5)  # 모든 백그라운드 작업 완료 대기

		# 결과 확인
		with manager.query("SELECT COUNT(*) FROM concurrent_test") as cursor:
			count = cursor.fetchone()[0]
			assert count == 50  # 5 threads * 10 inserts each


	def test_concurrent_query(self, manager):
		"""동시 쿼리 테스트"""
		# 테스트 데이터 준비
		manager.execute("""
			CREATE TABLE IF NOT EXISTS query_test (
				id INTEGER PRIMARY KEY,
				data TEXT
			)
		""")

		for i in range(100):
			manager.execute("INSERT INTO query_test (data) VALUES (?)", (f"data_{i}",))

		sleep(2)

		def query_data():
			results = []
			with manager.query("SELECT COUNT(*) FROM query_test") as cursor:
				count = cursor.fetchone()[0]
				results.append(count)

			with manager.query("SELECT data FROM query_test LIMIT 5") as cursor:
				data = cursor.fetchall()
				results.extend([row[0] for row in data])

			return results

		# 동시 쿼리 실행
		with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
			futures = [executor.submit(query_data) for _ in range(10)]
			results = [future.result() for future in concurrent.futures.as_completed(futures)]

		# 모든 결과가 동일해야 함
		for result in results:
			assert result[0] == 100  # count
			assert len(result) == 6  # count + 5 data items


	def test_retention_unlimited(self, temp_dirs):
		"""무제한 보존 테스트"""
		db_folder, backup_folder = temp_dirs

		with SqliteReplicationManager(
			db_name="unlimited_test",
			db_folder=db_folder,
			backup_folder=backup_folder,
			retention_period=RetentionPeriod.UNLIMITED
		) as manager:
			# 월별 로테이션이 실행되지 않아야 함
			original_backup_path = manager.backup_db_path
			manager._check_monthly_rotation()
			assert manager.backup_db_path == original_backup_path


	def test_monthly_rotation(self, temp_dirs):
		"""월별 로테이션 테스트"""
		db_folder, backup_folder = temp_dirs

		# 현재 날짜를 2025년 5월로 설정
		test_date = date(2025, 5, 1)

		class FakeDate(date):
			@classmethod
			def today(cls):
				return test_date

		table_schema = """
					CREATE TABLE IF NOT EXISTS ROTATION_DATA (
						id INTEGER PRIMARY KEY,
						data TEXT
					)
				"""

		current_time = 10 # time() - 100
		times = [current_time, current_time + 15, current_time + 30, current_time + 45, current_time + 60]
		with patch(f'lib.sqlite_replication_manager.date', FakeDate), patch(f'lib.sqlite_replication_manager.time', side_effect = times):

			with SqliteReplicationManager(
				db_name='rotation_test',
				db_folder=db_folder,
				backup_folder=backup_folder,
				retention_period=RetentionPeriod.ONE_MONTH,
				table_schema=table_schema
			) as manager:
				# 테스트 데이터 추가
				manager.execute('INSERT INTO ROTATION_DATA (data) VALUES (?)', ('test_data',))

				sleep(TIME_WAIT_BACKGROUND_WORKING)

				# 현재 날짜를 2025년 6월로 설정
				test_date = date(2025, 6, 1)

				sleep(2) # Rotation 될 때까지 대기

				manager.execute('INSERT INTO ROTATION_DATA (data) VALUES (?)', ('test_data2',))
				sleep(TIME_WAIT_BACKGROUND_WORKING)

				data_count = 0
				# # 데이터 조회 (DML)
				with manager.query("SELECT * FROM ROTATION_DATA ORDER BY id DESC LIMIT 10") as cursor:
					results = cursor.fetchall()
					for row in results:
						print(row)
						data_count += 1
				assert data_count == 2 # 최종적으로 데이터는 2개

				# TODO: 대량 데이터 조회를 넣어서 조회 이후에 로테이션이 정상적으로 수행되는지 확인하는 시험 필요

				backup_db_path = os.path.join(backup_folder, f'rotation_test-202506.db')
				assert os.path.exists(backup_db_path) # 새로운 백업 파일

				# 백업 DB에는 데이터가 1개뿐인지 확인
				data_count = 0
				backup_conn = sqlite3.connect(backup_db_path, timeout=30.0)
				backup_conn.execute("PRAGMA journal_mode=WAL")
				backup_conn.execute("PRAGMA synchronous=NORMAL")
				cursor = backup_conn.execute("SELECT * FROM ROTATION_DATA ORDER BY id DESC LIMIT 10")
				results = cursor.fetchall()
				for row in results:
					data_count += 1
					print(row)
				cursor.close()
				backup_conn.close()

				assert data_count == 1 # 백업 DB는 새로 생성되어 데이터는 1개


	def test_backup_compression(self, temp_dirs):
		"""백업 압축 테스트"""
		db_folder, backup_folder = temp_dirs

		with SqliteReplicationManager(
			db_name="compress_test",
			db_folder=db_folder,
			backup_folder=backup_folder
		) as manager:
			# 가짜 백업 파일 생성
			test_backup_path = os.path.join(backup_folder, "compress_test-202401.db")
			test_content = "This is test backup content"

			with open(test_backup_path, 'w') as f:
				f.write(test_content)

			# 백업 파일 경로 설정
			manager.backup_db_path = test_backup_path

			# 압축 실행
			manager._compress_previous_backup()

			# 압축 파일 존재 확인
			compressed_path = f"{test_backup_path}.gz"
			assert os.path.exists(compressed_path)

			# 압축 파일 내용 확인
			with gzip.open(compressed_path, 'rt') as f:
				decompressed_content = f.read()
				assert decompressed_content == test_content


	def test_cleanup_old_backups(self, temp_dirs):
		"""오래된 백업 정리 테스트"""
		db_folder, backup_folder = temp_dirs

		with SqliteReplicationManager(
			db_name="cleanup_test",
			db_folder=db_folder,
			backup_folder=backup_folder,
			retention_period=RetentionPeriod.ONE_MONTH
		) as manager:
			# 현재 날짜를 2025년 4월로 설정
			test_date = date(2025, 4, 1)

			# 오래된 백업 파일들 생성
			old_files = [
				"cleanup_test-202405.db.gz",  # 1년 전
				"cleanup_test-202501.db.gz",  # 3개월 전
				"cleanup_test-202502.db.gz",  # 2개월 전
				"cleanup_test-202503.db.gz",  # 1개월 전
			]

			for filename in old_files:
				filepath = os.path.join(backup_folder, filename)
				with gzip.open(filepath, 'wt') as f:
					f.write("test backup data")

			class FakeDate(date):
				@classmethod
				def today(cls):
					return test_date

			with patch('lib.sqlite_replication_manager.date', FakeDate):
				manager._cleanup_old_backups()

			# 1개월 이상 된 파일들이 삭제되었는지 확인
			remaining_files = os.listdir(backup_folder)

			# 2개월 이상 된 파일들은 삭제되어야 함
			assert "cleanup_test-202405.db.gz" not in remaining_files
			assert "cleanup_test-202501.db.gz" not in remaining_files
			assert "cleanup_test-202502.db.gz" not in remaining_files

			# 1개월 된 파일은 남아있어야 함 (경계값)
			assert "cleanup_test-202503.db.gz" in remaining_files


	def test_error_handling(self, manager):
		"""에러 처리 테스트"""
		# 잘못된 SQL 실행
		manager.execute("INVALID SQL STATEMENT")
		sleep(TIME_WAIT_BACKGROUND_WORKING)

		# 매니저가 여전히 작동하는지 확인
		manager.execute("""
			CREATE TABLE IF NOT EXISTS error_test (
				id INTEGER PRIMARY KEY,
				data TEXT
			)
		""")
		sleep(TIME_WAIT_BACKGROUND_WORKING)

		with manager.query("SELECT name FROM sqlite_master WHERE type='table' AND name='error_test'") as cursor:
			result = cursor.fetchone()
			assert result is not None


	# def test_queue_full_handling(self, manager): TODO: 큐가 가득차는 상황에 대한 모의 시험 마무리 필요
	# 	"""큐 가득찬 상황 처리 테스트"""
	# 	# 큐를 가득 채우기 위해 많은 작업 추가
	# 	original_queue = manager._execute_queue

	# 	# 작은 큐로 교체하여 테스트
	# 	import queue
	# 	manager._execute_queue = queue.Queue(maxsize=1)

	# 	try:
	# 		# 큐를 가득 채움
	# 		manager.execute("CREATE TABLE IF NOT EXISTS TEST1 (id INTEGER)")

	# 		# 큐가 가득찬 상태에서 추가 작업 시도
	# 		with pytest.raises(RuntimeError, match="Execute queue is full"):
	# 			manager.execute("CREATE TABLE IF NOT EXISTS TEST1 (id INTEGER)")
	# 			manager.execute("CREATE TABLE IF NOT EXISTS TEST2 (id INTEGER)")
	# 			manager.execute("CREATE TABLE IF NOT EXISTS TEST3 (id INTEGER)")
	# 			manager.execute("CREATE TABLE IF NOT EXISTS TEST4 (id INTEGER)")
	# 			manager.execute("CREATE TABLE IF NOT EXISTS TEST1 (id INTEGER)")
	# 			manager.execute("CREATE TABLE IF NOT EXISTS TEST2 (id INTEGER)")
	# 			manager.execute("CREATE TABLE IF NOT EXISTS TEST3 (id INTEGER)")
	# 			manager.execute("CREATE TABLE IF NOT EXISTS TEST4 (id INTEGER)")

	# 	finally:
	# 		# 원래 큐로 복원
	# 		manager._execute_queue = original_queue
	# 		pass


	def test_connection_recovery(self, manager):
		"""연결 복구 테스트"""
		# 정상 작업 확인
		manager.execute("""
			CREATE TABLE IF NOT EXISTS RECOVERY_TEST (
				id INTEGER PRIMARY KEY,
				data TEXT
			)
		""")
		sleep(TIME_WAIT_BACKGROUND_WORKING)

		# 연결 강제 종료
		manager._close_connections()

		# 재 연결 처리
		manager._initialize_connections()

		# 새로운 작업이 연결을 복구하고 정상 작동하는지 확인
		manager.execute("INSERT INTO RECOVERY_TEST (data) VALUES (?)", ("recovery_data",))
		sleep(TIME_WAIT_BACKGROUND_WORKING)

		with manager.query("SELECT data FROM RECOVERY_TEST WHERE data = 'recovery_data'") as cursor:
			result = cursor.fetchone()
			assert result is not None
			assert result[0] == "recovery_data"


	def test_context_manager_usage(self, temp_dirs):
		"""컨텍스트 매니저 사용 테스트"""
		db_folder, backup_folder = temp_dirs

		# with 문으로 사용
		with SqliteReplicationManager(
			db_name="context_test",
			db_folder=db_folder,
			backup_folder=backup_folder
		) as manager:
			manager.execute("""
				CREATE TABLE IF NOT EXISTS context_table (
					id INTEGER PRIMARY KEY,
					name TEXT
				)
			""")
			manager.execute("INSERT INTO context_table (name) VALUES (?)", ("test_name",))
			sleep(TIME_WAIT_BACKGROUND_WORKING)

			with manager.query("SELECT COUNT(*) FROM context_table") as cursor:
				count = cursor.fetchone()[0]
				assert count == 1

		# 컨텍스트 종료 후 파일이 여전히 존재하는지 확인
		main_db_path = os.path.join(db_folder, "context_test.db")
		assert os.path.exists(main_db_path)


	def test_thread_safety_stress(self, manager):
		"""스레드 안전성 스트레스 테스트"""
		# 테이블 생성
		manager.execute("""
			CREATE TABLE IF NOT EXISTS stress_test (
				id INTEGER PRIMARY KEY,
				thread_id INTEGER,
				operation_id INTEGER,
				timestamp TEXT
			)
		""")
		sleep(TIME_WAIT_BACKGROUND_WORKING)

		def stress_worker(thread_id, operations_count):
			for op_id in range(operations_count):
				# DDL 작업
				manager.execute(
					"INSERT INTO stress_test (thread_id, operation_id, timestamp) VALUES (?, ?, ?)",
					(thread_id, op_id, datetime.now().isoformat())
				)

				# DML 작업 (매 5번째마다)
				if op_id % 5 == 0:
					with manager.query(f"SELECT COUNT(*) FROM stress_test WHERE thread_id = {thread_id}") as cursor:
						cursor.fetchone()

		# 10개 스레드에서 각각 20개 작업 수행
		threads = []
		operations_per_thread = 20
		thread_count = 10

		for thread_id in range(thread_count):
			thread = threading.Thread(
				target=stress_worker,
				args=(thread_id, operations_per_thread)
			)
			threads.append(thread)
			thread.start()

		# 모든 스레드 완료 대기
		for thread in threads:
			thread.join()

		# 백그라운드 작업 완료 대기
		sleep(3)

		# 결과 검증
		with manager.query("SELECT COUNT(*) FROM stress_test") as cursor:
			total_count = cursor.fetchone()[0]
			expected_count = thread_count * operations_per_thread
			assert total_count == expected_count

		# 각 스레드별 작업 수 확인
		with manager.query("SELECT thread_id, COUNT(*) FROM stress_test GROUP BY thread_id ORDER BY thread_id") as cursor:
			results = cursor.fetchall()
			assert len(results) == thread_count

			for thread_id, count in results:
				assert count == operations_per_thread


	def test_large_data_handling(self, manager):
		"""대용량 데이터 처리 테스트"""
		# 테이블 생성
		manager.execute("""
			CREATE TABLE IF NOT EXISTS large_data_test (
				id INTEGER PRIMARY KEY,
				data TEXT,
				binary_data BLOB
			)
		""")
		sleep(TIME_WAIT_BACKGROUND_WORKING)

		# 큰 데이터 생성
		large_text = "x" * 10000  # 10KB 텍스트
		large_binary = b"binary_data" * 1000  # 약 11KB 바이너리

		# 대용량 데이터 삽입
		for i in range(10):
			manager.execute(
				"INSERT INTO large_data_test (data, binary_data) VALUES (?, ?)",
				(f"{large_text}_{i}", large_binary)
			)

		sleep(2)

		# 데이터 검증
		with manager.query("SELECT COUNT(*) FROM large_data_test") as cursor:
			count = cursor.fetchone()[0]
			assert count == 10

		with manager.query("SELECT LENGTH(data), LENGTH(binary_data) FROM large_data_test LIMIT 1") as cursor:
			text_len, binary_len = cursor.fetchone()
			assert text_len > 10000
			assert binary_len > 10000


	def test_database_integrity(self, manager):
		"""데이터베이스 무결성 테스트"""
		# 테이블 생성 및 데이터 삽입
		manager.execute("""
			CREATE TABLE IF NOT EXISTS integrity_test (
				id INTEGER PRIMARY KEY,
				unique_value TEXT UNIQUE,
				not_null_value TEXT NOT NULL
			)
		""")

		# 정상 데이터 삽입
		manager.execute(
			"INSERT INTO integrity_test (unique_value, not_null_value) VALUES (?, ?)",
			("unique1", "not_null1")
		)

		sleep(TIME_WAIT_BACKGROUND_WORKING)

		# 제약 조건 위반 시도 (UNIQUE 제약)
		manager.execute(
			"INSERT INTO integrity_test (unique_value, not_null_value) VALUES (?, ?)",
			("unique1", "not_null2")  # 중복 값
		)

		# NOT NULL 제약 위반 시도
		manager.execute(
			"INSERT INTO integrity_test (unique_value, not_null_value) VALUES (?, ?)",
			("unique2", None)  # NULL 값
		)

		sleep(2)

		# 정상 데이터만 삽입되었는지 확인
		with manager.query("SELECT COUNT(*) FROM integrity_test") as cursor:
			count = cursor.fetchone()[0]
			# 제약 조건 위반으로 인해 첫 번째 데이터만 삽입되어야 함
			assert count == 1

		with manager.query("SELECT unique_value, not_null_value FROM integrity_test") as cursor:
			result = cursor.fetchone()
			assert result[0] == "unique1"
			assert result[1] == "not_null1"


	def test_backup_file_consistency(self, manager):
		"""백업 파일 일관성 테스트"""
		# 테스트 데이터 생성
		manager.execute("""
			CREATE TABLE IF NOT EXISTS consistency_test (
				id INTEGER PRIMARY KEY,
				value INTEGER
			)
		""")

		# 여러 데이터 삽입
		for i in range(50):
			manager.execute(
				"INSERT INTO consistency_test (value) VALUES (?)",
				(i * 2,)
			)

		sleep(2)  # 모든 작업 완료 대기

		# 메인 DB 데이터 조회
		with manager.query("SELECT COUNT(*), SUM(value) FROM consistency_test") as cursor:
			main_count, main_sum = cursor.fetchone()

		# 백업 DB 직접 조회
		backup_conn = sqlite3.connect(manager.backup_db_path)
		backup_cursor = backup_conn.execute("SELECT COUNT(*), SUM(value) FROM consistency_test")
		backup_count, backup_sum = backup_cursor.fetchone()
		backup_conn.close()

		# 메인과 백업이 동일한지 확인
		assert main_count == backup_count == 50
		assert main_sum == backup_sum


	def test_performance_benchmark(self, manager):
		"""성능 벤치마크 테스트"""
		# 테이블 생성
		manager.execute("""
			CREATE TABLE IF NOT EXISTS performance_test (
				id INTEGER PRIMARY KEY,
				data TEXT,
				number INTEGER
			)
		""")
		sleep(TIME_WAIT_BACKGROUND_WORKING)

		# 성능 측정
		start_time = time()

		# 1000개 레코드 삽입
		for i in range(1000):
			manager.execute(
				"INSERT INTO performance_test (data, number) VALUES (?, ?)",
				(f"data_{i}", i)
			)

		# 백그라운드 작업 완료 대기
		sleep(5)

		end_time = time()
		elapsed_time = end_time - start_time

		# 성능 검증 (1000개 레코드가 30초 이내에 처리되어야 함)
		assert elapsed_time < 30, f"Performance test failed: {elapsed_time} seconds"

		# 데이터 정확성 확인
		with manager.query("SELECT COUNT(*) FROM performance_test") as cursor:
			count = cursor.fetchone()[0]
			assert count == 1000

		print(f"Performance test completed: {elapsed_time:.2f} seconds for 1000 records")


	def test_shutdown_gracefully(self, temp_dirs):
		"""정상 종료 테스트"""
		db_folder, backup_folder = temp_dirs

		manager = SqliteReplicationManager(
			db_name="shutdown_test",
			db_folder=db_folder,
			backup_folder=backup_folder
		)

		# 작업 추가
		manager.execute("""
			CREATE TABLE IF NOT EXISTS shutdown_table (
				id INTEGER PRIMARY KEY,
				data TEXT
			)
		""")

		for i in range(10):
			manager.execute(
				"INSERT INTO shutdown_table (data) VALUES (?)",
				(f"data_{i}",)
			)

		# 정상 종료
		manager.close()

		# 워커 스레드가 종료되었는지 확인
		assert not manager._worker_thread.is_alive()

		# 큐가 비어있는지 확인
		assert manager._execute_queue.empty()

		# DB 파일이 존재하는지 확인
		assert os.path.exists(manager.main_db_path)
		assert os.path.exists(manager.backup_db_path)





if (__name__ == "__main__"):
	from pathlib import Path
	from os import chdir

	project_folder = Path(__file__).parent.parent
	print(f'{project_folder=}')
	chdir(project_folder)

	# 테스트 실행 예제
	pytest.main([__file__, "-v"])
