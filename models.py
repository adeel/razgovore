import datetime
import re
import sha
import cgi

from elixir import *
from elixir.events import before_insert, before_update

metadata.bind = 'sqlite:///razgovore.db'
metadata.bind.echo = False

class User(Entity):
    id = Field(Integer, primary_key=True)
    nick = Field(Unicode(50))
    password = Field(Unicode(255))
    color = Field(PickleType)
    messages = OneToMany('Message')
    
    def get_instances(self):
        return UserInRoom.query.filter_by(user_id=self.id).all()
    instances = property(get_instances)
    
    def get_rooms(self):
        return [i.room for i in self.instances]
    rooms = property(get_rooms)
    
    def __repr__(self):
        return "User#%s (%s)" % (self.id, self.nick)
    
    @before_insert
    def hash_password(self, password=None):
        if password:
            return sha.new(password).hexdigest()
        if not self.password:
            return False
        self.password = sha.new(self.password).hexdigest()

class Room(Entity):
    id = Field(Integer, primary_key=True)
    name = Field(Unicode(50))
    name_ = Field(Unicode(50))
    topic = Field(UnicodeText)
    is_latex_on = Field(Boolean, default=False)
    was_created_on = Field(DateTime)
    messages = OneToMany('Message')
    
    def get_instances(self):
        return UserInRoom.query.filter_by(room_id=self.id).all()
    instances = property(get_instances)
    
    def get_users(self):
        return [i.user for i in self.instances]
    users = property(get_users)
    
    def __repr__(self):
        return "Room#%s (%s)" % (self.id, self.name)
    
    def add_user(self, user, **options):
        if user not in self.users:
            UserInRoom(room=self, user=user, **options)
            Message(room=self, text="%s has entered the room." % user.nick)
            session.commit()
    
    def is_active(self):
        last = self.time_since_last_message()
        if not last:
            return False
        return last.days < 1
    
    def time_since_last_message(self):
        if self.messages:
            return datetime.datetime.now() - self.messages[-1].date
    
    def headcount(self):
        self.cleanup()
        return len(self.users)
    
    def cleanup(self):
        for user in self.users:
            now = datetime.datetime.now()
            delta = (now - user.last_poll).seconds
            if delta > 10:
                if delta < 60:
                    Message(room=self, text="%s left." % user.nick)
                user.room = None
        session.commit()
    
    @before_insert
    @before_update
    def urlize_name(self):
        re_whitespace = re.compile('\s+')
        re_invalid_chars = re.compile('[^A-Za-z0-9_\-]')
        name_ = self.name.lower()
        name_ = re_whitespace.sub('-', name_)
        name_ = re_invalid_chars.sub('', name_)
        self.name_ = name_

class UserInRoom(Entity):
    """This model represents a single instance of one User in one Room."""
    id = Field(Integer, primary_key=True)
    user_id = Field(Integer)
    room_id = Field(Integer)
    is_admin = Field(Boolean, default=False)
    last_ping = Field(DateTime, default=datetime.datetime.now)
    arrived_on = Field(DateTime, default=datetime.datetime.now)
    
    def _get_user(self):
        return User.get_by(id=self.user_id)
    def _set_user(self, user):
        self.user_id = user.id
    user = property(_get_user, _set_user)
    
    def _get_room(self):
        return Room.get_by(id=self.room_id)
    def _set_room(self, room):
        self.room_id = room.id
    room = property(_get_room, _set_room)
    
    def __repr__(self):
        return "<%s in %s>" % (self.user, self.room)

class Message(Entity):
    id = Field(Integer, primary_key=True)
    user = ManyToOne('User')
    room = ManyToOne('Room')
    text = Field(UnicodeText)
    date = Field(DateTime, default=datetime.datetime.now)
    
    def __repr__(self):
        return "Message#%s ('%s', room=%s, user=%s, date=%s)" % (self.id,
            self.text, self.room, self.user, self.date)
    
setup_all()