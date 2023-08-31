# 유튜브 정보 추출 예제
from argparse import ArgumentParser
from pytube import YouTube


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


def main(args):
	""" Main routine 
	"""
	yt = YouTube(args.youtube_url)
	stream = None
	for st in yt.streams.filter(file_extension = 'mp4', res = '1080p'):
		if (st.includes_audio_track == True):
			stream = st
			break

	if (stream == None):
		for st in yt.streams.filter(file_extension = 'mp4', res = '720p'):
			if (st.includes_audio_track == True):
				stream = st
				break

	if (stream == None):
		print("Not found downlaod strema (1080p, 720p)")
		return

	date_str = '1226'
	stream.download(filename_prefix = f'y{date_str} - {yt.author} - ')



if __name__ == '__main__':
	args = make_parser()
	main(args)