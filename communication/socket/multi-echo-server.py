# reference
# 	https://webnautes.tistory.com/1381
#	https://sungmin-joo.tistory.com/57
import socket
import threading


# 접속할 서버 주소입니다. 여기에서는 루프백(loopback) 인터페이스 주소 즉 localhost를 사용합니다. 
HOST = '127.0.0.1'

# 클라이언트 접속을 대기하는 포트 번호입니다.   
PORT = 9999        

def handle_client(client_socket, addr):
	print(f"접속한 클라이언트의 주소 입니다. : {addr}")
	while True:
		client_data = False
		try:
			client_data = client_socket.recv(1024)
		except ConnectionResetError as e:
			print(f'ConnectionResetError : {e}')
			break
		if not client_data: # client에서 접속이 종료되면, client_data에 False가 할당됨
			break
		print(f"recv : {client_data.decode()}")
		string = f"ECHO : {client_data.decode()}"
		client_socket.sendall(string.encode())

	print(f"{addr} 접속이 종료됩니다.")
	client_socket.close()


# 서버 소켓 객체를 생성합니다. 
# 주소 체계(address family)로 IPv4, 소켓 타입으로 TCP 사용합니다.  
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# 포트 사용중이라 연결할 수 없다는 
# WinError 10048 에러 해결를 위해 필요합니다. 
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


# bind 함수는 소켓을 특정 네트워크 인터페이스와 포트 번호에 연결하는데 사용됩니다.
# HOST는 hostname, ip address, 빈 문자열 ""이 될 수 있습니다.
# 빈 문자열이면 모든 네트워크 인터페이스로부터의 접속을 허용합니다. 
# PORT는 1-65535 사이의 숫자를 사용할 수 있습니다.  
server_socket.bind((HOST, PORT))

# 서버가 클라이언트의 접속을 허용하도록 합니다. 
server_socket.listen()


# 무한루프를 돌면서 
while True:

	# accept 함수에서 대기하다가 클라이언트가 접속하면 새로운 소켓을 리턴합니다. 
	client_socket, addr = server_socket.accept()

	# #accept() 함수로 클라이언트의 연결만 받아 주고 이후 클라이언트의 데이터 처리는 핸들러에게 맡긴다.
	t = threading.Thread(target=handle_client, args=(client_socket, addr))
	t.daemon = True
	t.start()

server_socket.close()