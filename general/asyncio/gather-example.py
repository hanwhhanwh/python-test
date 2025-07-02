# -*- coding: utf-8 -*-
# asyncio.gather() example
# made : hbesthee@naver.com
# date : 2025-07-02

# Original Packages
import asyncio


async def func1():
	await asyncio.sleep(1)
	print("func1 완료")
	return "결과1"

async def func2():
	await asyncio.sleep(2)
	print("func2 완료")
	return "결과2"

async def main_gather():
	print("gather 시작")
	results = await asyncio.gather(
		func1(),
		func2()
	)
	print(f"gather 결과: {results}")

if (__name__ == "__main__"):
	asyncio.run(main_gather())