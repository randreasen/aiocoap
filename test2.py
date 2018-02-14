import asyncio
from aiocoap import *

run = asyncio.get_event_loop().run_until_complete

# protocol = run(Context.create_client_context())
# msg = Message(code=GET, uri="coap://localhost/other/separate")
# response = run(protocol.request(msg).response)
# print(response)

async def main():
	protocol = await Context.create_client_context()
	# msg = Message(code=GET, uri="coap://localhost/other/separate")
	# response = await protocol.request(msg).response
	# print(response)

	responses = [ protocol.request(Message(code=GET, uri=u)).response \
				  for u in ("coap://localhost/time", \
							"coap://vs0.inf.ethz.ch/obs" \
							"coap://coap.me/test") ]

	for f in asyncio.as_completed(responses):
		response = await f
		print("Response from {}: {}".format(response.get_request_uri(), response.payload))


run(main())