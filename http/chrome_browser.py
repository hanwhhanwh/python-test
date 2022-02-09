import os

# os.system('chrome http://hbesthee.tistory.com')
# 오류 발생 : 'chrome'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램, 또는 배치 파일이 아닙니다.
# Chrome 실행 파일이 PATH에 등록되어 있지 않았음

# os.system('"%ProgramFiles%\Google\Chrome\Application\chrome.exe" http://hbesthee.tistory.com/')
# 오류 발생 : 'C:\Program'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램, 또는 배치 파일이 아닙니다.
# 직접적으로 환경변수를 이용하면 "Program Files" 경로 찾기 실패

# os.system('"C:\Program Files\Google\Chrome\Application\chrome.exe" http://hbesthee.tistory.com/')
# 정상 동작했으나 윈도우 설치 환경이나, 파이썬 버전에 따라서 정상적으로 동작하지 않을 수 있음

program_files = os.environ["ProgramFiles"] # 환경변수를 통하여 윈도우 버전 및 설치 환경에 관계없이 "Program Files" 경로 얻기
chrome = f'{program_files}\Google\Chrome\Application\chrome.exe' # 크롬 브라우저 실행파일 전체 경로
print(chrome)
cmd = f'"{chrome}" http://hbesthee.tistory.com/' # 크롬 브라우저 명령 문자열
print(cmd)

if (os.path.exists(chrome)):
	os.system(cmd) # 크롬 브라우저 실행
else:
	raise Exception('Not found chrome!')
