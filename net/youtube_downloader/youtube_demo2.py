# 유튜브 정보 추출 예제
from argparse import ArgumentParser
from pytube import YouTube
from pytube.helpers import safe_filename
from sqlalchemy import create_engine
from typing import Final


def make_parser():
	""" YouTube Downlaoder set-up run-time argument.
	"""
	# 실행 옵션 설정
	parser = ArgumentParser(prog = 'python youtube_demo1.py', description = "YouTube Downlaoder")
	parser.add_argument("youtube_url", type = str, help = "다운로드 받길 원하는 YouTube 영상 주소(URL)를 입력해주세요.")
	parser.add_argument("-d", "--download_path", type = str, help = "영상을 다운로드 받길 원하는 경로를 입력해주세요.")
	# parser.add_argument("-h", "--help", action = 'store_false', help = "도움말을 출력합니다.")
	return parser.parse_args()


def download_youtube(target_dir, yt):
	""" 지정한 폴더로 유튜브 동영상을 다운로드 받습니다.
	"""
	pass


def insert_youtube_info(yt):
	""" 유튜브 동영상 클립 정보를 DB에 저장합니다. """
	DDB_HOST				: Final = "192.168.0.1"
	DDB_PORT				: Final = "23306"
	DDB_USER_ID				: Final = "youtubeuser"
	DDB_PASSWORD			: Final = "%40!youtube~user"
	DDB_DATABASE			: Final = "YOUTUBE_DL"

	DB_URL					: Final = f"mysql+mysqlconnector://{DDB_USER_ID}:{DDB_PASSWORD}@{DDB_HOST}:{DDB_PORT}/{DDB_DATABASE}?charset=utf8mb3&collation=utf8mb3_general_ci"

	# Database 연결을 위한 engine을 생성하여 반환합니다.
	engine = create_engine(DB_URL, encoding = 'utf-8')

	try:
		connection = engine.raw_connection()
	except Exception as e: # 데이터베이스 연결 실패
		return { 'code':500, 'message': f'database connection fail! >> {e}' }

	try:
		cursor = connection.cursor()  # get Database cursor
	except Exception as e: # Database cursor fail
		return { 'code':500, 'message': f'database cursor fail! >> {e}' }

	clip_id = "fW34INc6BCY"
	query = f"""
INSERT INTO CLIP
(
	member_no, clip_id, channel_id, author, title
	, length, publish_date, thumbnail_url, description
)
VALUES
(
	1, %s, %s, %s, %s
	, %s, %s, %s, %s
);
"""
	cursor.execute(query, (clip_id, yt.channel_id, yt.author, yt.title
			, yt.length, yt.publish_date.strftime('%Y-%m-%d'), yt.thumbnail_url, yt.description))
	connection.commit()
	connection.close()

	return None


def main(args):
	""" Main routine 
	"""
	yt = YouTube(args.youtube_url)
	stream = None
	res_str = '1080p'
	target_path = args.download_path
	if (target_path == None):
		target_path = '.'

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
		print("Not found downlaod strema (1080p, 720p)")
		return

	date_str = '1226'
	result = insert_youtube_info(yt)
	if (result != None):
		print(result)
		return

	stream.download(output_path = target_path
		, filename = f'{safe_filename(stream.title)}-{res_str}.{stream.subtype}'
		, filename_prefix = f'y{date_str} {yt.author} - ')



if __name__ == '__main__':
	args = make_parser()
	main(args)