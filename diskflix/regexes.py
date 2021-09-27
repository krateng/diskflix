import re

FORMATS = {
	'video':['mkv','webm','mp4','avi'],
	'audio':['mp3','flac','wav','ogg'],
	'picture':['jpg','jpeg','png','webp'],
	'metadata':['yml','yaml']
}
def regex_formats(filetype):
	return r'\b(?:{0})\b'.format('|'.join(FORMATS[filetype]))
	
REGEX = {
	'episode': [
		re.compile(r'.*(?:s|season) ?([0-9]+) ?(?:e|episode) ?([0-9]+).*',re.IGNORECASE),
		re.compile(r'.*([0-9]+)x([0-9]+).*',re.IGNORECASE),
		re.compile(r'.*?()([0-9]+).*',re.IGNORECASE)
	],
	'season': [
		re.compile(r'(?:s|season) ?([0-9]+).*',re.IGNORECASE)
	],
	'cover': [
		re.compile(r'(?:cover|poster).*' + r'\.' + regex_formats('picture'),re.IGNORECASE)
	],
	'background': [
		re.compile(r'(?:bg|background).*' + r'\.' + regex_formats('picture'),re.IGNORECASE)
	],
	'music': [
		re.compile(r'(?:theme|music).*' + r'\.' + regex_formats('audio'),re.IGNORECASE)
	],
}

def try_match(string,category):
	for r in REGEX[category]:
		match = r.match(string)
		if match: return match
	return None
