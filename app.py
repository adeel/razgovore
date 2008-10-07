import os
import cherrypy
from sqlalchemy import asc
from jinja2 import Environment, FileSystemLoader
import config
from models import User, Room, Message
from models import session as db_session

class Controller(object):
    
    # util functions
    
    def __init__(self):
        loader = FileSystemLoader('views/')
        self.views = Environment(loader=loader)
    
    def render(self, filename, data={}):
        return self.views.get_template(filename + '.jinja').render(data)
    
    def get_session(self):
        db_session.clear()
        user = cherrypy.session.get('User')
        if not user or not user.id:
            return None
        user = User.get_by(id=user.id)
        cherrypy.session['User'] = user
        return user
    
    def force_login(self):
        user = self.get_session()
        if not user:
            self.redirect('/login')
        return user
    
    def redirect(self, url):
        raise cherrypy.HTTPRedirect(url)
    
    # exposed methods
    
    @cherrypy.expose
    def index(self):
        rooms = Room.query.all()
        user = self.get_session()
        return self.render('list_rooms', {'rooms': rooms})
    
controller = Controller()

dispatcher = cherrypy.dispatch.RoutesDispatcher()

dispatcher.connect('register', 'register', controller, action='register')

dispatcher.connect('update', ':name_/update', controller, action='update')
dispatcher.connect('post', ':name_/message', controller, action='new_message')
dispatcher.connect('set_topic', ':name_/topic', controller, action='set_topic')

dispatcher.connect('room_new', 'new', controller, action='new')
dispatcher.connect('room_leave', ':name_/leave', controller, action='leave')
dispatcher.connect('room_delete', ':name_/delete', controller, action='delete')
dispatcher.connect('room', ':name_', controller, action='chat')

dispatcher.connect('index', '', controller, action='index')

# maybe there's a better way to do this
app_dir = os.path.dirname(os.path.abspath(__file__))

cherrypy.config.update({
    'server.socket_host': config.SERVER_HOST,
    'server.socket_port': config.SERVER_PORT,
    'tools.sessions.on': True,
    'tools.sessions.timeout': 360
})

cherrypy.quickstart(controller, '/', {
  '/': {
    'tools.staticdir.root': app_dir,
    'request.dispatch': dispatcher,
  },
  '/static': {
    'tools.staticdir.on': True,
    'tools.staticdir.dir': 'static'
  }
})