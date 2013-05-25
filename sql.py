"""
MicrORM+ is a mini ORM with mega features. It is fully SQLite3 thread-safe, and 
also supports MySQL for larger installations. Compared to SQLAlchemy, MicrORM+ 
is much smaller, at less than 350 lines; much less magical; and, with almost 
all functionality in one well-documented class, much more obvious and readable. 
Plus, MicrORM+'s interface is quite similar to that of Django's DB, and easier 
to use than SQLAchemy's powerful but esoteric codebase.

----------------------------------------
Copyright (c) 2012-2013 Daniel Foerster/Dsigner Software <pydsigner@gmail.com> 
and released under the LGPL, version 3 or later.
"""

__version__ = '1.4.1'


import sys
import os

try:
    from thread import get_ident
except ImportError:
    from _thread import get_ident


__all__ = ['init', 'get_cursor', 'get_connection', 'close_connection', 
           'commit_and_close', 'initialize_database', 'comp', 'ID', 'Integer', 
           'Float', 'VarChar', 'Text', 'DateTime', 'BaseMapper']


_cursor_pool = {}
_connector = None
_dictify = None


def init(connector, converter):
    """
    Set the connection generator and the row2dict-like converter. Must be 
    called before accessing the database.
    """
    global _connector, _dictify
    _connector = connector
    _dictify = converter


def get_cursor():
    """
    Get or create the cursor for this thread.
    """
    tid = get_ident()
    if tid in _cursor_pool:
        return _cursor_pool[tid]
    
    conn = _connector()
    curs = conn.cursor()
    _cursor_pool[tid] = curs
    return curs


def get_connection():
    """
    Get or create the connection for this thread.
    """
    return get_cursor().connection


def close_connection():
    """
    Close the connection for this thread, if there is one. It's a Good Idea for 
    the threads of long-running processes to close their database connections 
    after finishing their actual DB communications (setting column values, 
    add()ing, get()ing, remove()ing, and filter()ing all access the database) 
    to avoid having a cache full of connections that will never be used again. 
    Although these connections may be reused in a different thread with the 
    same identification, this is unlikely, as many possible thread IDs exist.
    """
    tid = get_ident()
    if tid in _cursor_pool:
        _cursor_pool.pop(tid).connection.close()


def commit_and_close():
    """
    Same as `close_connection()` above, but commits changes first.
    """
    tid = get_ident()
    if tid in _cursor_pool:
        c = _cursor_pool.pop(tid).connection
        c.commit()
        c.close()


def initialize_database(classes):
    """
    Create all the tables required for `classes`.
    """
    for cls in classes:
        table = cls.tablename
        try:
            mk = cls._mk_create()
            get_cursor().execute('create table if not exists %s (%s)' %
                                 (table, mk))
        except Exception as e:
            sys.excepthook(*sys.exc_info())
            # What!
            return False
    return True


def comp(col, comp='='):
    if '?' in col:
        return col
    return '%s%s?' % (col, comp)


##### Column Types  ##########


class ID(object):
    def __str__(self):
        return 'id integer primary key'


class Integer(object):
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return '%s integer' % self.name


class Float(object):
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return '%s real' % self.name


class VarChar(object):
    def __init__(self, name, size):
        self.name = name
        self.size = size
    
    def __str__(self):
        return '%s varchar(%s)' % (self.name, self.size)


class Text(object):
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return '%s text' % self.name


class DateTime(object):
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return '%s datetime' % self.name


##### Main Class #############


class BaseMapper(object):
    
    """
    Base class for row/instance mappers. One-word row names that must not be 
    used:
      id
      columns
      tablename
      remove
      save
      filter
      get
      all
    It is hoped that no one needs such names as `_filter` or `get_items`. Note 
    that `id` is created automatically, as it is required.
    """
    
    # Internals
    _col_prefix = '_col_'
    _have_built = False
    
    # Override these
    tablename = None
    columns = ()
    
    def __init__(self, row):
        """
        Sets information from dict-like object `row`.
        """
        cols = row.keys()
        self._all_cols = list(cols)
        
        self._in_db = 'id' in row.keys()
        
        if not self._have_built:
            self._build_properties()
            self._have_built = True
        
        for col in cols:
            self._set_property(col, row[col])
    
    def __repr__(self):
        name = self.__class__.__name__
        vals = ', '.join('%s=%r' % (col, self[col]) for col in self._all_cols)
        return '<%s %s>' % (name, vals)
    
    def __getitem__(self, x):
        """
        obj['x'] <==> obj.x
        """
        return getattr(self, x)
    
    def __setitem__(self, x, val):
        """
        obj['x'] = y <==> obj.x = y
        """
        setattr(self, x, val)
    
    ### Access #########
    
    def get_keys(self):
        """
        Get an tuple version of the column list.
        """
        return tuple(self._all_cols)
    
    def get_values(self):
        """
        Get an tuple of this row's values.
        """
        return tuple(getattr(self, col) for col in self._all_cols)
    
    def get_items(self):
        """
        Get an tuple of the (column, value) pairs of this row.
        """
        return tuple((col, getattr(self, col)) for col in self._all_cols)
    
    ### Internals ######
    
    @classmethod
    def _add_property(cls, col):
        """
        Build and cache the property accessor for a particular column.
        """
        mcol = cls._col_prefix + col
        
        @property
        def prop(self):
            return getattr(self, mcol)
        
        if col != 'id':
            @prop.setter
            def prop(self, val):
                setattr(self, mcol, val)
                cmd = 'update %s set %s=? where id=?' % (cls.tablename, col)
                get_cursor().execute(cmd, (val, self.id))
        
        setattr(cls, col, prop)
    
    def _build_properties(self):
        """
        Create all appropriate properties for this class.
        """
        self._add_property('id')
        for col in self.get_keys():
            if col != 'id':
                self._add_property(col)
    
    def _set_property(self, col, val):
        """
        Initialize the hidden value of a column.
        """
        setattr(self, self._col_prefix + col, val)
    
    @classmethod
    def _mk_create(cls):
        """
        Build the column definition for this table. Used internally.
        """
        cols = (ID(),)
        cols += cls.columns
        return ', '.join(str(col) for col in cols)
    
    @classmethod
    def _filter(cls, **filters):
        """
        Get the raw cursor result for a query. Used internally.
        """
        start = 'select * from %s where ' % cls.tablename
        cont = ' and '.join(comp(k) for k in filters)
        vals = tuple(filters.values())
        return get_cursor().execute(start + cont, vals)
    
    ### Class-wides ####
    
    @classmethod
    def count(cls, **filters):
        base = 'select count(id) from %s' % cls.tablename
        if filters:
            base += ' where ' + ' and '.join(comp(k) for k in filters)
            vals = tuple(filters.values())
            res = get_cursor().execute(base, vals)
        else:
            res = get_cursor().execute(base)
        return res.fetchone()[0]
    
    @classmethod
    def all(cls):
        curs = get_cursor().execute('select * from %s' % cls.tablename)
        return (cls(_dictify(curs, row)) for row in curs)
    
    @classmethod
    def filter(cls, **filters):
        """
        Get all the results for **filters.
        """
        curs = cls._filter(**filters)
        return (cls(_dictify(curs, row)) for row in curs)
    
    @classmethod
    def get(cls, **filters):
        """
        Get exactly one result for **filters or None.
        """
        curs = cls._filter(**filters)
        res = curs.fetchone()
        if res is None:
            return
        return cls(_dictify(curs, res))
    
    ### Save/remove #####
    
    def add(self):
        """
        Create the row in the DB if it does not exist already. Returns the 
        resulting cursor object if the row was added, otherwise None.
        """
        if not self._in_db:
            keys = self._all_cols
            
            to_insert = ', '.join(keys)
            qmarks = ', '.join('?' for i in range(len(keys)))
            
            cmd = 'insert into %s(%s) values (%s)'
            cmd %= (self.tablename, to_insert, qmarks)
            
            res = get_cursor().execute(cmd, self.get_values())
            
            self._set_property('id', res.lastrowid)
            self._all_cols.insert(0, 'id')
            self._in_db = True
            
            return res
    
    def remove(self):
        """
        Delete the row out of the database. Cannot be reversed using save(), 
        but may be canceled with a rollback. Returns the resulting cursor 
        object if the row was removed, otherwise None.
        """
        id = getattr(self, self._col_prefix + 'id', None)
        if id is None:
            return
        
        cmd = 'delete from %s where id=?' % self.tablename
        return get_cursor().execute(cmd, (id,))

