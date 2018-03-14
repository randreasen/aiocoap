# Para inicializar el seq no? Hara falta?

 set_seqno = aiocoap.Message(code=aiocoap.PUT, uri='coap://%s/sequence-numbers'%(common.loopbackname_v6 or common.loopbackname_v46), payload=b'0')
        await self.client.request(set_seqno).response_raising

# Debo primero mandar los mensajes

