import cherrypy
from app import *

class AJAXController(AppController):
  
  @cherrypy.expose
  def update(self, name_encoded):
    "Get all updates."
    user = get_user()
    if not user:
      return False
    # if not user.room.name_encoded == name_encoded:
    #   return False
    self.update_polled_time()
    import simplejson
    return simplejson.dumps({'messages': self.update_messages(),
      'users': self.update_users(), 'topic': self.update_topic()})
  
  def update_users(self):
    "Get list of users in the room."
    user = get_user()
    room = user.room
    room.cleanup()
    users = db_session.query(User).filter_by(room=room).\
      order_by(asc(User.name)).all()
    return tuple([user.name] + [u.name for u in users if u.name != user.name\
      and not u.name.startswith(u'System/')])
  
  def update_topic(self):
    "Get current room topic."
    room = get_user().room
    if not room:
      return False
    return room.topic
  
  def update_messages(self):
    "Get new messages since last retrieval."
    user = get_user()
    room = user.room
    
    bots.clock.time(room)
    last_retrieval = cherrypy.session.get('last_retrieval')
    if not last_retrieval:
      messages = db_session.query(Message).filter_by(room=room).filter(
        Message.date >= user.arrival_time).all()
    else:
      messages = db_session.query(Message).filter_by(room=room).filter(
        Message.id > last_retrieval).all()
    if messages:
      cherrypy.session['last_retrieval'] = messages[-1].id
    return tuple([{'user_name': m.user.name, 'message_text': m.text}\
      for m in messages])
  
  @cherrypy.expose
  def new_message(self, name_encoded, message_text, _=None):
    """
    Add a new message.
    (The _ is just Prototype.js being funky.)
    TODO: Make sure this is a POST request.
    """
    user = get_user()
    if not user or not user.room:
      return False
    message_text = message_text.strip()
    if not message_text:
      return ''
    db_session.save(Message(room=user.room, user=get_user(),
      text=unicode(message_text), date=datetime.datetime.now()))
    db_session.commit()
    return ''
  
  @cherrypy.expose
  def set_topic(self, name_encoded, topic):
    """Set the room topic.
       (The _ is just Prototype.js being funky.)
       TODO: Make sure this is a POST request."""
    user = get_user()
    if not user or not user.room:
      return False
    if not user.room.name_encoded == name_encoded:
      return False
    room = db_session.query(Room).get_by(name_encoded=name_encoded)
    if not user.can_set_topic(room):
      return False
    room.topic = encode_unicode(topic)
    db_session.commit()
    return topic
  
  @cherrypy.expose
  def register(self, password, _=None):
    """Register your name by providing a password.
       (The _ is just Prototype.js being funky.)
       TODO: Make sure this is a POST request."""
    user = get_user()
    if not user:
      return False
    if not user.password or password != user.password:
      import sha
      user.password = sha.new(password).hexdigest()
      db_session.commit()
      cherrypy.session['User'] = user
    return render('ajax/user_account')
  
  def update_polled_time(self):
    """Update the user's last polled time (now).
       (Maybe this can just a session variable?)"""
    user = get_user()
    if not user:
      cherrypy.session['User'] = False
      return False
    user.last_polled = datetime.datetime.now()
    db_session.commit()
    cherrypy.session['User'] = user
    return True
  
