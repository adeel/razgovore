import datetime

from elixir import *
from elixir.events import *

import config

metadata.bind = config.db
metadata.bind.echo = True

class Room(Entity):
  id = Field(Integer, primary_key=True)
  name = Field(Unicode(255))
  name_encoded = Field(Unicode(255))
  description = Field(Unicode(255))
  topic = Field(Text, default='WELCOME')
  creation_date = Field(DateTime, default=datetime.datetime.now)
  creator_id = Field(Integer)
  users = OneToMany('User')
  messages = OneToMany('Message')
  is_latex_on = Field(Boolean, default=False)
  
  def __repr__(self):
    return '<Room#%s(%s)>' % (self.id, self.name)
  
  def is_active(self):
    return self.time_since_last_message().days < 1
  
  def time_since_last_message(self):
    if not self.messages:
      last_message_date = self.creation_date
    else:
      last_message_date = self.messages[-1].date
    return datetime.datetime.now() - last_message_date
  
  def encode_name(self):
    import re
    name_encoded = self.name.lower()
    name_encoded = re.compile('\s+').sub('-', name_encoded)
    name_encoded = re.compile('[^A-Za-z0-9_\!\?\.\,\-]').sub('', name_encoded)
    self.name_encoded = name_encoded
  encode_name = before_insert(encode_name)
  encode_name = before_update(encode_name)
  
  def cleanup(self):
    import bots.notifier
    users = User.query.filter_by(room=self).all()
    for user in users:
      if not user.name.startswith('System/'):
        now = datetime.datetime.now()
        elapsed = (now - user.last_polled).seconds
        if elapsed > 10:
          if elapsed < 60:
            bots.notifier.left(user)
          user.room = None
    session.commit()
    return True
  
  def headcount(self):
    """Get a headcount of the users in the room."""
    self.cleanup()
    return len([True for u in self.users if not u.name.startswith('System/')])
  

class Message(Entity):
  id = Field(Integer, primary_key=True)
  text = Field(Text)
  user = ManyToOne('User')
  room = ManyToOne('Room')
  date = Field(DateTime, default=datetime.datetime.now)
  
  def __repr__(self):
    return "<%s>" % self.text
  
  def filters(self):
    import cgi, filters
    from util import encode_unicode
    self.text = cgi.escape(self.text)
    self.text = encode_unicode(self.text)
    self.text = filters.urls_to_links(self.text)
    if self.room.is_latex_on:
      self.text = filters.latex(self.text)
  filters = before_insert(filters)
  

class User(Entity):
  id = Field(Integer, primary_key=True)
  name = Field(Unicode(255))
  password = Field(Unicode(255))
  arrival_time = Field(DateTime, default=datetime.datetime.now)
  last_polled = Field(DateTime, default=datetime.datetime.now)
  room = ManyToOne('Room')
  admin = Field(Boolean, default=False)
    
  def can_set_topic(self, room):
    return self.admin
  
  def can_create_room(self):
    return self.admin
  
  def can_delete_room(self, room):
    return self.admin or self.id == room.creator_id
  
  def hash_password(self, password=None):
    import sha
    if password: return sha.new(password).hexdigest()
    if not self.password: return False
    self.password = sha.new(self.password).hexdigest()
  hash_password = before_insert(hash_password)
  
  def __repr__(self):
    return "<%s>" % self.name
  

setup_all()
# create_all()

def defaults():
  create_all()
  [x.delete() for x in User.query.all() + Room.query.all() + Message.query.all()]
  user = User(name=u"adeel", admin=True)
  session.flush()
  room = Room(name=u"Test", description=u"This is a test room.", topic=u"testing",
    creator_id=user.id)
  session.flush()
  
  # system users
  User(name=u"System/time", room=room, messages=[])
  User(name=u"System/notifier", room=room, messages=[])
  
  session.flush()
  session.commit()
