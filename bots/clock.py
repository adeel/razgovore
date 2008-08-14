import datetime

from .models import Room, Message, User
from .models import session as db_session

def time(room):
  bot = db_session.query(User).filter_by(
    name=u'System/time', room=room).first()
  if not bot:
    bot = User(name=u'System/time', room=room)
    db_session.save(bot)
  freq, now = 5, datetime.datetime.now()
  if now.minute % freq == 0:
    last = now.replace(minute=(now.minute - now.minute % freq),
      second=0, microsecond=0)
    systime = db_session.query(Message).filter_by(
      room=room, user=bot, date=last).all()
    if not systime:
      db_session.save(Message(room=room,
        user=bot, date=last, text=u''))
  db_session.commit()
  return True
