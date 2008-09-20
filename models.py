from elixir import *

metadata.bind = 'sqlite:///razgovore.db'
metadata.bind.echo = True

class User(Entity):
    id = Field(Integer, primary_key=True)
    nick = Field(Unicode(50))
    password = Field(Unicode(50))
    color = Field(PickleType)
    rooms = ManyToMany('Room')
    messages = OneToMany('Message')
    
    def __repr__(self):
        return "<User#%s (%s)>" % (self.id, self.nick)
    

class Room(Entity):
    id = Field(Integer, primary_key=True)
    name = Field(Unicode(50))
    topic = Field(UnicodeText)
    users = ManyToMany('User')
    messages = OneToMany('Message')
    
    def __repr__(self):
        return "<Room#%s (%s)>" % (self.id, self.name)

class Message(Entity):
    id = Field(Integer, primary_key=True)
    user = ManyToOne('User')
    room = ManyToOne('Room')
    text = Field(UnicodeText)
    date = Field(DateTime)
    
    def __repr__(self):
        return "<Message#%s ('%s', room=%s, user=%s, date=%s)>" % (self.id,
            self.text, self.room, self.user, self.date)
    

setup_all()