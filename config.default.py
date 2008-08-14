db = {'hostname': 'localhost',
  'database': 'razgovore',
  'username': 'username',
  'password': 'password'}

db = 'mysql://%s:%s@%s/%s' % (
    db['username'], db['password'], db['hostname'], db['database'])

cherrypy = {'server.socket_host': '127.0.0.1',
  'server.socket_port': 80,
  'log.screen': True,
  'request.show_tracebacks': True,
  'tools.sessions.on': True,
  'tools.sessions.timeout': 360}