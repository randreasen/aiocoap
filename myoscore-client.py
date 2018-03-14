import asyncio

from aiocoap import *
from aiocoap import interfaces
from aiocoap import credentials
from aiocoap import oscore

from plugtest_common import get_security_context
import tempfile
import json
import os
import os.path

# from plugtest_common import *
contextdir = os.path.dirname("__file__") + '/myoscore-common-context/'
TESTNO = 0

class TestSetupError(ValueError):
	"""Raised when finding a parameter not yet supported by myoscore-client"""

def my_get_security_context(role='client'):
	""" This creates a 'temporary' directory (actually the files persist,
	in the future they should be deleted after use) within the folder temp-contexts.

	Each file in this directory is a folder with the pattern:
	context-#######

	where ###### represents a random string of characters generated by the function
	mkdtemp. 

	Within each of these files is stored a copy of the secret (secret.json, containing
	the Master Secret), and the settings for the session (settings.json, containing the 
	encryption algorithm, and the client and server sender id's)

	This is the copy which is accessed and modified by each instance of client or server 
	programs. The originals are not touched.

	Returns the security context as setup by FilesystemSecurityContext in oscore.py
	"""
	print("Using TESTNO = {}".format(TESTNO))

	# For now assume client:
	if role != 'client':
		raise TestSetupError("Currently only support for client side")


	# Create temporary directory:

	os.makedirs('temp-contexts', exist_ok=True)
	contextcopy = tempfile.mkdtemp(prefix='context-', dir='temp-contexts')

	# Load and copy secret data:

	# print("Path is: {}".format("." + contextdir + 'secret.json'))
	secretdata = json.load(open("." + contextdir + 'secret.json')) # I shouldn't need to make it relative
	with open(os.path.join(contextcopy, 'secret.json'), 'w') as out:
		json.dump(secretdata, out)

	# Load and copy settings data:	

	settingsdata = json.load(open("." + contextdir + 'settings.json'))
	with open(os.path.join(contextcopy, 'settings.json'), 'w') as out:
		json.dump(settingsdata, out)

	# print("contextcopy is: {}".format(contextcopy))

	# Start sequence numbers:
	if not os.path.exists(os.path.join(contextcopy, 'sequence.json')):
		sequence = {
				 "used": {(settingsdata['client-sender-id_hex']).lower():TESTNO},
				 "seen": {(settingsdata['server-sender-id_hex']).lower():[-1]}
			}

		with open(os.path.join(contextcopy, 'sequence.json'), 'w') as out:
			json.dump(sequence, out)

	print("Temporary context with seqno %d copied to %s"%(TESTNO, contextcopy))
	secctx = oscore.FilesystemSecurityContext(contextcopy, role=role)

	return secctx

class ProtectedRequester(interfaces.RequestProvider):
	"""A RequestProvider that protectes requests using OSCORE using a
    configured mapping between URIs and security contexts and sends it over the underlying_requester."""
	def __init__(self, underlying_requester):
		self._wire = underlying_requester

		self.client_credentials = credentials.CredentialsMap() # Map is effectively empty
		# print("//////////////////////Credentials: {}".format(self.client_credentials.items()))

		import logging
		self.log = logging.getLogger('protected-requester')
		self.exchange_monitor_factory = lambda message: None

	def request(self, request_message, handle_blockwise=True, exchange_monitor_factory=lambda message:None):
	    # "handle_blockwise" means inner blockwise here

	    if handle_blockwise:
	        return protocol.BlockwiseRequest(self, request_message)
	    else:
	        # FIXME: this is not yet fully aligned with the relatively dumb
	        # credentials keeper object used for DTLS
	        security_context = self.client_credentials.credentials_from_request(request_message)

	        return self.Request(self._wire, security_context, request_message)


	class Request(interfaces.Request):
	    def __init__(self, wire, security_context, request_message):
	        if request_message.opt.observe is not None:
	            self.observation = self.Observation(request_message)
	        self._security_context = security_context

	        self.response = self._initial(wire, request_message)

	    async def _initial(self, wire, request_message):
	        protected, self._original_request_seqno = self._security_context.protect(request_message)
	        # FIXME where should this be called from?
	        self._security_context._store()

	        wire_request =  wire.request(protected)

	        # FIXME do we want to expose anything else of the request? what other
	        # interfaces are there that are applicable?

	        if request_message.opt.observe is not None:
	            wire_request.observation.register_errback(self.observation.error)
	            wire_request.observation.register_callback(self._observe_message)

	            # FIXME something is weak too aggressively here -- proper solution
	            # would probably be keeping references in callback recipients as
	            # mandatory-to-keep callback removers (ie. the handle is not only
	            # for removing one's callback again, but also to keep it alive)
	            self.observation._wire_observation = wire_request.observation

	        wire_response = await wire_request.response
	        unprotected_response, _ = self._security_context.unprotect(wire_response, self._original_request_seqno)
	        self._security_context._store()

	        return unprotected_response

	    def _observe_message(self, message):
	        unprotected_message, _ = self._security_context.unprotect(message, self._original_request_seqno)
	        self._security_context._store()
	        self.observation.callback(unprotected_message)

	    class Observation(protocol.ClientObservation):
	        # using the inheritance mainly for the __aiter__ that's so nicely generated from register_{call,err}back
	        def _register(self, *args):
	            "This is an OSCORE observation and doesn't register"
	        def _unregister(self, *args):
	            "This is an OSCORE observation and doesn't unregister"





class OscoreClientProgram:
	async def run(self):
		self.host = "localhost"

		# Get security context from FilesystemSecurityContext:

		security_context = my_get_security_context(role='client')

		# Make secure client context:

		self.ctx = await Context.create_client_context()
		self.protected_ctx = ProtectedRequester(self.ctx)
		self.protected_ctx.client_credentials["coap://%s/*" % self.host] = security_context

		# request = Message(code=GET, uri='coap://' + self.host + '/hello/coap')
		# response = await self.ctx.request(request).response
		# print("Response:", response)

		# print("")

		# additional_verify("Responde had correct code", response.code, CONTENT)
		# additional_verify("Responde had correct payload", response.payload, b"Hello World!")
		# additional_verify("Options as expected", response.opt, Message(content_format=0).opt)

		request = Message(code=GET, uri='coap://' + self.host+ '/hello/%d'%TESTNO + ("?first=1" if TESTNO == 2 else ""))
		expected = {'content_format': 0}
		if TESTNO == 2:
		    expected['etag'] = b"\x2b"
		if TESTNO == 3:
		    request.opt.accept = 0
		    expected['max_age'] = 5
		unprotected_response = await self.protected_ctx.request(request).response

		print("Unprotected response:", unprotected_response)
		# additional_verify("Code as expected", unprotected_response.code, CONTENT)
		# additional_verify("Options as expected", unprotected_response.opt, Message(**expected).opt)


	@classmethod
	def sync_run(cls):
	    asyncio.get_event_loop().run_until_complete(cls().run())



if __name__ == "__main__":
    OscoreClientProgram.sync_run()

