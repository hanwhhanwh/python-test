# AVDB constants
# make hbesthee@naver.com
# date 2023-10-03

from typing import Final

HEADER_USER_AGENT: Final				= "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

ERR_BS4_PARSER_FAIL: Final				= -101 # 파서 생성 실패
ERR_BS4_ELM_NOT_FOUND: Final			= -102 # 해당 요소를 찾지 못함
ERR_HEADER_LOADING: Final				= -103 # 헤더 파일을 로딩할 수 없음
ERR_HEADER_LOADING2: Final				= -104 # 헤더 파일을 로딩할 수 없음2
ERR_DOWNLOAD_FILE: Final				= -105 # 파일 다운로드 실패
ERR_FAIL_REQUEST: Final					= -106 # URL 요청 실패

ERR_DB_INTERNAL: Final					= -1001 # 내부 오류 발생 ; 상세 오류 내용은 로그 확인 필요
ERR_DB_INTEGRITY: Final					= -1002 # 중복된 데이터를 추가했을 경우 발생 ; 기존에 수집한 자료가 발견되었으므로, 프로그램 종료하기


CN_DETAIL_URL: Final					= 'detail_url'
CN_TITLE: Final							= 'title'
CN_FILM_ID: Final						= 'film_id'
CN_DATE: Final							= 'avgosu_date'
CN_FILE_SIZE: Final						= 'file_size'
CN_COVER_IMAGE_URL: Final				= 'cover_image_url'
CN_THUMBNAIL_URL: Final					= 'thumbnail_url'
CN_MAGNET_ADDR: Final					= 'magnet_addr'


CN_YAMOON_BOARD_NO: Final				= 'yamoon_board_no'
CN_UPLOADER: Final						= 'uploader'
CN_SCRIPT_NAME: Final					= 'script_name'
CN_SCRIPT_PATH: Final					= 'script_path'
CN_SCRIPT_FILE_URL: Final				= 'script_file_url'
CN_BOARD_DATE: Final					= 'board_date'



JSON_DB: Final							= 'database'

JKEY_DB_HOST: Final						= 'db_host'
JKEY_DB_PORT: Final						= 'db_port'
JKEY_DB_NAME: Final						= 'db_name'
JKEY_DB_ENCODING: Final					= 'encoding'
JKEY_USERNAME: Final					= 'username'
JKEY_PASSWORD: Final					= 'password'
JKEY_LIMIT_PAGE_COUNT: Final			= 'limit_page_count'

DEF_LIMIT_PAGE_COUNT: Final				= 10 # 자료수집할 최대 페이지 수
DEF_RETRY_COUNT: Final					= 3 # request를 다시 시도할 회수
DEF_RETRY_WAIT_TIME: Final				= 3 # request를 다시 시도하기 전 대기시간 (초)
DEF_DB_ENCODING: Final					= 'utf-8'


DEF_CONF_DATABASE: Final				= { # 데이터베이스 설정 기본값
	JKEY_DB_HOST: 'localhost'
	, JKEY_DB_PORT: '3306'
	, JKEY_DB_NAME: 'MyDB'
	, JKEY_DB_ENCODING: DEF_DB_ENCODING
	, JKEY_USERNAME: 'username'
	, JKEY_PASSWORD: 'password'
}


DEF_CONF_AVGOSU: Final					= { # 자료수집 프로그램 기본 설정값
	JSON_DB: DEF_CONF_DATABASE
	, JKEY_LIMIT_PAGE_COUNT: DEF_LIMIT_PAGE_COUNT
}
