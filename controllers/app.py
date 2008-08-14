import cherrypy

from sqlalchemy import asc
from .models import User, Room, Message
from .models import session as db_session
from util import *

import bots.notifier
import bots.clock

def handle_error():
  cherrypy.response.status = 404
  cherrypy.response.body = '<h1>Error</h1>'

class AppController(object):
  
  _cp_config = {'request.error_response': handle_error}
  
  def clear_session(self):
    cherrypy.session['User'] = None
    redirect('/')
  
