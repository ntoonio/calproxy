import hashlib

def _md5(s):
	return hashlib.md5(s.encode()).hexdigest()
