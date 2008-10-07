import unittest
from models import *

class ModelsTester(unittest.TestCase):
    
    def setUp(self):
        create_all()
    
    def test_add_a_user_to_a_room(self):
        al = User(nick=u'al', color=(0, 0, 0))
        room = Room(name=u'Secret Treehouse')
        room.add_user(al)
        session.commit()
        self.assert_(al in room.users)
        self.assert_(room in al.rooms)
    
    def test_urlize_room_name(self):
        room = Room(name=u'Secret Treehouse!')
        session.commit()
        self.assertEqual(room.name_, 'secret-treehouse')

if __name__ == '__main__':
    unittest.main()