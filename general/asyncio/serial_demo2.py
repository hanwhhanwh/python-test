# -*- coding: utf-8 -*-
# serial_asyncio() demo2 - open_serial_connection
# made : hbesthee@naver.com
# date : 2025-10-14

# Original Packages
from asyncio import get_running_loop, Protocol, run, \
					CancelledError, StreamReader, StreamWriter, wait_for
from typing import Final



# Third-party Packages
from serial_asyncio import open_serial_connection



SERIAL_PORT: Final[str]			= 'COM8'
SERIAL_BAUDRATE: Final[str]		= 115200



async def main_serial():
	loop = get_running_loop()

	reader: StreamReader = None
	writer: StreamWriter = None
	reader, writer = await open_serial_connection(loop=loop,
								url=SERIAL_PORT, baudrate=SERIAL_BAUDRATE)
	while (True):
		try:
			writer.write(b'hello\n')
			data: bytes = await reader.read(1024)
			if (data is None):
				break
			print(data.decode())
		except CancelledError:
			break


if (__name__ == "__main__"):
	run(main_serial())
