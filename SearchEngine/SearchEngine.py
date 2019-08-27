import os
import json
import secrets
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.utils import redirect
from jinja2 import Environment, FileSystemLoader


class SearchEngine(object):

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def __init__(self):
        self.session={}
        template_path = os.path.join(os.path.dirname(__file__), 'template')
    
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                 autoescape=True)  
        self.url_map = Map([
            Rule('/', endpoint='index_url'),
            Rule('/search_controller', endpoint='search_controller'),
            Rule('/visit', endpoint='visit')
            ])
    
    
    def index_url(self, request):
        
        sid = request.cookies.get('session')
        visited_links = self.session.get('visited_links') or []
        print('sid', sid)
        if sid is None:
            sid = self.make_token()
            visited_links = []
        self.session.update({
            'session_id': sid,
            'visited_links': visited_links
            })
        with open('static/app.json') as response:
            data = json.loads(response.read())
          

        response = self.render_template("page.html",data=data)
        response.set_cookie('session', sid)
        return response

    def search_controller(self, request):
       
        keyworddata = request.args.get('searchkey')
        with open('static/app.json') as response:
            data = json.loads(response.read()) 
        mykeydata=[]

        for i in data['result']:
            i.update({'visited': 'false'})
            if keyworddata in i['keyword']:
                if i.get('link') in self.session.get('visited_links'):
                    i.update({'visited': 'true'})
                mykeydata.append(i)
                
        return Response(json.dumps(mykeydata),mimetype='application/json')

    def visit(self, request):
        
        print('url', request.args.get('url'))
        target_url = request.args.get('url')
        visited_links = self.session.get('visited_links')
        print('visited_links', visited_links, type(visited_links))
        if target_url not in visited_links:
            visited_links.append(target_url)
        self.session.update({
            'visited_links': visited_links
            })
        return redirect(target_url)


    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            print('endpoint', endpoint)
            return getattr(self, endpoint)(request, **values)
        except HTTPException as e:
            return e    
    
    def render_template(self, templatename, **context):
        t = self.jinja_env.get_template(templatename)
        return Response(t.render(context), mimetype='text/html')

    def make_token(self):
        return secrets.token_urlsafe(16)
    

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