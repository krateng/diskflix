from simplejson import JSONEncoder

JSONEncoder.oldencoder = JSONEncoder.default
def newencoder(Enc, obj):
	try:
		return obj.__json__()
	except:
		return Enc.oldencoder(obj)
	
JSONEncoder.default = newencoder
