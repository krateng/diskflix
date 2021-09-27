import itertools
import yaml
import os
import re

from .regexes import try_match, REGEX, FORMATS

entities = {}




	
def ext(filename):
	return filename.lower().split(".")[-1]

class Entity:

	id_iter = itertools.count()
	
	def __init__(self,root,dedicated_folder=True):
		self.folder = root
		self.id = next(self.id_iter)
		entities[self.id] = self
		self.metadata = {
			'title':None,
			'sorttitle':None,
			'cover':None,
			'background':None,
			'music':None,
			'cast':{}
		}
		self.parent = None
		self.children = {}
		
		if dedicated_folder:
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
		
	def get_link(self):
		return "/" + self.entity_type + ".html?id=" + str(self.id)
		
	def list_files_in(self):
		return [f for f in os.listdir(self.folder) if not os.path.isdir(os.path.join(self.folder,f))]
	
	def list_folders_in(self):
		return [f for f in os.listdir(self.folder) if os.path.isdir(os.path.join(self.folder,f))]
		
	def list_files_in_by_type(self):
		return {ft:[f for f in self.list_files_in() if ext(f) in FORMATS[ft]] for ft in FORMATS}
		
	def open_file(self,path):
		return open(os.path.join(self.folder,path))
		
	def read_metadata(self):
		self.metadata['title'] = os.path.basename(self.folder)
		self.metadata['sorttitle'] = os.path.basename(self.folder)
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
	entity_type = 'movie'
	
class Show(Entity):
	entity_type = 'show'
	def __init__(self,root,**kwargs):
		super().__init__(root,**kwargs)
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
				self.seasons.setdefault(s,Season(self.folder,show=self,number=s,dedicated_folder=False))
				self.seasons[s].episodes[e] = f
		
		
			
		# check subfolders that might represent seasons	
		for f in self.list_folders_in():
			match = try_match(f,'season')
			if match:
				season = match.groups()[0]
				s = int(season)
				self.seasons.setdefault(s,Season(os.path.join(self.folder,f),show=self,number=s))
						
		# check images that might belong to seasons
		for f in self.list_files_in_by_type()['picture']:
			match = try_match(f,'season')
			if match:
				season = match.groups()[0]
				s = int(season)
				self.seasons.setdefault(s,Season(self.folder,show=self,number=s,dedicated_folder=False))
				self.seasons[s].metadata['cover'] = f
	
class Season(Entity):
	entity_type = 'season'

	def __init__(self,root,show,number,**kwargs):
		super().__init__(root,**kwargs)
		self.metadata['title'] = "Season " + str(number)
		self.parent = show
		self.show = self.parent
		self.episodes = self.children
	
	def __json__(self):
		return {
			** super().__json__(),
			'episodes':self.episodes	
		}
		
	def load_metadata(self):
		super().load_metadata()
		if self.metadata['cover'] is not None and os.path.exists(os.path.join(self.folder,self.metadata['cover'])):
			pass
		else:
			files = self.list_files_in_by_type()['picture']
			#print('check files',files)
			for f in files:
				match = try_match(f,'season')
				if match:
					self.metadata['cover'] = f
					break
		

	def get_media(self,mediatype):
		if self.metadata[mediatype] is not None:
			return self.get_file(self.metadata[mediatype])
		else:
			return self.show.get_media(mediatype)

class Episode(Entity):
	def __init__(self,root,season,**kwargs):
		super().__init__(root,**kwargs)
		self.parent = season
		self.season = self.parent
