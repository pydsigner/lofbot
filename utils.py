def isection(itr, size):
    """
    Goes through `itr` and splits it up into chunks of `size`. `itr` must be 
    subscriptable.
    """
    while itr:
        yield itr[:size]
        itr = itr[size:]


def rotate(itr, places):
    """
    Rotate `itr` `places` to the left. `itr` must be subscriptable. A negative 
    value for `places` will cause rotation to the right.
    """
    return itr[places:] + itr[:places]


class Vector(object):
    
    """
    A basic vector class. Supports addition and subtraction, indexing, and 
    iteration.
    """
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __repr__(self):
        return 'Vector(%s, %s)' % (self.x, self.y)
    
    ## Iteration
    
    def __len__(self):
        return 2
    
    def __iter__(self):
        return iter((self.x, self.y))
    
    ## Indexing
    
    def __getitem__(self, i):
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        else:
            raise IndexError('Vector index out of range')
    
    def __setitem__(self, i, val):
        if i == 0:
            self.x = val
        elif i == 1:
            self.y = val
        else:
            raise IndexError('Vector index out of range')
    
    ## Operations
    
    def __add__(self, other):
        return Vector(self.x + other[0], self.y + other[1])
    
    def __iadd__(self, other):
        self.x += other[0]
        self.y += other[1]
        return self
    
    def __sub__(self, other):
        return Vector(self.x - other[0], self.y - other[1])
    
    def __isub__(self, other):
        self.x -= other[0]
        self.y -= other[1]
        return self
