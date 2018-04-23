import asyncio

from aiocoap import *
from aiocoap import interfaces
from aiocoap import credentials
from aiocoap import oscore

import tempfile
import json
import os
import os.path
import binascii

def floadncopy(filename):
	filedata = json.load(open("." + contextdir + filename))
	with open(os.path.join(contextcopy, filename), "w") as out:
		json.dump(filedata, out)

	return filedata

def copyexists(filename):
	return os.path.exists(os.path.join(contextcopy, filename))

def bytes2ascii(b):
	return binascii.hexlify(b).decode('ascii')

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


secctx = oscore.FilesystemSecurityContext(contextcopy, role="client")
request0 = Message(code=GET, uri="coap://localhost/hello/coap")

def printPayload(msg):
	print(msg.payload.hex())

def printOS(msg):
	print(msg.opt.object_security.hex())


request1 = Message(code=POST, uri='coap://localhost/hello/6', payload=b"\x4a", content_format=0)
request2 = Message(code=PUT, uri='coap://localhost/hello/7', payload=b"\x7a", content_format=0, if_match=[b"\x7b"])
request3 = Message(code=DELETE, uri='coap://localhost/test')

protected_msg0,  original_request_seqno = secctx.protect(request0)
secctx._store()
protected_msg1,  original_request_seqno = secctx.protect(request1)
secctx._store()
protected_msg2,  original_request_seqno = secctx.protect(request2)
secctx._store()
protected_msg3,  original_request_seqno = secctx.protect(request3)
secctx._store()
