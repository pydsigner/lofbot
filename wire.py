"""
LOF BOT WIRE PROTOCOL
=====================

This module provides an tmwAthena wire protocol wrapper for the LoF bot.
"""

import socket
import struct


__all__ = ['PacketBuffer', 'PacketIn', 'PacketOut', 'PACKET_IDS', 
           'PACKET_NAMES']


packet_lengths = [
   10,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 
#0x0040
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 
    0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 
    0, 50,  3, -1, 55, 17,  3, 37, 46, -1, 23, -1,  3,108,  3,  2, 
    3, 28, 19, 11,  3, -1,  9,  5, 54, 53, 58, 60, 41,  2,  6,  6, 
#0x0080
    7,  3,  2,  2,  2,  5, 16, 12, 10,  7, 29, 23, -1, -1, -1,  0, 
    7, 22, 28,  2,  6, 30, -1, -1,  3, -1, -1,  5,  9, 17, 17,  6, 
   23,  6,  6, -1, -1, -1, -1,  8,  7,  6,  7,  4,  7,  0, -1,  6, 
    8,  8,  3,  3, -1,  6,  6, -1,  7,  6,  2,  5,  6, 44,  5,  3, 
#0x00C0
    7,  2,  6,  8,  6,  7, -1, -1, -1, -1,  3,  3,  6,  6,  2, 27, 
    3,  4,  4,  2, -1, -1,  3, -1,  6, 14,  3, -1, 28, 29, -1, -1, 
   30, 30, 26,  2,  6, 26,  3,  3,  8, 19,  5,  2,  3,  2,  2,  2, 
    3,  2,  6,  8, 21,  8,  8,  2,  2, 26,  3, -1,  6, 27, 30, 10, 
#0x0100
    2,  6,  6, 30, 79, 31, 10, 10, -1, -1,  4,  6,  6,  2, 11, -1, 
   10, 39,  4, 10, 31, 35, 10, 18,  2, 13, 15, 20, 68,  2,  3, 16, 
    6, 14, -1, -1, 21,  8,  8,  8,  8,  8,  2,  2,  3,  4,  2, -1, 
    6, 86,  6, -1, -1,  7, -1,  6,  3, 16,  4,  4,  4,  6, 24, 26, 
#0x0140
   22, 14,  6, 10, 23, 19,  6, 39,  8,  9,  6, 27, -1,  2,  6,  6, 
  110,  6, -1, -1, -1, -1, -1,  6, -1, 54, 66, 54, 90, 42,  6, 42, 
   -1, -1, -1, -1, -1, 30, -1,  3, 14,  3, 30, 10, 43, 14,186,182, 
   14, 30, 10,  3, -1,  6,106, -1,  4,  5,  4, -1,  6,  7, -1, -1, 
#0x0180
    6,  3,106, 10, 10, 34,  0,  6,  8,  4,  4,  4, 29, -1, 10,  6, 
   90, 86, 24,  6, 30,102,  9,  4,  8,  4, 14, 10,  4,  6,  2,  6, 
    3,  3, 35,  5, 11, 26, -1,  4,  4,  6, 10, 12,  6, -1,  4,  4, 
   11,  7, -1, 67, 12, 18,114,  6,  3,  6, 26, 26, 26, 26,  2,  3, 
#0x01C0
    2, 14, 10, -1, 22, 22,  4,  2, 13, 97,  0,  9,  9, 29,  6, 28, 
    8, 14, 10, 35,  6,  8,  4, 11, 54, 53, 60,  2, -1, 47, 33,  6, 
   30,  8, 34, 14,  2,  6, 26,  2, 28, 81,  6, 10, 26,  2, -1, -1, 
   -1, -1, 20, 10, 32,  9, 34, 14,  2,  6, 48, 56, -1,  4,  5, 10, 
#0x0200
   26,  0,  0,  0, 18,  0,  0,  0,  0,  0,  0, 19, 10,  0,  0,  0,
    0,  0,  0,  0,  0,  4,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0
]

# Names to ids
PACKET_IDS = dict(
  ## Client messages
  C_L_LOGIN=0x64, C_C_LOGIN=0x65, C_PICK_CHAR=0x66, 
  C_M_LOGIN=0x72, C_MAP_LOADED=0x7d, C_PING=0x7e, 
  C_GOTO=0x85, C_CHANGE_ACT=0x89, C_ATTACK=0x89, C_MSG=0x8c, 
  C_NAME_REQ=0x94, C_WHISPER=0x96, C_FACE=0x9b, 
  C_EMOTE=0xbf, C_RESPAWN=0xb2, 
  
  ## Server messages
  S_CSERV=0x69, S_LOGIN_ERROR=0x6a, S_PICK_CHAR=0x6b, 
  S_MSERV=0x71, S_CONNECTED=0x73, S_PING=0x7f, 
  S_REMOVE=0x80, S_NORM_MSG=0x8d, S_OTHER_MSG=0x8e, 
  S_NAME_RES=0x95, S_WHISPER=0x97, S_ANNOUNCE=0x9a, 
  S_XXX_USED_AFTER_DEATH=0xb0, S_XXX_USED_AFTER_DEATH2=0x01d9, 
  S_EMOTE=0xc0, 
  S_TRADE_REQ=0xe5, S_TRADE_RESP=0xe7, S_TRADE_ADD=0xe9, 
  S_TRADE_OK=0xec, S_TRADE_NO=0xee, S_TRADE_DONE=0xf0, 
  # non-standard eAthena (according to net/*/protocol.h)
  S_TRADE_ADD_RESP=0x1b1, 
  S_NAME_RES2=0x0220
)

# Inverted -- ids to names
PACKET_NAMES = dict(zip(PACKET_IDS.values(), PACKET_IDS.keys()))

# Export the packet types into the global space -- yeah. It's ugly. >:D
for packet_name, packet_id in PACKET_IDS.items():
    globals()[packet_name] = packet_id
    __all__.append(packet_name)


def pack(x, y, d):
    """
    Pack an x, y location and a direction into 3 bytes.
    """
    def cast(n):
        return n % 256
    def hibyte(n):
        return cast(n >> 8)
    
    t = x << 6
    b0 = hibyte(t)
    b1 = cast(t)
    t = y << 4
    b1 |= hibyte(t)
    b2 = cast(t) | d
    
    return b0, b1, b2


def unpack(b0, b1, b2):
    """
    Unpack an (x, y, direction) set done up in the manner above.
    """
    def mkword(l, h):
        return (l % 256) | ((h % 256) << 8)
    
    x = mkword(b1 & 0xc0, b0 & 0xff) >> 6
    y = mkword(b2 & 0xf0, b1 & 0x3f) >> 4
    d = b2 & 0xf
    
    return x, y, d


class PacketIn(object):
    
    """
    An in-coming packet.
    """
    
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.packet_id = self.int16()
    
    def __eq__(self, other):
        """
        Compare this message's ID to another ID.
        """
        return self.packet_id == other
    
    def parse(self):
        """
        Parse the message according to its type.
        """
        if self == S_WHISPER:
            self.skip(2)
            return self.string(24), self.string()
        
        elif self == S_NORM_MSG:
            # Unknown bytes -- something, and then what seems to always be 0
            self.skip(2)
            # Acc ID, Message
            return (self.int32(), self.string())
        
        elif self == S_OTHER_MSG:
            self.skip(2)
            return (self.string(),)
        
        elif self == S_EMOTE:
            # Being ID, Emote ID
            return self.int32(), self.int8()
        
        elif self == S_CSERV:
            self.skip(2)
            id1, accid, id2 = self.int32(), self.int32(), self.int32()
            # Server name, time, etc
            self.skip(30)
            sex = self.int8()
            ip = self.ip()
            port = self.int16()
            return id1, accid, id2, sex, ip, port
        
        elif self == S_MSERV:
            charid = self.int32()
            # Break off the trailing .gat or whatever
            mapname = self.string(16).split('.')[0]
            ip = self.ip()
            port = self.int16()
            return charid, ip, port
        
        elif self == S_CONNECTED:
            self.int32()    # server tick
            # There is nothing else worthwhile -- 
            # see GameHandler::processMapLogin() @ src/net/ea/gamehandler.cpp 
            # in the Manaplus source
            return self.coords()
        
        elif self == S_NAME_RES:
            being_id = self.int32()
            name = self.string(24)
            return being_id, name
        
        elif self == S_NAME_RES2:
            size = self.int16()
            being_id = self.int32()
            name = self.string(size - 8)
            return being_id, name
        
        elif self == S_REMOVE:
            # being id; type, death if =1 else just remove
            return (self.int32(), self.int8() == 1)
        
        elif self == S_XXX_USED_AFTER_DEATH:
            # Finish this later...
            return ()
        
        elif self == S_PING:
            # Look this up -- this isn't likely right
            return (self.string())
    
    def skip(self, n):
        self.pos += n
    
    def int8(self):
        """
        Get an 8-bit integer.
        """
        res = ord(self.data[self.pos])
        self.pos += 1
        return res
    
    def int16(self):
        """
        Get a 16-bit integer.
        """
        opos = self.pos
        self.pos += 2
        return struct.unpack('<H', self.data[opos:self.pos])[0]
    
    def int32(self):
        """
        Get a 32-bit integer.
        """
        opos = self.pos
        self.pos += 4
        return struct.unpack('<L', self.data[opos:self.pos])[0]
    
    def ip(self):
        """
        Get a 32-bit-packed IP.
        """
        opos = self.pos
        self.pos += 4
        return socket.inet_ntoa(self.data[opos:self.pos])
    
    def string(self, size=None):
        """
        Get a (possibly padded) string of a particular size.
        """
        if size is None:
            res = self.data[self.pos:]
            self.pos = len(self.data)
        else:
            opos = self.pos
            self.pos += size
            res = self.data[opos:self.pos]
        
        return res.rstrip('\0')
    
    def coords(self):
        opos = self.pos
        self.pos += 3
        return unpack(*struct.unpack('<BBB', self.data[opos:self.pos]))


class PacketOut(object):
    
    """
    An out-going packet.
    """
    
    def __init__(self, packet_id, *args):
        self.packet_id = packet_id
        self.data = struct.pack('<H', packet_id)
        # Allow cutting down on code; 
        # This is the intended use pattern, after all.
        if args:
            self.fill(*args)
    
    def __eq__(self, other):
        """
        Compare this message's ID to the given ID.
        """
        return self.packet_id == other
    
    def __str__(self):
        return self.data
    
    def fill(self, *args):
        """
        Fill in all the parts of the message.
        """
        if self == C_L_LOGIN:
            acc, pswd = args
            # Client version. Need 1 currently.
            self.int32(0)
            self.string(acc, 24)
            self.string(pswd, 24)
            # ManaPlus has this "second version info" repurposed as an ability 
            # mask, but we don't support anything they put there.
            self.int8(3)
        
        elif self == C_C_LOGIN:
            accid, id1, id2, sex = args
            self.int32(accid)
            self.int32(id1)
            self.int32(id2)
            # This is the client major version that we are emulating (1.x)
            self.int16(1)
            self.int8(sex)
        
        elif self == C_PICK_CHAR:
            # Must do this manually since we cannot rely on unpacking to do it 
            # for us
            assert len(args) == 1, 'This message only has one blank!'
            self.int8(args[0])
        
        elif self == C_M_LOGIN:
            accid, charid, id1, id2, sex = args
            self.int32(accid)
            self.int32(charid)
            self.int32(id1)
            self.int32(id2)
            self.int8(sex)
        
        elif self == C_CHANGE_ACT and len(args) == 1:
            # Attack is the same id
            self.int32(0)
            self.int8(args[0])
        
        elif self == C_MSG:
            assert len(args) == 1, 'This message only has one blank!'
            self.int16(len(args[0]) + 4)
            self.string(args[0])
        
        elif self == C_WHISPER:
            nick, msg = args
            self.int16(len(msg) + 28)
            try:
                self.string(nick, 24)
            except Exception:
                print(' '.join('%02x' % ord(c) for c in self.data))
                print(' '.join('%02x' % ord(c) for c in nick))
                raise
            self.string(msg)
        
        elif self == C_FACE:
            assert len(args) == 1, 'This message only has one blank!'
            self.int16(0)
            self.int8(args[0])
        
        elif self == C_EMOTE:
            assert len(args) == 1, 'This message only has one blank!'
            self.int8(args[0])
        
        elif self == C_RESPAWN:
            assert not args, 'This message does not have any blanks!'
            self.int8(0)
        
        elif self == C_ATTACK:
            being_id, keep = args
            self.int32(being_id)
            self.int8(7 if keep else 0)
            print(repr(self.data))
        
        elif self == C_GOTO:
            self.coords(*args)
        
        elif self == C_NAME_REQ:
            assert len(args) == 1, 'This message only has one blank!'
            self.int32(args[0])
        
        else:
            # That is, or we know not how to use this message ID...
            assert not args, 'This message does not have any blanks!'
    
    def send(self, conn):
        conn.sendall(self.data)
    
    def int8(self, i):
        self.data += chr(i)
    
    def int16(self, i):
        self.data += struct.pack('<H', i)
    
    def int32(self, i):
        self.data += struct.pack('<L', i)
    
    def string(self, s, size=None):
        if size is not None:
            s = s.ljust(size, '\0')
        if isinstance(s, unicode):
            # Have to do this to avoid explosions from command types > 127
            s = s.encode()
        self.data += s
    
    def coords(self, x, y, d=-1):
        self.data += struct.pack('<BBB', *pack(x, y, d))


class PacketBuffer(object):
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.buff = ''

    def feed(self, data):
        self.buff += data

    def drop(self, count):
        self.buff = self.buff[count:]

    def __iter__(self):
        return self

    def next(self):
        if len(self.buff) < 2:
            raise StopIteration

        pkttype = struct.unpack('<H', self.buff[:2])[0]
        assert pkttype < len(packet_lengths)
        assert packet_lengths[pkttype] != 0
        if packet_lengths[pkttype] < 0:
            if len(self.buff) < 4:
                raise StopIteration
            pktlen = struct.unpack('<H', self.buff[2:4])[0]
            assert pktlen >= 4
        else:
            pktlen = packet_lengths[pkttype]

        if len(self.buff) < pktlen:
            raise StopIteration
        packet = self.buff[:pktlen]
        self.buff = self.buff[pktlen:]
        return PacketIn(packet)
