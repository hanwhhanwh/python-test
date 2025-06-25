# -*- coding: utf-8 -*-
# send_message using PyKakao
# made : hbesthee@naver.com
# date : 2025-06-25
# 기본 출처 : PyKakao.Message 

# Original Packages
from json import dumps
from time import time
from typing import Final



# Third-party Packages
from requests import get as request_get, post as request_post




class KakaoMessageKey:
	ACCESS_TOKEN: Final				= 'access_token'
	ACCESS_TOKEN_EXPIRE: Final		= 'expires_in'
	REFRESH_TOKEN: Final			= 'refresh_token'
	REFRESH_TOKEN_EXPIRE: Final		= 'refresh_token_expires_in'
	URL_AUTH_TOKEN: Final			= 'https://kauth.kakao.com/oauth/token'
	URL_MESSAGE_ME: Final			= "https://kapi.kakao.com/v2/api/talk/memo/default/send"
	URL_MESSAGE_FRIEND :Final		= "https://kapi.kakao.com/v1/api/talk/friends/message/default/send"


class KakaoMessage:
	"""
	카카오 메시지 API 클래스

	Parameters
	----------
	service_key : str
		카카오 개발자 센터에서 발급받은 애플리케이션의 REST API 키
	"""

	def __init__(self, service_key=None, redirect_uri="https://localhost:5000", scope="talk_message"):
		self.service_key = service_key
		self.redirect_uri = redirect_uri
		self.scope = scope
		self.url_message_me = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
		self.url_message_friend = "https://kapi.kakao.com/v1/api/talk/friends/message/default/send"


	def get_url_for_generating_code(self):
		"""
		카카오 인증코드 발급 URL 생성

		Returns
		-------
		str
			카카오 인증코드 발급 URL
		"""
		url = f"https://kauth.kakao.com/oauth/authorize?client_id={self.service_key}&redirect_uri={self.redirect_uri}&response_type=code&scope={self.scope}"
		res = request_get(url).url
		return res


	def get_code_by_redirected_url(self, url):
		"""
		카카오 인증코드 추출

		Parameters
		----------
		url : str
			카카오 인증코드 발급 URL 접속 후 리다이렉트된 URL

		Returns
		-------
		str
			카카오 인증코드
		"""
		return url.split("code=")[1]


	def get_auth_token_json(self, code) -> dict:
		"""
		카카오 인증코드로 토큰 발급 결과 json 전체 정보 ; 객체 내부에 관련 정보를 저장해 놓음

		Args:
			code (str): 카카오 인증코드

		Returns: 
			dict: 토큰 발급 결과
		"""
		url = KakaoMessageKey.URL_AUTH_TOKEN
		data = {
			"grant_type": "authorization_code",
			"client_id": self.service_key,
			"redirect_uri": self.redirect_uri,
			"code": code,
		}
		response = request_post(url, data=data)
		auto_token_json = response.json()
		self.access_token = auto_token_json.get(KakaoMessageKey.ACCESS_TOKEN, '')
		self.access_token_expire_time = time() + auto_token_json.get(KakaoMessageKey.ACCESS_TOKEN_EXPIRE, 21600)
		self.refresh_token = auto_token_json.get(KakaoMessageKey.REFRESH_TOKEN, '')
		self.refresh_token_expire_time = time() + auto_token_json.get(KakaoMessageKey.REFRESH_TOKEN_EXPIRE, 5184000)
		return auto_token_json


	def get_access_token_by_code(self, code):
		"""
		카카오 인증코드로 액세스 토큰 발급

		Parameters
		----------
		code : str
			카카오 인증코드

		Returns
		-------
		str
			액세스 토큰
		"""
		auth_token = self.get_auth_token_json(code)
		return auth_token.get('access_token')


	def get_access_token_by_redirected_url(self, url):
		"""
		카카오 인증코드 발급 URL 접속 후 리다이렉트된 URL로 액세스 토큰 발급

		Parameters
		----------
		url : str
			카카오 인증코드 발급 URL 접속 후 리다이렉트된 URL

		Returns
		-------
		str
			액세스 토큰
		"""
		code = self.get_code_by_redirected_url(url)
		auth_token = self.get_auth_token_json(code)
		return auth_token.get('access_token')


	def set_access_token(self, access_token):
		"""
		액세스 토큰 설정

		Parameters
		----------
		access_token : str
			액세스 토큰
		"""
		self.headers = {
			"Authorization": f"Bearer {access_token}",
			"Content-Type": "application/x-www-form-urlencoded",
		}
		# print("액세스 토큰 설정 완료")


	def send_message_to_me(self, message_type: str, **kwargs) -> dict:
		"""나에게 보내기 API. 외부에서 Exception 처리 필요함
				try:
					json_result = kakao_msg.send_message_to_me(message_type='text', text=text)
					if (json_result.get('result_code', -1) != 0):
						print(f'send_message_to_me fail: {json_result}')
				except Excpetion as e:
					print(f'send_message_to_me error: {e}')

		Args:
			message_type (str): 메시지 유형 ('text', 'feed', 'list', 'location', 'commerce' 등)
			kwargs (dict): 메시지 유형에 따른 추가 파라미터 (text, link, button_title 등)

		Returns:
			dict: 나에게 보내기 API 응답 결과 JSON 데이터
		"""
		params = {"object_type": message_type}
		params.update(kwargs)
		data = {"template_object": dumps(params)}
		response = request_post(self.url_message_me, headers=self.headers, data=data)
		response.raise_for_status()
		json_result = response.json()
		return json_result


	def send_message_to_friend(self, message_type: str, receiver_uuids: list, **kwargs) -> dict:
		"""친구에게 보내기 API
				```python
				try:
					receiver_uuids = [friend_uuid, ...]
					json_result = kakao_msg.send_message_to_friend(message_type='text', receiver_uuids=receiver_uuids, text=text)
					if (json_result.get('result_code', -1) != 0):
						print(f'send_message_to_friend fail: {json_result}')

					# 성공한 UUID 목록 확인
					if ("successful_receiver_uuids" in json_result):
						print("메시지 전송 성공:", json_result["successful_receiver_uuids"])
					# 실패 정보 확인
					if ("failure_info" in json_result):
						print("일부 메시지 전송 실패:", json_result["failure_info"])
				except Excpetion as e:
					print(f'send_message_to_friend error: {e}')```
		---

		Args:
			message_type (str): 메시지 유형 ('text', 'feed', 'list', 'location', 'commerce' 등)
			receiver_uuids (list): 받는 사람의 고유 ID 목록
			kwargs (dict): 메시지 유형에 따른 추가 파라미터 (receiver_uuids, text, link, button_title 등)

		Returns:
			dict: 친구에게 보내기 API 응답 결과 JSON 데이터
		"""
		params = {"object_type": message_type}
		params.update(kwargs)
		data = {
			"receiver_uuids": dumps(receiver_uuids),
			"template_object": dumps(params),
			}
		response = request_post(self.url_message_friend, headers=self.headers, data=data)
		response.raise_for_status()
		json_result = response.json()
		return json_result
