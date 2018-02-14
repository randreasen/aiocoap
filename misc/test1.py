import asyncio
from aiocoap import *

run = asyncio.get_event_loop().run_until_complete

protocol = run(Context.create_client_context())
msg = Message(code=GET, uri="coap://localhost/other/separate")
response = run(protocol.request(msg).response)
print(repsonse)