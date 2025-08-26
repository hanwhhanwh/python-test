# -*- coding: utf-8 -*-
# refresh "refresh_token" using KakaoMessage
# made : hbesthee@naver.com
# date : 2025-08-26



# Third-party Packages
import requests



# User's Package 들을 포함시키기 위한 sys.path에 프로젝트 폴더 추가하기
from os import getcwd
from sys import path as sys_path
project_folder = getcwd()
# print(f'{project_folder=}')
if (not project_folder in sys_path):
	sys_path.append(str(project_folder))


# User's Package
from lib.json_util import load_json_conf
from lib.kakao_message import KakaoMessageDef, KakaoMessageKey, KakaoMessage




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
		print(f'"reservation_monitor.conf" load fail!: {err_msg}')
		return -2

	service_key = conf.get('rest_api_key')

	# 메시지 API 인스턴스 생성
	kakaoMessage = KakaoMessage(service_key = service_key)

	# 카카오 인증코드 발급 URL 생성
	auth_url = kakaoMessage.get_url_for_generating_code()
	print(f'카카오 인증코드 발급 URL: \n\t{auth_url}\n')

	# 카카오 인증코드 발급 URL 접속 후 리다이렉트된 URL
	redirect_url = input('브라우저 리다이렉트된 URL: ')
	# url = "https://localhost:5000/?code=WP..."

	# 위 URL로 액세스 토큰 추출
	auth_code = kakaoMessage.get_code_by_redirected_url(redirect_url)
	auth_token = kakaoMessage.get_auth_token_json(auth_code)
	print(f'{auth_token=}')



if (__name__ == "__main__"):
	main()
