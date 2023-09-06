# N8975A SCPI command : screenshot
# date	2023-08-22
# author	hbesthee@naver.com

from pyvisa import ResourceManager
from time import sleep


_GPIB = 8
_port = 0

rm = ResourceManager(r'C:\WINDOWS\system32\visa64.dll') # visa 객체를 생성합니다.

client = rm.open_resource(f'GPIB{_port}::{_GPIB}::INSTR') # 지정한 HOST와 PORT를 사용하여 서버에 접속합니다. 
print (client.query('*IDN?'))

client.write(f'MMEM:STOR:SCR:REV "C:\GUI.GIF"') # 화면 갈무리
sleep(25) # 계측기에서 갈무리가 완료될 때까지 대기하기

client.write(f'MMEMory:DATA? "C:\GUI.GIF"') # 갈무리한 파일을 PC로 전달
img = client.read_raw() # 갈무리 파일을 binary 형식으로 읽어오기

header_index = img.find(b'GIF')
if (header_index > 0): # found PNG header
	img = img[header_index:]

	with open('./result/screenshot/pnf.gif', 'wb') as f: # 화면 캡쳐 파일 저장하기
		f.write(img)

client.write(f'MMEM:DELete "C:\GUI.GIF"') # 갈무리했던 파일을 계측기에서 삭제
client.close()