import unittest
import models

class ModelsTester(unittest.TestCase):
    
    def setUp(self):
        models.create_all()
    
    def test_add_a_user_to_a_room(self):
        al = models.User(nick=u'al', color=(0, 0, 0))
        room = models.Room(name=u'Secret Treehouse')
        room.add_user(al)
        models.session.commit()
        self.assert_(al in room.users)
        self.assert_(room in al.rooms)

if __name__ == '__main__':
    unittest.main()