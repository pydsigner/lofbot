import sqlite3
import os

from sql import *


db_loc = os.path.join(os.path.dirname(__file__), 'database.sqlite')


def connector():
    conn = sqlite3.connect(db_loc)
    conn.text_factory = str
    return conn

init(connector, sqlite3.Row)


class Listing(BaseMapper):
    max_pop = 100
    
    tablename = 'listing'
    # word: one like "at" or "for", used in a phrase like "50 shoes for 500gp"
    columns = (Integer('price'), Integer('quantity'), 
               VarChar('seller', 30), VarChar('item', 40), VarChar('word', 10))
    
    def add(self):
        if not self._in_db:
            current = list(self.all())
            if len(current) >= self.max_pop:
                current[0].remove()
            BaseMapper.add(self)
            get_connection().commit()
    
    def remove(self):
        BaseMapper.remove(self)
        get_connection().commit()


class Message(BaseMapper):
    tablename = 'message'
    columns = (VarChar('text', 200), VarChar('recipient', 30))


class Listener(BaseMapper):
    tablename = 'listener'
    columns = (VarChar('listener', 30), Integer('listening'))


class Price(BaseMapper):
    tablename = 'price'
    columns = (VarChar('item', 40), Integer('quantity'), Integer('price'))
    
    @classmethod
    def clear_table(cls):
        return get_cursor().execute('delete from %s' % cls.tablename)


class Sighting(BaseMapper):
    tablename = 'sighting'
    columns = (VarChar('player', 30), Integer('time'), Integer('count'))


# For persisting singletons
class SingleStat(BaseMapper):
    tablename = 'singlestat'
    columns = (VarChar('ref', 20), Text('data'))


class ListenPref(BaseMapper):
    tablename = 'listenpref'


class Character(BaseMapper):
    tablename = 'character'
    columns = (VarChar('alias', 30),    # Properly capitalized character name
               VarChar('handle', 30),   # Lowercase character name
               VarChar('name', 30),     # Properly capitalized master name
               Integer('account'))


initialize_database((Listing, Message, Listener, Price, Sighting, SingleStat, 
                     Character))
