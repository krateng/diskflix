import os
import re
from . import data
import random

FORMATS = {
	'video':['mkv','webm','mp4','avi'],
	'audio':['mp3','flac'],
	'picture':['jpg','jpeg','png','webp'],
	'metadata':['yml']
}
IGNOREFILES = ['.diskflix_ignore']

REGEX = {
	'episode': [
		re.compile(r'.*(?:s|season) ?([0-9]+) ?(?:e|episode) ?([0-9]+).*',re.IGNORECASE),
		re.compile(r'.*([0-9]+)x([0-9]+).*',re.IGNORECASE),
		re.compile(r'.*?()([0-9]+).*',re.IGNORECASE)
	],
	'season': [
		re.compile(r'(?:s|season) ?([0-9]+)',re.IGNORECASE)
	]
}

uid = 0
def get_numbered_object():
	global uid
	uid += 1
	obj = {'id':uid}
	data.media['direct'][uid] = obj
	return obj


join = os.path.join



def try_match(string,category):
	for r in REGEX[category]:
		match = r.match(string)
		if match: return match
	return None

def ext(filename):
	return filename.lower().split(".")[-1]
	
def filesin(root):
	return [f for f in os.listdir(root) if not os.path.isdir(os.path.join(root,f))]

def foldersin(root):
	return [f for f in os.listdir(root) if os.path.isdir(os.path.join(root,f))]

def filterfiles(files,filetypes):
	return [[f for f in files if ext(f) in FORMATS[ft]] for ft in filetypes]

def guess_type(folders,files):
	for f in folders+files:
		if try_match(f,'season'):
			return 'show'
	videofiles, = filterfiles(files,['video'])
	
	if len(videofiles) == 0:
		return None
	if len(videofiles) < 5:
		if all([name[0].isdigit() for name in videofiles]): return 'show'
		else: return 'movie'
	else:
		return 'show'
	
			
	
		
	return None

def parse_common(root):
	info = get_numbered_object()
	info.update({
		'folder':root,
		'presentation':{
			'cover':[],
			'background':[],
			'music':[]
		},
		'metadata':{
			'title':os.path.basename(root),
			'sorttitle':os.path.basename(root),
			'cover':'',
			'background':'',
			'music':'',
		}
	})
	
	imgfiles, audiofiles = filterfiles(filesin(root),['picture','audio'])
	
	for fn in imgfiles:
		if 'background' in fn.lower():
			info['presentation']['background'].append(join(root,fn))
		if 'cover' in fn.lower() or 'poster' in fn.lower():
			info['presentation']['cover'].append(join(root,fn))
			
	for fn in audiofiles:
		if 'theme' in fn.lower():
			info['presentation']['music'].append(join(root,fn))
		
		
	
		
	return info

def parse_season(root,parentshow,num):
	info = get_numbered_object()
	info.update({
		'presentation':{
			'cover':[],
			'background':[],
			'music':[],
		},
		'metadata':{
			'cover':'', #parentshow['metadata']['cover']
			'background':'',
			'music':'',
			'title':'Season ' + str(num)
		},
		'episodes':{
		
		}
	})
	
	imgfiles, = filterfiles(filesin(root),['picture'])
	for fn in imgfiles:
		if 'cover' in fn.lower() or 'poster' in fn.lower() or 'season' in fn.lower():
			info['presentation']['cover'].append(join(root,fn))
	
	for pres_type in ['cover']:
		if info['metadata'][pres_type] == '' and info['presentation'][pres_type]:
			info['metadata'][pres_type] = random.choice(info['presentation'][pres_type])
			
	
	return info
	
	

def parse_show(root):
	info = parse_common(root)
	videofiles,imgfiles = filterfiles(filesin(root),['video','picture'])
	info['seasons'] = {}
	
	# check videos for containing episode information
	for fn in videofiles:
		fn_raw = '.'.join(fn.split('.')[:-1])
		match = try_match(fn_raw,'episode')
		if match:
			season,episode = match.groups()
			if season.strip() == '': season = 1
			s, e = int(season), int(episode)
			info['seasons'].setdefault(s,parse_season(root,info,s))
			info['seasons'][s]['episodes'].setdefault(e,{'files':[]})
			info['seasons'][s]['episodes'][e]['files'].append(join(root,fn))
	
	
		
	# check subfolders that might represent seasons	
	for fol in foldersin(root):
		match = re.match(r's(?:eason)? ?([0-9]+)',fol.lower())
		if match:
			season = match.groups()[0]
			s = int(season)
			info['seasons'].setdefault(s,parse_season(join(root,fol),info,s))
			videofiles, = filterfiles(filesin(join(root,fol)),['video'])
			for fn in videofiles:
				fn_raw = '.'.join(fn.split('.')[:-1])
				match = try_match(fn_raw,'episode')
				if match:
					_, e = match.groups()
					e = int(e)
					info['seasons'][s]['episodes'].setdefault(e,{'files':[]})
					info['seasons'][s]['episodes'][e]['files'].append(join(root,fol,fn))
					
	# check images that might belong to seasons		
	for fn in imgfiles:
		fn_raw = '.'.join(fn.split('.')[:-1])
		match = try_match(fn_raw,'season')
		if match:
			season = match.groups()[0]
			s = int(season)
			info['seasons'].setdefault(s,parse_season(root,info,s))
			info['seasons'][s]['presentation']['cover'].append(join(root,fn))
			
			
	return info

def parse_movie(root):
	info = parse_common(root)
	videofiles, = filterfiles(filesin(root),['video'])
	info['files'] = [join(root,f) for f in videofiles]
	
	return info


def parse_tree(path):
	for root,dirs,files in os.walk(path,topdown=True):
	
		for f in files:
			if f in IGNOREFILES:
				dirs[:] = []
				break
				
		
				
				
		else:
			dirs[:] = [d for d in dirs if not d.startswith('.')]
			
			
			foldertype = guess_type(dirs,files)
			if foldertype:
				dirs[:] = []
				
				if foldertype == 'show':
					info = parse_show(root)
					data.media['shows'].append(info)
				elif foldertype == 'movie':
					info = parse_movie(root)
					data.media['movies'].append(info)
					
	
	for info in data.media['direct'].values():
		for pres_type in ['background','cover','music']:
			if info['metadata'][pres_type] == '' and info['presentation'][pres_type]:
				info['metadata'][pres_type] = random.choice(info['presentation'][pres_type])


