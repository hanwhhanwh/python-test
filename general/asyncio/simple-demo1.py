# -*- coding: utf-8 -*-
# 코루틴 스케줄링에 대한 이해를 돕는 간단한 예제
# made : hbesthee@naver.com
# date : 2025-09-11

"""
asyncio.create_task()로 코루틴을 생성하면, 생성과 동시에 코루틴이 실행되는가?

결론은 실행된다기 보다는 스케줄링된다.
asyncio.create_task(co) 를 호출하면 해당 코루틴이 Task 객체로 감싸져 이벤트 루프에 즉시 스케줄링됩니다.

하지만 현재 실행 중인 스레드와 무관하게 동작하지는 않습니다.
→ asyncio의 코루틴은 단일 스레드 이벤트 루프 안에서 동시 실행되며, 멀티스레딩처럼 병렬로 실행되지는 않습니다.

즉, create_task()는 코루틴을 "실행 대기 상태"로 등록하고, 이벤트 루프가 다음에 제어권을 넘길 때(await, I/O 대기 등) 실행이 시작됩니다.
"""

# Original Packages
import asyncio


async def worker(name: str, delay: int):
	"""일을 하는 코루틴"""
	print(f"{name} 시작")
	await asyncio.sleep(delay)
	print(f"{name} 완료")


async def main():
	print("메인 시작")

	# Task 생성 (스케줄링됨)
	task1 = asyncio.create_task(worker("작업1", 2))
	task2 = asyncio.create_task(worker("작업2", 1))

	print("메인: Task 생성 완료")

	# 다른 작업을 하다가
	await asyncio.sleep(0.5)
	print("메인: 0.5초 경과")

	# 두 Task가 끝나길 기다림
	await task1
	await task2

	print("메인 종료")


asyncio.run(main())
"""Results>>>
메인 시작
메인: Task 생성 완료
작업1 시작
작업2 시작
메인: 0.5초 경과
작업2 완료
작업1 완료
메인 종료
"""
