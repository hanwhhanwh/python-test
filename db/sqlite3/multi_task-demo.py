# -*- coding: utf-8 -*-
# SQLite 다중 작업 처리 예시
# made : hbesthee@naver.com
# date : 2025-06-13


# Original Packages
from datetime import datetime
from os import close as os_close, path, remove
from tempfile import mkstemp
from typing import Dict, Any

import sqlite3
import queue
import threading
import time
import random



class DatabaseWorker:
	def __init__(self, db_path: str, max_workers: int = 1):
		"""
		SQLite 백그라운드 처리를 위한 워커 클래스

		Args:
			db_path: SQLite 데이터베이스 파일 경로
			max_workers: 워커 스레드 수 (SQLite는 보통 1개 권장)
		"""
		self.db_path = db_path
		self.max_workers = max_workers
		self.task_queue = queue.Queue()
		self.workers = []
		self.running = False

		# 데이터베이스 초기화
		self._init_database()


	def _init_database(self):
		"""데이터베이스 테이블 초기화"""
		conn = sqlite3.connect(self.db_path)
		cursor = conn.cursor()

		cursor.execute('''
			CREATE TABLE IF NOT EXISTS user_logs (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER NOT NULL,
				action TEXT NOT NULL,
				timestamp TEXT NOT NULL,
				data TEXT
			)
		''')

		conn.commit()
		conn.close()


	def _worker(self):
		"""백그라운드 워커 스레드"""
		conn = sqlite3.connect(self.db_path)
		cursor = conn.cursor()

		print(f"워커 스레드 {threading.current_thread().name} 시작")

		while self.running:
			try:
				# 큐에서 작업 가져오기 (타임아웃 설정)
				task = self.task_queue.get(timeout=1)

				if task is None:  # 종료 신호
					break

				# 작업 처리
				self._process_task(cursor, task)

				# 작업 완료 표시 - 이것이 핵심!
				self.task_queue.task_done()

			except queue.Empty:
				continue
			except Exception as e:
				print(f"작업 처리 중 오류: {e}")
				# 오류가 발생해도 task_done() 호출
				self.task_queue.task_done()

		conn.close()
		print(f"워커 스레드 {threading.current_thread().name} 종료")


	def _process_task(self, cursor: sqlite3.Cursor, task: Dict[str, Any]):
		"""개별 작업 처리"""
		task_type = task.get('type')

		if task_type == 'insert_log':
			cursor.execute('''
				INSERT INTO user_logs (user_id, action, timestamp, data)
				VALUES (?, ?, ?, ?)
			''', (
				task['user_id'],
				task['action'],
				task['timestamp'],
				task.get('data', '')
			))
			cursor.connection.commit()
			print(f"로그 삽입 완료: User {task['user_id']}, Action: {task['action']}")

		elif task_type == 'batch_insert':
			cursor.executemany('''
				INSERT INTO user_logs (user_id, action, timestamp, data)
				VALUES (?, ?, ?, ?)
			''', task['records'])
			cursor.connection.commit()
			print(f"배치 삽입 완료: {len(task['records'])}개 레코드")

		# 실제 작업 시뮬레이션
		time.sleep(0.1)


	def start(self):
		"""워커 스레드들 시작"""
		if self.running:
			return

		self.running = True

		for i in range(self.max_workers):
			worker = threading.Thread(
				target=self._worker,
				name=f"DBWorker-{i+1}"
			)
			worker.daemon = True
			worker.start()
			self.workers.append(worker)

		print(f"{self.max_workers}개의 워커 스레드 시작됨")


	def stop(self, wait_for_completion=True):
		"""워커 스레드들 종료"""
		if not self.running:
			return

		if wait_for_completion:
			print("모든 작업 완료 대기 중...")
			# 모든 작업이 완료될 때까지 대기
			self.task_queue.join()

		# 종료 신호 전송
		self.running = False
		for _ in self.workers:
			self.task_queue.put(None)

		# 모든 워커 스레드 종료 대기
		for worker in self.workers:
			worker.join()

		self.workers.clear()
		print("모든 워커 스레드 종료됨")


	def add_log(self, user_id: int, action: str, data: str = None):
		"""단일 로그 추가"""
		task = {
			'type': 'insert_log',
			'user_id': user_id,
			'action': action,
			'timestamp': datetime.now().isoformat(),
			'data': data
		}
		self.task_queue.put(task)


	def add_batch_logs(self, records: list):
		"""배치 로그 추가"""
		task = {
			'type': 'batch_insert',
			'records': records
		}
		self.task_queue.put(task)


	def get_queue_size(self):
		"""현재 큐 크기 반환"""
		return self.task_queue.qsize()


# 사용 예제
def main():
	# 데이터베이스 워커 생성 및 시작
	temp_db_fd, temp_db_fn = mkstemp(suffix='.db')
	os_close(temp_db_fd)

	db_worker = DatabaseWorker(temp_db_fn)
	db_worker.start()

	try:
		# 개별 로그 추가
		print("개별 로그 추가 중...")
		for i in range(10):
			db_worker.add_log(
				user_id=random.randint(1, 100),
				action=random.choice(['login', 'logout', 'view_page', 'click_button']),
				data=f"추가 데이터 {i}"
			)

		# 배치 로그 추가
		print("배치 로그 추가 중...")
		batch_records = []
		for i in range(5):
			batch_records.append((
				random.randint(1, 100),
				'batch_action',
				datetime.now().isoformat(),
				f'배치 데이터 {i}'
			))

		db_worker.add_batch_logs(batch_records)

		# 큐 상태 모니터링
		while db_worker.get_queue_size() > 0:
			print(f"남은 작업: {db_worker.get_queue_size()}개")
			time.sleep(0.5)

		print("모든 작업 큐에 추가 완료")
		return temp_db_fn

	finally:
		# 안전한 종료
		print("데이터베이스 워커 종료 중...")
		db_worker.stop(wait_for_completion=True)
		print("프로그램 종료")


# 결과 확인 함수
def check_results(db_filename):
	"""데이터베이스 결과 확인"""
	conn = sqlite3.connect(db_filename)
	cursor = conn.cursor()

	cursor.execute('SELECT COUNT(*) FROM user_logs')
	count = cursor.fetchone()[0]
	print(f"총 {count}개의 로그가 저장됨")

	cursor.execute('SELECT * FROM user_logs ORDER BY id DESC LIMIT 5')
	recent_logs = cursor.fetchall()

	print("최근 5개 로그:")
	for log in recent_logs:
		print(f"ID: {log[0]}, User: {log[1]}, Action: {log[2]}, Time: {log[3]}")

	conn.close()



if (__name__ == "__main__"):
	temp_db_fn = main()
	check_results(temp_db_fn)
	if (path.exists(temp_db_fn)):
		remove(temp_db_fn)