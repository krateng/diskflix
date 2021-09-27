import itertools
import yaml
import os
import re

entities = {}

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
	
	
def ext(filename):
	return filename.lower().split(".")[-1]

class Entity:

	id_iter = itertools.count()
	
	def __init__(self,root):
		self.folder = root
		self.id = next(self.id_iter)
		entities[self.id] = self
		self.metadata = {
			'title':os.path.basename(self.folder),
			'sorttitle':os.path.basename(self.folder),
			'cover':None,
			'background':None,
			'music':None,
			'cast':{}
		}
		self.parent = None
		self.children = {}
		
		self.read_metadata()
		self.load_metadata()
		
	def __json__(self):
		return {
			'serverdata':{
				'folder':self.folder,
				'id':self.id
			},
			'metadata':self.metadata
		}
		
	def list_files_in(self):
		return [f for f in os.listdir(self.folder) if not os.path.isdir(os.path.join(self.folder,f))]
	
	def list_folders_in(self):
		return [f for f in os.listdir(self.folder) if os.path.isdir(os.path.join(self.folder,f))]
		
	def list_files_in_by_type(self):
		return {ft:[f for f in self.list_files_in() if ext(f) in FORMATS[ft]] for ft in FORMATS}
		
	def open_file(self,path):
		return open(os.path.join(self.folder,path))
		
	def read_metadata(self):
		for f in self.list_files_in_by_type()['metadata']:
			with self.open_file(f) as fd:
				self.metadata.update(yaml.safe_load(fd))
				
	def load_metadata(self):
		for mediatype in ('cover','background','music'):
			if self.metadata[mediatype] is not None and os.path.exists(os.path.join(self.folder,self.metadata[mediatype])):
				pass
			else:
				files = self.list_files_in()
				#print('check files',files)
				for f in files:
					match = try_match(f,mediatype)
					if match:
						self.metadata[mediatype] = f
						break
					
		
	def get_file(self,path):
		return os.path.join(self.folder,path)
		
	def get_media(self,mediatype):
		if self.metadata[mediatype] is not None:
			return self.get_file(self.metadata[mediatype])
		else:
			return ''



class Movie(Entity):
	pass
	
class Show(Entity):
	def __init__(self,root):
		super().__init__(root)
		self.seasons = self.children
		self.get_seasons()
		
	def __json__(self):
		return {
			** super().__json__(),
			'seasons':self.seasons	
		}
		
		
	def get_seasons(self):
	
		
		# check videos for containing episode information
		for f in self.list_files_in_by_type()['video']:
			match = try_match(f,'episode')
			if match:
				season,episode = match.groups()
				if season.strip() == '': season = 1
				s, e = int(season), int(episode)
				self.seasons.setdefault(s,Season(self.folder,self))
				self.seasons[s].episodes[e] = f
		
		
			
		# check subfolders that might represent seasons	
		for f in self.list_folders_in():
			match = try_match(f,'season')
			if match:
				season = match.groups()[0]
				s = int(season)
				self.seasons.setdefault(s,Season(os.path.join(self.folder,f),self))
						
		# check images that might belong to seasons
		for f in self.list_files_in_by_type()['picture']:
			match = try_match(f,'season')
			if match:
				season = match.groups()[0]
				s = int(season)
				self.seasons.setdefault(s,Season(self.folder,self))
	
class Season(Entity):

	def __init__(self,root,show):
		super().__init__(root)
		self.parent = show
		self.episodes = self.children
	
	def __json__(self):
		return {
			** super().__json__(),
			'episodes':self.episodes	
		}

	def get_media(self,mediatype):
		if self.metadata[mediatype] is not None:
			return self.get_file(self.metadata[mediatype])
		else:
			return self.show.get_media(mediatype)

class Episode(Entity):
	def __init__(self,root,season):
		super().__init__(root)
		self.parent = season
		self.season = self.parent
