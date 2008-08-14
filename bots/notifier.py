import datetime

from .models import Room, Message, User
from .models import session as db_session

def entered(user):
  room = db_session.query(Room).filter_by(id=user.room.id).first()
  notifier = db_session.query(User).filter_by(name='System/notifier',
    room=room).first()
  if not notifier:
    notifer = User(name='System/notifier', room=room)
    db_session.save(notifier)
  db_session.save(Message(user=notifier, room=room, date=user.arrival_time,
    text="%s has entered the room." % user.name))
  db_session.commit()
  return True

def left(user):
  room = db_session.query(Room).filter_by(id=user.room.id).first()
  notifier = db_session.query(User).filter_by(
    name='System/notifier', room=room).first()
  if not notifier:
    notifier = User(name='System/notifier', room=room)
    db_session.save(notifier)
  db_session.save(Message(user=notifier, room=room,
    text="%s left." % user.name))
  return True
