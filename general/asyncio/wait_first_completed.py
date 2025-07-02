# -*- coding: utf-8 -*-
# asyncio.wait(FIRST_COMPLETED) example
# made : hbesthee@naver.com
# date : 2025-07-02

# Original Packages
import asyncio

async def task_one():
	print("Task One: 시작")
	try:
		await asyncio.sleep(3)  # 3초 대기
		print("Task One: 완료")
		return "Task One 완료됨"
	except asyncio.CancelledError:
		print("Task One: 취소됨")
		raise

async def task_two():
	print("Task Two: 시작")
	try:
		await asyncio.sleep(5)  # 5초 대기
		print("Task Two: 완료")
		return "Task Two 완료됨"
	except asyncio.CancelledError:
		print("Task Two: 취소됨")
		raise


async def main():
	print("메인 함수: 태스크 생성 중...")
	task1 = asyncio.create_task(task_one())
	task2 = asyncio.create_task(task_two())

	# 두 태스크 중 하나라도 완료되면 반환 (FIRST_COMPLETED)
	done, pending = await asyncio.wait([task1, task2], return_when=asyncio.FIRST_COMPLETED)

	print("\n메인 함수: 하나의 태스크가 완료되었습니다.")
	print(f"완료된 태스크: {done}")
	print(f"아직 실행 중인 태스크: {pending}")

	# 완료되지 않은 태스크들 취소
	for task in pending:
		task.cancel()
		try:
			await task  # 취소될 때까지 대기
		except asyncio.CancelledError:
			print(f"메인 함수: {task.get_name()}이(가) 성공적으로 취소되었습니다.")

	print("메인 함수: 모든 태스크 처리 완료, 프로그램 종료.")

if __name__ == "__main__":
	asyncio.run(main())