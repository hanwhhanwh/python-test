# -*- coding: utf-8 -*-
# send_message using PyKakao
# made : hbesthee@naver.com
# date : 2025-06-23



# Third-party Packages
from PyKakao import Message
import requests



# User's Package
from os import getcwd
from sys import path as sys_path
sys_path.append(getcwd())

from lib.json_util import load_json_conf




def get_friends_list(access_token: str) -> list:
	headers = {"Authorization": f"Bearer {access_token}"}
	url = "https://kapi.kakao.com/v1/api/talk/friends"
	response = requests.get(url, headers=headers)
	result = response.json()
	friends_list = result.get("elements", [])
	return friends_list



def main() -> int:

	conf, err_msg = load_json_conf('conf/reservation_monitor.json')
	if (err_msg != ''):
		print(f'conf load fail!: {err_msg}')
		return -2


	rest_api_key = conf.get('rest_api_key')


	# 메시지 API 인스턴스 생성
	MSG = Message(service_key = rest_api_key)

	# 카카오 인증코드 발급 URL 생성
	auth_url = MSG.get_url_for_generating_code()
	print(f'카카오 인증코드 발급 URL: {auth_url}')

	# 카카오 인증코드 발급 URL 접속 후 리다이렉트된 URL
	url = input('리다이렉트된 URL: ')
	# url = "https://localhost:5000/?code=WP..."

	# 위 URL로 액세스 토큰 추출
	access_token = MSG.get_access_token_by_redirected_url(url)
	print(f'{access_token=}')

	# 액세스 토큰 설정
	MSG.set_access_token(access_token)

	# 1. 나에게 보내기 API - 텍스트 메시지 보내기 예시
	message_type = "text" # 메시지 유형 - 텍스트
	text = "텍스트 영역입니다. 최대 200자 표시 가능합니다." # 전송할 텍스트 메시지 내용
	link = {
		"web_url": "https://developers.kakao.com",
		"mobile_web_url": "https://developers.kakao.com",
	}
	button_title = "바로 확인" # 버튼 타이틀

	MSG.send_message_to_me(
		message_type=message_type, 
		text=text,
		link=link,
		button_title=button_title,
	)

	# 2. 친구에게 목록 확인하기
	print("친구 목록:")
	friends = get_friends_list(access_token)
	friend_index = 0
	for friend in friends:
		friend_index += 1
		print(f'  [{friend_index}] {friend["uuid"]} = {friend["profile_nickname"]}')
	print("친구 목록:", friends)


	receiver_uuid = input('Friend UUID: ')

	# 2. 친구에게 보내기 API - 텍스트 메시지 보내기 예시 (친구의 UUID 필요)
	message_type = "text" # 메시지 유형 - 텍스트
	receiver_uuids = [receiver_uuid] # 메시지 수신자 UUID 목록
	text = "텍스트 영역입니다. 최대 200자 표시 가능합니다." # 전송할 텍스트 메시지 내용
	link = {
		"web_url": "https://developers.kakao.com",
		"mobile_web_url": "https://developers.kakao.com",
	}
	button_title = "바로 확인" # 버튼 타이틀

	MSG.send_message_to_friend(
		message_type=message_type, 
		receiver_uuids=receiver_uuids,
		text=text,
		link=link,
		button_title=button_title,
	)



if (__name__ == "__main__"):
	main()
