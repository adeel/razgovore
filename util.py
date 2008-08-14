import time, datetime

def render(filename, data={}):
  import cherrypy
  from jinja import Environment, FileSystemLoader
  environment = Environment(loader=FileSystemLoader('views'))
  
  data['VERSION'] = encode_unicode(file('VERSION').read()).strip()
  try:
    data['flash'] = get_flash()
    data['flash_class'] = cherrypy.session['flash_class']
  except KeyError: pass
  data.update(helpers)
  data['User'] = cherrypy.session.get('User')
  return environment.get_template(filename + '.jinja').render(data)

def render_comet(output_fn, output_fn_args=(), comet_type=1, comet_name='piComet', force_cache=None):
  import cherrypy
  import sys, pi
  cherrypy.response.headers['Content-Type'] = pi.getContentType(comet_type)
  while True:
    yield pi.getOutput(output_fn(*output_fn_args), comet_type, comet_name)
    sys.stdout.flush()
    time.sleep(1)

def get_user():
  import cherrypy
  from elixir import session as db_session
  db_session.clear()
  from models import User
  try:
    return User.get_by(id=cherrypy.session.get('User').id)
  except AttributeError:
    return None

def check_session():
  import cherrypy
  if not cherrypy.session.get('User'):
    redirect('/')

def set_flash(message, klass='note'):
  import cherrypy
  cherrypy.session['flash'] = message
  cherrypy.session['flash_class'] = klass

def get_flash():
  import cherrypy
  flash = cherrypy.session['flash']
  cherrypy.session['flash'] = None
  return flash

def redirect(url):
  import cherrypy
  raise cherrypy.HTTPRedirect(url)

def encode_unicode(text):
  try:
    text = unicode(text)
  except:
    try:
      text = text.decode('utf-8', 'xmlcharrefreplace')
    except UnicodeEncodeError:
      return False
  return encode_entities(text)

def encode_entities(string):
  chars = []
  for char in string:
    if ord(char) < 128:
      chars.append(char)
    else:
      chars.append('&#%i;' % ord(char))
  return ''.join(chars)

class date_helper:
  def now(self):
    return datetime.datetime.now()
  def format(self, date, format='%e %B %Y'):
    return datetime.datetime.strftime(date, format)
  def timestamp(self, date=None):
    if not date:
      return int(time.time())
    return int(time.mktime(time.strptime(date.ctime())))
  

def pluralise(single, multiple, size):
  if size == 0:
    return "No %s" % multiple
  elif size == 1:
    return "1 %s" % single
  else:
    return "%s %s" % (size, multiple)

# view helpers
helpers = {'date': date_helper, 'pluralise': pluralise}

def sort_rooms_by_activity(a, b):
  a = a.time_since_last_message()
  b = b.time_since_last_message()
  if a > b: return 1
  if a < b: return -1
  return 0
