# -*- coding: utf-8 -*-
# serial_asyncio() demo1 - create_serial_connection
# made : hbesthee@naver.com
# date : 2025-10-14

# Original Packages
from asyncio import get_event_loop, get_running_loop, Protocol, run, sleep, \
					StreamReader, StreamWriter
from typing import Final



# Third-party Packages
from serial_asyncio import create_serial_connection




SERIAL_PORT: Final[str]			= 'COM8'
SERIAL_BAUDRATE: Final[str]		= 115200



class EchoProtocol(Protocol):
	def connection_made(self, transport):
		self.transport = transport
		print('Serial port opened')

	def data_received(self, data):
		print('Received:', data)
		# self.transport.write(data)  # Echo back

	def connection_lost(self, exc):
		print('Serial port closed')
		get_event_loop().stop()


async def main_serail():
	loop = get_running_loop()
	transport, protocol = await create_serial_connection(loop=loop, protocol_factory=EchoProtocol,
								url=SERIAL_PORT, baudrate=SERIAL_BAUDRATE)

	transport.write(b'hello\n')
	await sleep(0.2)


if (__name__ == "__main__"):
	run(main_serail())
