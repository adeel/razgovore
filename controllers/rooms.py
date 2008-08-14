import cherrypy
from app import *

class RoomsController(AppController):
  
  @cherrypy.expose
  def index(self):
    "List active rooms."
    rooms = db_session.query(Room).all()
    active_rooms = [x for x in rooms if x.is_active()]
    active_rooms.sort(sort_rooms_by_activity)
    return render('rooms/list', {'rooms': rooms, 'active_rooms': active_rooms[:10]})
  
  @cherrypy.expose
  def new(self, name=None, description=None, is_latex_on=None):
    "Create a new room."
    user = get_user()
    if not user:
      return '<p>It looks like your session has timed out.' \
        + '  Try refreshing the page.</p>'
    if not user.can_create_room():
      return False
    
    if name and description:
      name, description = encode_unicode(name), encode_unicode(description)
      is_latex_on = (is_latex_on == 'on')
      room = db_session.query(Room).get_by(name=name)
      if name.lower() in ['new', 'register', 'index'] or room:
        return render('rooms/new', {'error_name_taken': True})
      room = Room(name=name, description=description, creator_id=user.id,
        is_latex_on=is_latex_on)
      db_session.save(room)
      db_session.save(User(name='System/notifier', room=room))
      db_session.save(User(name='System/time', room=room))
      db_session.commit()
      redirect('/%s' % room.name_encoded)
    
    return render('rooms/new')
  
  @cherrypy.expose
  def chat(self, name_encoded, user_name=None, user_password=None):
    "The chatroom.  If the user is not logged in yet, make them enter first."
    if not db_session.query(Room).get_by(name_encoded=name_encoded):
      return False
    user = get_user()
    if user and user.room and name_encoded == user.room.name_encoded:
      return render('rooms/index', {'room': user.room})
    return self.enter(name_encoded, user_name, user_password)
  
  def enter(self, name_encoded, user_name=None, user_password=None):
    "Enter the chatroom by providing username and password if necessary."
    user = get_user()
    room = db_session.query(Room).get_by(name_encoded=name_encoded)
    count = room.headcount()
    if count == 0:
      headcount = "There's no one in this room right now."
    elif count == 1:
      headcount = "There's already 1 person in this room."
    else:
      headcount = "There are %s people in this room." % count
    
    if user:
      if user.room:
        bots.notifier.left(user)
        db_session.commit()
      room = db_session.query(Room).get_by(name_encoded=name_encoded)
      user = self.admit_user(room, user)
      return self.chat(name_encoded=user.room.name_encoded)
    else:
      if user_password:
        someone = db_session.query(User).get_by(name=user_name)
        if someone.hash_password(user_password) == someone.password:
          user = self.admit_user(room, someone)
          return self.chat(name_encoded=user.room.name_encoded)
        else:
          return render('rooms/enter_password', {'room': room,
            'user_name': user_name, 'error_wrong_password': True,
            'headcount': headcount})
      elif user_name:
        someone = db_session.query(User).get_by(name=user_name)
        if someone and someone.password:
          return render('rooms/enter_password', {'room': room,
            'user_name': user_name, 'headcount': headcount})
        if someone and someone.room == room:
          return render('rooms/enter', {'room': room,
            'error_name_taken': True, 'headcount': headcount})
        if len(user_name) > 20:
          return render('rooms/enter', {'room': room,
            'error_name_length': True, 'headcount': headcount})
        if user_name.startswith('System/'):
          return render('rooms/enter', {'room': room,
            'error_invalid_name': True, 'headcount': headcount})
        if not someone:
          someone = User(name=encode_unicode(user_name))
        user = self.admit_user(room, someone)
        return self.chat(name_encoded=user.room.name_encoded)
      else:
        return render('rooms/enter', {'room': room, 'headcount': headcount})
  
  @cherrypy.expose
  def leave(self, name_encoded):
    "Leave the room."
    user = get_user()
    if user:
      if user.room and name_encoded == user.room.name_encoded:
        bots.notifier.left(user)
        user.room = None
    db_session.commit()
    cherrypy.session['User'] = user
    redirect('/')
  
  @cherrypy.expose
  def delete(self, name_encoded):
    "Delete the room."
    user = get_user()
    if user:
      room = db_session.query(Room).get_by(name_encoded=name_encoded)
      if user.can_delete_room(room):
        room.delete()
        db_session.commit()
    redirect('/')
  
  def admit_user(self, room, user):
    "Add the user to the room."
    user.room = room
    user.last_polled = datetime.datetime.now()
    user.arrival_time = datetime.datetime.now()
    db_session.commit()
    bots.notifier.entered(user)
    db_session.commit()
    cherrypy.session['User'] = user
    return user
  
