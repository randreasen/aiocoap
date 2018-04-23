import asyncio
from aiocoap import *

run = asyncio.get_event_loop().run_until_complete
result = bytearray(b'A\x02\x00\x01\x82\xb7measure\xff\x82\x19\t\xc4\x1a\x00\x01\x8b\xb4')

# protocol = run(Context.create_client_context())
# msg = Message(code=GET, uri="coap://localhost/other/separate")
# response = run(protocol.request(msg).response)
# print(response)

async def main():
	protocol = await Context.create_client_context()
	# msg = Message(code=GET, uri="coap://localhost/other/separate")
	msg = Message.decode(result, remote=None)
	response = await protocol.request(msg).response
	print(response)

run(main())