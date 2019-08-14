import os
import json
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.utils import redirect
from jinja2 import Environment, FileSystemLoader
from http import cookies

class SearchEngine(object):

    def dispatch_request(self, request):
        return Response('Hello World!')

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def __init__(self):
    
        template_path = os.path.join(os.path.dirname(__file__), 'template')
    
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                 autoescape=True)  
        self.url_map = Map([
            Rule('/', endpoint='index_url'),
            Rule('/search_controller', endpoint='search_controller')
            #Rule('/link_color', endpoint='link_color')
            ])
    
    
    def index_url(self, request):
        with open('static/app.json') as response:
            data = json.loads(response.read())
            #data = json.load(source)
            print(data)

        return self.render_template("page.html",data=data)

    def search_controller(self, request):

        keyworddata = request.args.get('searchkey')
        with open('static/app.json') as response:
            data = json.loads(response.read())
            #data = json.load(source)
        #data = json.loads(keyword) 
        mykeydata=[]
        for i in data['result']:
            #import pdb;pdb.set_trace()
            if keyworddata in i['keyword']:
               mykeydata.append(i)
               print(mykeydata)
            
        return Response(json.dumps(mykeydata),mimetype='application/json')


    def link_color(self, request):
        myquestion=request.args.get('myque')
        #Get cookies
        cookie_data=request.cookie.get('app_cookie')
        searched_data=[]
        if cookie_data:
            #Read cookies
            cookie=json.loads(cookie_data)
            print(cookie)
            #set cookies
        if cookie.exist:

        else:
            response.set_cookie('app_cookie', cookie_data,
                            httponly=True)
        
        with open('static/app.json') as response:
            data = json.loads(response.read())
        
        for i in data['result']:
            if i[0] in cookie:
                searched_data.append(i)
                print(searched_data)

        return Response('app_cookie',json.dumps(searched_data))


    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, endpoint)(request, **values)
        except HTTPException as e:
            return e    
    
    def render_template(self, templatename, **context):
        t = self.jinja_env.get_template(templatename)
        return Response(t.render(context), mimetype='text/html')
    

def create_app():
    app = SearchEngine()
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/static':  os.path.join(os.path.dirname(__file__), 'static')
    })
    return app

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    app = create_app()
    run_simple('127.0.0.1', 5000, app, use_debugger=True, use_reloader=True)





