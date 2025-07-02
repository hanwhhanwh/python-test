# -*- coding: utf-8 -*-
# asyncio.wait() example
# made : hbesthee@naver.com
# date : 2025-07-02

# Original Packages
import asyncio


async def func3():
	await asyncio.sleep(3)
	print("func3 완료")
	return "결과3"

async def func4():
	await asyncio.sleep(1)
	print("func4 완료")
	return "결과4"

async def main_wait():
	print("wait 시작 (FIRST_COMPLETED)")
	task3 = asyncio.create_task(func3())
	task4 = asyncio.create_task(func4())

	done, pending = await asyncio.wait(
		[task3, task4],
		return_when=asyncio.FIRST_COMPLETED
	)

	print(f"wait 결과: done={done}, pending={pending}")

	# 완료되지 않은 태스크 취소 (예시에서처럼 직접 처리해야 함)
	for task in pending:
		task.cancel()
		try:
			await task
		except asyncio.CancelledError:
			print(f"{task.get_name()} 취소됨")

if (__name__ == "__main__"):
	asyncio.run(main_wait())
