from aiocoap import *

m1 = Message(code = GET)
m2 = Message(code = GET)
m1.opt.uri_path = ('s', '1')
m2.opt.uri_path = ('s', '1')
m1.opt.size1 = 10
m2.opt.size1 = 20

m1.get_cache_key() == m2.get_cache_key()
