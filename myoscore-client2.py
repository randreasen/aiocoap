import asyncio

from aiocoap import *
from aiocoap import interfaces
from aiocoap import credentials
from aiocoap import oscore

import tempfile
import json
import os
import os.path

def floadncopy(filename):
	filedata = json.load(open("." + contextdir + filename))
	with open(os.path.join(contextcopy, filename), "w") as out:
		json.dump(filedata, out)

	return filedata

def copyexists(filename):
	return os.path.exists(os.path.join(contextcopy, filename))

# Setup temporary files and directories:

SEQNO = 0

contextdir = os.path.dirname("__file__") + '/myoscore-common-context/'

os.makedirs('temp-contexts', exist_ok=True)
contextcopy = tempfile.mkdtemp(prefix='context-', dir='temp-contexts')

secretdata = floadncopy("secret.json")
settingsdata = floadncopy("settings.json")

# Setup sequence numbers:

if not copyexists("sequence.json"):
	sequence = {
		"used": {(settingsdata["client-sender-id_hex"]).lower(): SEQNO},
		"seen": {(settingsdata["server-sender-id_hex"]).lower():  [-1]}
	}
	with open(os.path.join(contextcopy, "sequence.json"), "w") as out:
		json.dump(sequence, out)

# print("Temporary context with seqno {} copied to {}".format(SEQNO, contextcopy))

# Get security context:
# [wrapping in function since this is asynchronous code:]

async def main():

	secctx = oscore.FilesystemSecurityContext(contextcopy, role="client")
	msgctx = await Context.create_client_context()
	request = Message(code=GET, uri="coap://localhost/hello/coap")

	protected_msg, original_request_seqno = secctx.protect(request)
	secctx._store()

	protected_request = msgctx.request(protected_msg)
	protected_response = await protected_request.response

	unprotected_response, _ = secctx.unprotect(protected_response, original_request_seqno)
	secctx._store()

	print(unprotected_response)

asyncio.get_event_loop().run_until_complete(main())