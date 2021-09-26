from . import parser, data
from pprint import pprint
import bottle
import waitress
from jinja2 import Environment, PackageLoader
import pkgutil

jinjaenv = Environment(loader=PackageLoader('diskflix'))

app = bottle.Bottle()

@app.get('/<filename>.html')
def page(filename):
	template = jinjaenv.get_template(filename + ".html.jinja")
	query = bottle.FormsDict.decode(bottle.request.query)
	for k in query:
		try: query[k] = int(query[k])
		except: pass
	return template.render(**data.media,query=query)

@app.get('/static/<filename:path>.<ext>')
def staticfile(filename,ext):
	return pkgutil.get_data(__name__,"static/" + filename + '.' + ext)
	
@app.get('/<filename:path>.<ext>')
def usercontent(filename,ext):
	return bottle.static_file(filename + '.' + ext,root="./")
	
	# potentially sign every loaded file to only allow what the server actually needs

@app.get('/data.json')
def api():
	return data.media

if __name__ == '__main__':
	parser.parse_tree(".")
	print("Loaded library!")
		
	print("Serving on localhost:8080...")
	waitress.serve(app,host='localhost',port=8080,threads=16)	
	#bottle.run(server='waitress',host='localhost',port=8080)
