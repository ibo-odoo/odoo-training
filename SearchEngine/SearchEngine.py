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
        
        session_id = request.cookies.get('session_id')
        if not session_id:
            session_id = self.make_token()
            self.session = self.create_session(session_id)
        else:
            self.session = self.read_session(session_id)

        with open('static/app.json') as response:
            data = json.loads(response.read())
          

        response = self.render_template("page.html",data=data,session_data=self.session)
        response.set_cookie('session_id',self.session['session_id'])
        return response

    def search_controller(self, request):
       
        keyworddata = request.args.get('searchkey')
        
        with open('static/app.json') as response:
            data = json.loads(response.read()) 
        mykeydata=[]

        for i in data['result']:
            i.update({'visited': 'false'})
            if keyworddata in i['keyword']:
                for session in self.session.get('data'):
                    if i.get('link') in session['url']:
                        i.update({'visited': 'true'})
                mykeydata.append(i)
                
        return Response(json.dumps(mykeydata),mimetype='application/json')

    def visit(self, request):
        
        session_id = request.cookies.get('session_id')
        visited_links = request.args.get('url')
        if session_id:
            with open('static/session.json') as response:
                session_source = response.read()
            session_data = json.loads(session_source)           
            newData = []
            urls = []
            for session in session_data["session_data"]:

                if session_id == session.get('session_id'):
                    if session.get('data'):
                        for session_data in session.get('data'):
                            urls.append(session_data.get('url'))
                        if visited_links in urls:
                            self.session = session
                            for session_data in session.get('data'):
                                if session_data.get('url') == visited_links:
                                    session_data['count'] += 1
                        else:
                            session['data'].append({'url': visited_links, 'count': 1})
                            self.session = session
                    else:
                        session['data'].append({'url': visited_links, 'count': 1})
                    newData.append(session)
            sessionFile = open("static/session.json", "w+")
            sessionData = {'session_data': newData}
            sessionFile.write(json.dumps(sessionData))
            sessionFile.close()
        response = {
            "session": self.session 
        }
        # visited_links = self.session.get('visited_links')
        # if target_url not in visited_links:
        #     visited_links.append(target_url)
        # import pdb;pdb.set_trace()
        # with open('static/app.json') as response:
        #     data = json.loads(response.read())
        # updated_row = []

        # for i in data["result"]:   
        #     if url in i['visited_links']:
        #         # if int(Mylikes) < 0:

        #         i["count"] = count
        #         self.session['count'] += 1

        #         updated_row.append(i)

        # result = { "row": updated_row}
        # print(self.session)

        # jsonFile = open("static/app.json", "w+")
        # jsonFile.write(json.dumps(data))

        # jsonFile.close()
        # with open('static/session.json') as response:
        #     session_source = response.read()
        # session_data = json.loads(session_source)
        # newData = []
        # for session in session_data["session_data"]:   
        #     if self.session['session_id'] in session['session_id']:
        #         session = self.session
        #     newData.append(session)

        # sessionFile = open("static/session.json", "w+")
        # sessionData = {'session_data': newData}
        # sessionFile.write(json.dumps(sessionData))

        # sessionFile.close()

        # response = {
        #     "updated_row":updated_row,
        #     "session": self.session 
        # }
        return Response(json.dumps(response), mimetype='application/json')

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

    def create_session(self, session_id):

        with open('static/session.json') as response:
            data = response.read()
        session_data = json.loads(data)
        data = { "session_id": session_id , "data":[]}
        session_data['session_data'].append(data)     
        jsonFile = open("static/session.json", "w")
        jsonFile.write(json.dumps(session_data))
        jsonFile.write("\n")
        jsonFile.close()
        return data

    def read_session(self, session_id):
        with open('static/session.json') as response:
            source = response.read()
        data = json.loads(source)

        for session in data["session_data"]:   
            if session_id in session['session_id']:
                return session
    

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