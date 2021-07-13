# reference : https://docs.python.org/3/library/io.html#io.BytesIO
import io

b = io.BytesIO(b"abcdef")
print(b.tell()) # 0 ; 초기 값이 주어졌더라도 생성된 IO 객체의 초기 위치는 0임
view = b.getbuffer() # 복사하지 않고 버퍼의 내용에 대한 읽을 수 있고 쓸 수 있는 뷰를 반환 
print(view) # <memory at 0x0000025B10747340>
print(view.hex()) # 616263646566
print(b.getvalue()) # b'abcdef'
view[2:4] = b"56" # 실제 버퍼의 내용을 변경함
print(b.getvalue()) # b'ab56ef'
#b.write(b'23094') # 뷰가 존재하는 상태에서 버퍼에 쓰려고 하면 오류 발생 -> BufferError: Existing exports of data: object cannot be re-sized
print(b.tell()) # 0
print(b.read()) # b'ab56ef'
print(b.tell()) # 6 ; 버퍼의 데이터를 모두 읽었으므로, 위치 정보는 마지막 값을 가리킴
view = None
print(b.tell()) # 6 ; 위치 정보는 변화 없음
b.write(b'23094') # 뷰가 없어진 상태여서 쓰기가 정상 수행됨
b.write(b'23094')
print(b.getvalue()) # b'2309423094'
b.close()
#b.write(b'23094') # close된 버퍼에 쓰려고 하면 오류 발생 -> ValueError: I/O operation on closed file.

chars = bytes(10)
buf = io.StringIO()
for ch in chars:
	buf.write(f'{ch:02x} ')
result = buf.getvalue().encode()
print(result)

resutl = ''
for ch in chars:
	result = result + hex(ch)[2:4] + ' '
print(result)
