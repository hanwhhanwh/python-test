# 유튜브 영상 클립 다운로더
# make hbesthee@naver.com
# date 2023-01-06

from datetime import datetime
from flask import Flask, make_response, request
from flask_cors import CORS
from json import dumps, loads
from multiprocessing import Queue
from os import makedirs, path
from pytube import YouTube
from pytube.helpers import safe_filename
from requests import get, post
from threading import Thread
from typing import Final


YOUTUBE_URL_PREFIX = 'https://www.youtube.com/watch?v='
YOUTUBE_DL_INFO_API = f'http://localhost:35000/youtube_dl'


# 멀티 프로세스 video_id 저장을 위한 큐 생성
_video_id_q = Queue()


app = Flask(__name__)
CORS(app)


def download_youtube(target_dir, yt):
	""" 지정한 폴더로 유튜브 동영상을 다운로드 받습니다.
	"""
	pass


def get_youtube_info(video_id):
	""" 유튜브 동영상 클립 정보를 API 호출을 통하여 가져옵니다. """
	youtube_clip_info_url = f'{YOUTUBE_DL_INFO_API}?video_id={video_id}'
	json_header = {'Content-Type': 'application/json'}
	res = get(youtube_clip_info_url, headers = json_header)
	youtube_clip_info = None
	try:
		youtube_clip_info = loads(res.text)
	except:
		youtube_clip_info = { 'resultCode': 501, 'resultMsg': f'API result error: not found json => {res.text}'}
	return youtube_clip_info


def insert_youtube_info(yt):
	""" 유튜브 동영상 클립 정보를 API 호출을 통하여 DB에 저장합니다. """
	youtube_clip_info_url = YOUTUBE_DL_INFO_API
	json_header = {'Content-Type': 'application/json'}
	json_data = {
			'clip_id': yt.video_id
			, 'channel_id': yt.channel_id
			, 'author': yt.author
			, 'title': yt.title
			, 'length': yt.length
			, 'publish_date': yt.publish_date.strftime('%Y-%m-%dT%H:%M')
			, 'thumbnail_url': yt.thumbnail_url
			, 'description': yt.description
		}
	data = dumps(json_data, ensure_ascii = True) # REST API 호출 시, ensure_ascii = True 설정을 해주어야 수신측에서 올바르게 수신 가능함
	res = post(youtube_clip_info_url, headers = json_header, data = data)
	result = None
	try:
		result = loads(res.text)
	except:
		result = { 'resultCode': 502, 'resultMsg': f'API POST error: not found json => {res.text}'}
	return result


def download_thread_main(download_path):
	""" download thread main routine
	"""
	print(f'"YOUTUBE_DL download thread" started.')

	video_id = None
	stream = None
	res_str = '1080p'
	if (download_path == None):
		download_path = '.'
	target_path = download_path

	_download_error_yt_list = dict()
	while (True):
		video_id =_video_id_q.get()
		clip_url = f'{YOUTUBE_URL_PREFIX}{video_id}'
		yt = YouTube(clip_url)

		try:
			for st in yt.streams.filter(file_extension = 'mp4', res = res_str):
				if (st.includes_audio_track == True):
					stream = st
					break

			if (stream == None):
				res_str = '720p'
				for st in yt.streams.filter(file_extension = 'mp4', res = res_str):
					if (st.includes_audio_track == True):
						stream = st
						break

			if (stream == None):
				print(f"{video_id}: Not found downlaod stream (1080p, 720p)")
				continue

			date_str = datetime.now().strftime('%m%d')
			target_path = f'{download_path}/y{date_str}'

			if (not path.exists(target_path)):
				makedirs(target_path)
			stream.download(output_path = target_path
				, filename = f"{safe_filename(stream.title.replace('/', '-'))}-{res_str}.{stream.subtype}"
				, filename_prefix = f"y{date_str} {yt.author} {yt.publish_date.strftime('%y%m%d')} - " )

			result = insert_youtube_info(yt)
			if (result != None):
				print(result)
				continue
			print(f'"{stream.title}" download complete.')
		except Exception as e:
			print(f'Download error ({video_id}): {e}')
			error_count = _download_error_yt_list.get(video_id)
			error_count = error_count + 1 if error_count else 1
			_download_error_yt_list[video_id] = error_count
			if (error_count < 5): # 5회까지만 재시도 처리
				_video_id_q.put(video_id) # 재시도 할 수 있도록 다시 넣기


@app.route("/youtube_dl")
def youtube_dl():
	result = None
	video_id = request.args.get('video_id')
	force_download = request.args.get('video_id') == 'y'
	if (not video_id):
		result = { "resultCode":400, "resultMsg":"Bad parameter : youtube infomation (body)" }

	# RESTful API로 다운로드 받은 이력이 있는지 확인하기
	youtube_clip_info = get_youtube_info(video_id)
	print(youtube_clip_info)
	try:
		if ((not force_download) and (youtube_clip_info.get('resultCode') == 200) ):
			result = { "resultCode":201, "resultMsg": f"Already downloaded : {video_id}" }

		if (result == None):
			_video_id_q.put(video_id)
			result = { "resultCode":200, "resultMsg": f"Success: {video_id} added." }
	except Exception as e:
		errMsg = f'API call error: {e}'
		result = {"resultCode":500, "resultMsg": errMsg }

	response = make_response(dumps(result, ensure_ascii = False))
	response.headers['Content-type'] = 'application/json; charset=utf-8'
	response.headers['Cache-Control'] = 'no-store' # 캐쉬 처리 방지

	return response


if __name__ == '__main__':

	# run Youtube download thread
	target_path = 'C:/Temp/Youtube'
	thread = Thread(target = download_thread_main, args = (target_path, ))
	thread.start()

	# run Flask web server
	app.run(host='0.0.0.0', port=80, debug=True)
