#! /usr/bin/env python
"""
LOF BOT
=======

LoF Bot is an OOP tmwAthena bot controlled by whispers, programmed specifically 
for the Land of Fire server.

ACKNOWLEDGEMENTS
++++++++++++++++

This bot is based on the original WhisperBot by gnurfk. Many thanks for that 
invaluable starting point!

Most of the protocol implemented in this bot has been translated from the C++ 
code of Manaplus. Many thanks for a structured (though dense in and of itself) 
coding of this dense protocol! 
Note that all references to C++ code are to the Manaplus codebase, and can be 
looked up in the src directory of the Manaplus source distribution.

LICENSING
+++++++++

Copyright (c) 2012-2015 Daniel Foerster/Dsigner Software <pydsigner@gmail.com> 
and released under the Apache License, version 2.0.
"""

__version__ = '2.2.1'


import sys
import time
import socket
socket.setdefaulttimeout(120)

from taskit.threaded import threaded, allocate_lock
from taskit.log import *

from utils import Vector
from wire import *
import config
import commands


### Constants

PACKET = 'PDUMP'


### Specialized logger


class LOFLogNode(LoggerNode):
    def make_client_log(self, client):
        def log(level, msg):
            self.__call__(level, msg, client.account)
        return log
    
    # I really didn't want to copy-hack this bit from taskit.log, but this is 
    # currently very much a special case sub-class
    def __call__(self, importance, msg, title=''):
        """
        Log message `' '.join(msg)` with `importance` importance.
        """
        ## Quick-cache for speed... really!
        allowed = self.allowed
        ## Ignore dis-allowed importances.
        if allowed is not None and importance not in allowed:
            return False
        
        for logger in self.children:
            # Yes, we're completely redoing this just to change this call. 
            # TODO: Something to think about for the next version of taskit.log...
            ## .__call__() is much faster for classes, but has bad aesthetics...
            logger(importance, msg, title)
        
        return True


class LOFFileLog(LOFLogNode):
    def __init__(self, fobj, allowed=None, flush=5, children=()):
        """
        fobj  -- The file-like object to be written to.
        flush -- How many lines to write before flush()ing if greater than 
                 zero, otherwise flush will not be called and the close() 
                 method will have to be used to save data.
        """
        LoggerNode.__init__(self, children, allowed)
        
        self.fobj = fobj
        self.flush = flush
        # Set up the flush counter.
        self.count = 0
    
    def _format(self, level, msg, title):
        level = {INFO: 'info:',
                 ERROR: 'ERROR',
                 IMPORTANT: '<IMP>'
                 }.get(level, level.lower()[:5])
        
        t = time.strftime('%H:%M:%S %d.%m.%y')
        
        return '%s  %s%s\t%s\n' % (t, title.ljust(15), level, msg)
    
    # I really didn't want to copy-hack this bit from taskit.log, but this is 
    # currently very much a special case sub-class
    def __call__(self, importance, msg, title=''):
        ## Let the super-class take care of the children...
        res = LOFLogNode.__call__(self, importance, msg, title)
        
        ## If we aren't logging this event... well... then don't!
        if not res:
            return False
        
        # Yes, we're completely redoing this just to change this call. 
        # TODO: Something to think about for the next version of taskit.log...
        ## Then take care of our handling.
        self.fobj.write(self._format(importance, msg, title))
        if self.flush:
            self.count += 1
            if self.count == self.flush:
                self.fobj.flush()
                self.count = 0
        
        return True
    
    def close(self):
        """
        Close the underlying file. Does not close child loggers; see 
        `close_children()`.
        """
        self.fobj.close()


### Base client

class TMWAClient(object):
    
    """
    The tmwAthena base client. Powered by a mainloop with callbacks.
    """
    
    def __init__(self, server, port, account, pswd, same_ip=False, cindex=0):
        self.server = server
        self.port = port
        self.account = account
        self.pswd = pswd
        self.same_ip = same_ip
        self.cindex = cindex
        self.packet_cbs = dict(
          S_NORM_MSG=self.got_msg, S_EMOTE=self.got_emote, 
          S_OTHER_MSG=self.got_server, S_WHISPER=self.got_whisper, 
          S_NAME_RES=self.got_name_res, S_NAME_RES2=self.got_name_res, 
          S_REMOVE=self.got_remove, S_XXX_USED_AFTER_DEATH=self.got_xxx_ad,
          S_PING=self.got_ping)
        
        # Personalize the logger
        self.log = self.log.make_client_log(self)
    
    def _handle_packet(self, packet):
        name = PACKET_NAMES.get(packet.packet_id)
        parsed = packet.parse()
        if parsed:
            cb = self.packet_cbs.get(name)
            if cb:
                cb(*parsed)
        else:
            self.got_unknown(packet)
    
    #### Connect
    
    def connect(self):
        """
        Does protocol with the server to get all the way into the game. 
        Returns the boolean success of the connection.
        """
        
        self.ready = False
        
        self.buff = PacketBuffer()
        
        self.log(IMPORTANT, 'Connecting to the login server...')
        
        try:
            login = socket.socket()
            login.connect((self.server, self.port))
        except socket.error:
            log(ERROR, 'Could not connect to the login server!')
            return False
        
        self.log(IMPORTANT, 'Connected to the login server!')
        
        p = PacketOut(C_L_LOGIN, self.account, self.pswd)
        p.send(login)
        
        charip = charport = None
        
        while True:
            data = login.recv(2048)
            if not data:
                break
            self.buff.feed(data)
            for packet in self.buff:
                if packet == S_LOGIN_ERROR:
                    self.log(ERROR, 'Could not log in!')
                    return False
                elif packet == S_CSERV:
                    self.log(IMPORTANT, 'Successfully logged in!')
                    id1, accid, id2, sex, charip, charport = packet.parse()
                    login.close()
                    break
            if charip:
                break
        
        if not charport:
            return False
        
        self.buff.reset()
        
        charserv = (self.server if self.same_ip else charip, charport)
        self.log(IMPORTANT, 'Connecting to the character server (%s:%s)...' % charserv)
        
        try:
            char = socket.socket()
            char.connect(charserv)
        except socket.error as e:
            log(ERROR, 'Could not connect to the character server (%s)!' % e)
            return False
        
        p = PacketOut(C_C_LOGIN, accid, id1, id2, sex)
        p.send(char)
        
        # What's this?
        char.recv(4)
        
        mapip = mapport = None
        
        while True:
            data = char.recv(2048)
            if not data:
                break
            self.buff.feed(data)
            for packet in self.buff:
                if packet == S_PICK_CHAR:
                    self.log(IMPORTANT, 'Picking character...')
                    PacketOut(C_PICK_CHAR, self.cindex).send(char)
                elif packet == S_MSERV:
                    self.log(IMPORTANT, 'Received MServ information.')
                    charid, mapip, mapport = packet.parse()
                    char.close()
                    break
            if mapip:
                break

        if not mapport:
            return False
        
        self.buff.reset()
        
        self.log(IMPORTANT, 'Connecting to the map server...')
        
        try:
            mapserv = socket.socket()
            mapserv.connect((self.server if self.same_ip else mapip, mapport))
        except socket.error:
            self.log(ERROR, 'Could not connect to the map server!')
            return False
        
        p = PacketOut(C_M_LOGIN, accid, charid, id1, id2, sex)
        p.send(mapserv)
        
        # Again, what are we trashing?
        mapserv.recv(4)
        
        done = False
        pos = Vector(0, 0)
        while not done:
            data = mapserv.recv(2024)
            if not data:
                break
            self.buff.feed(data)
            for packet in self.buff:
                if packet == S_CONNECTED:
                    self.log(IMPORTANT, 'Successfully connected!')
                    x, y, d = packet.parse()
                    pos = Vector(x, y)
                    PacketOut(C_MAP_LOADED).send(mapserv)
                    done = True
                    break
        
        self.conn = mapserv
        
        self.pos = pos
        self.account_id = accid
        self.ready = True
        self.done = False
        
        return True
    
    #### Mainloop
    
    def main(self):
        while not self.done:
            data = self.conn.recv(2024)
            if not data:
                break
            self.buff.feed(data)
            for packet in self.buff:
                threaded(self._handle_packet, (packet,))
    
    #### Commands
    
    def sit(self):
        """
        Sit down.
        """
        PacketOut(C_CHANGE_ACT, 2).send(self.conn)
    
    def stand(self):
        """
        Stand up.
        """
        PacketOut(C_CHANGE_ACT, 3).send(self.conn)
    
    def whisper(self, nick, msg):
        """
        Send whisper `msg` to `nick`.
        """
        PacketOut(C_WHISPER, nick, msg).send(self.conn)
    
    def msg(self, msg):
        """
        Send standard message `msg`.
        """
        msg = '%s : %s' % (self.account, msg)
        PacketOut(C_MSG, msg).send(self.conn)
    
    _e = [
      # Standard TMW (but server-side modifiable) emotes
      (1, 'yuck', 'gross', 'bleh'), (2, 'O.o', 'O_o', 'surprised', '0_o'), 
      (3, ':-)', 'smile', 'happy', ':)'), (4, ':-(', ':(', 'sad'), 
      (5, '>:D', 'evil'), (6, ';-)', ';)', 'wink'), 
      (7, 'angelic', 'angel', 'halo'), (8, 'blush', 'embarrassed'), 
      (9, ':P', ':p'), (10, '8D', ':D', 'grin'), (11, 'upset'), 
      (12, 'perturbed', 'troubled'), (13, '(...)', '...'), (14, 'speech'), 
      # LoF-specific emotes
      (18, '>XD', 'evil grin'), (19, 'snowman', 'frosty'), 
      (20, 'yum', 'food', 'hungry'),
      
      # ManaPlus emotes
      (101, 'kat', 'kitty', 'cat', ':3'),(102, 'XD', 'lol', 'laugh', '><'), 
      (103, 'cheerful', '^.^'), (104, 'love'), (105, 'money'), 
      # The first representation here is intended only for the id-to-text.
      (106, 'ZzZzzZ', 'zzz', 'sleep', 'tired', 'sleepy'), 
      (107, 'rest', 'relax', 'u.u'), (108, '-.-', 'bothered'), 
      (109, 'afraid', 'frightened', 'fright', ':o', 'scared', 'fear'), 
      (110, 'x_x', 'xx', 'dead'), (111, 'suspicious'), (112, 'melancholy'), 
      (113, 'facepalm', 'palm'), (114, 'angry', 'bite'), (115, 'headache'), 
      (116, 'purple'), (117, '(@#!)', 'swear'), (118, 'heart'), (119, 'blank'), 
      (120, 'pumpkin'), (121, 'vicious', 'deadly'), (122, 'epic'), 
      (123, 'geek'), (124, 'mimi', 'shy'), (125, 'alien', 'bug'), 
      (126, 'troll'), (127, 'pain', 'metal'), 
      (128, ':\'(', 'tears', 'cry', 'crying')
    ]
    
    emote_id_db = {}
    emote_name_db = {}
    
    for _etup in _e:
        _eid = _etup[0]
        # The first name is the preferred translation to be used for textual 
        # representations.
        emote_name_db[_eid] = _etup[1]
        # These names will be translated into the correct emote by `emote()`.
        for _name in _etup[1:]:
            emote_id_db[_name] = _eid
    
    # Clean up namespace
    del _e, _etup, _eid, _name
    
    def emote(self, emote_id):
        """
        Do an emote.
        """
        e = str(emote_id)
        e = int(self.emote_id_db.get(e.lower(), e))
        
        PacketOut(C_EMOTE, e).send(self.conn)
    
    directions = dict(w=0, s=1, e=8, n=4)
    
    def face(self, d):
        """
        Face in the given direction.
        """
        
        d = int(self.directions.get(str(d)[0].lower(), d))
        
        PacketOut(C_FACE, d).send(self.conn)
    
    def goto(self, x, y, d=6):
        """
        Go to the given location. `d` doesn't seem to affect anything.
        """
        p = PacketOut(C_GOTO, x, y, d)
        p.send(self.conn)
    
    def respawn(self):
        """
        Respawn. TESTING!
        """
        p = PacketOut(C_RESPAWN)
        p.fill()
        p.send(self.conn)
    
    def attack(self, being_id, keep):
        """
        Attack something. TESTING!
        """
        p = PacketOut(C_ATTACK, being_id, keep)
        p.send(self.conn)
    
    def whois(self, being_id):
        """
        Ask for the name corresponding to the given being id.
        """
        p = PacketOut(C_NAME_REQ, being_id)
        p.send(self.conn)
        
    
    #### Callbacks
    
    def got_whisper(self, whom, msg):
        """
        Callback for whispers
        """
    
    def got_server(self, msg):
        """
        Callback for server messages
        """
    
    def got_msg(self, being_id, msg):
        """
        Callback for standard character speeches
        """
    
    def got_emote(self, being_id, emote_id):
        """
        Callback for emotes
        """
    
    def got_name_res(self, being_id, name):
        """
        Callback for name query results
        """
    
    def got_remove(self, being_id, died):
        """
        Callback for being removals
        """
    
    def got_ping(self, *args):
        """
        Callback for ping responses
        """
    
    def got_xxx_ad(self, *args):
        pass
    def got_xxx_ad2(self, *args):
        pass
    
    def got_unknown(self, packet):
        """
        Callback for unknown packets (e.g. for research and learning purposes)
        """
    
    ### Class-wide setup
    
    @classmethod
    def set_log(cls, log):
        """
        Set the logging agent for this client class.
        """
        cls.log = log


### Base for all LoF bots

class BotBase(TMWAClient):
    
    """
    Core functionality for bots using the mod_command interface.
    """
    
    is_slave = False
    
    ### Mod handler inserts
    
    handler_names = ['emote', 'msg', 'server', 'name_res', 'remove', 'ping', 
                     'unknown']
    _generated_handlers = False
    
    
    def __init__(self, *args, **kw):
        TMWAClient.__init__(self, *args, **kw)
        
        # Initialize channel
        self.channel = 'main'
        
        # Yup, that's this class. We essentially have a work-around here that 
        # allows us not to define these methods manually. Only do it once.
        if not BotBase._generated_handlers:
            for name in BotBase.handler_names:
                BotBase._mk_handler(name)
            BotBase._generated_handlers = True
        
        # Setup the mod_commands structure
        commands.setup_commands(self)
    
    ### Command setup
    
    @classmethod
    def _mk_handler(cls, name):
        def doer(self, *args, **kw):
            for h in self.handlers[name]:
                h(self, *args, **kw)
        setattr(cls, 'got_' + name, doer)
    
    def reset_commands(self):
        """
        Reset the command bank. Used by `init_commands` in `commands.py`.
        """
        self.required_mods = set()
        self.installed_mods = {}
        self.filters = []
        self.periodic_cbs = []
        self.command_db = {}
        self.help_db = {}
        self.handlers = {name: [] for name in self.handler_names}
        self.cb_404 = BotBase._basic_404
    
    def _basic_404(self, nick, cmd):
        return 'The `%s` command is not supported by this bot.' % cmd
    
    ### Controllers
    
    def main(self):
        if self.periodic_cbs:
            threaded(self.periodic, ())
        TMWAClient.main(self)
    
    def periodic(self):
        while 1:
            start = time.time()
            
            for cb in self.periodic_cbs:
                try:
                    cb(self)
                except Exception:
                    sys.excepthook(*sys.exc_info())
            
            # I'm willing to take a nanosec or two of error for some 
            # self-explanatory variable names...
            finish = time.time()
            delta = finish - start
            # 12 seconds = 5 runs a minute
            adjusted = 12 - delta
            if adjusted < 0:
                log(IMPORTANT, 'Periodic loop too loaded for sleep period!')
                log(IMPORTANT, '(time taken: %s)' % delta)
            else:
                time.sleep(adjusted)
    
    def got_whisper(self, whom, msg):
        log(INFO, '%s: %s' % (whom, msg))
        response = commands.evaluate(self, whom, msg)
        if response:
            for L in response.split('\n'):
                self.whisper(whom, L)
    
    def got_xxx_ad(self, *args):
        log(INFO, 'sending reload finish')
        PacketOut(C_MAP_LOADED).send(self.conn)
    def got_xxx_ad2(self, *args):
        log(INFO, 'sending reload finish 2')
    
    def set_channel(self, channel):
        self.channel = channel
    
    ### Class-wide bot setup
    
    @classmethod
    def set_mods(cls, mods):
        """
        Set the enabled mods list for this bot class.
        """
        cls.enabled_mods = list(mods)
    
    @classmethod
    def set_mod_conf(cls, mod_conf):
        """
        Set the mod configurations dictionary for this bot class.
        """
        cls.mod_conf = mod_conf
    
    def sleep(self, ms):
        """
        A lag-adjusting sleep utility. While rather dumb, this function can be 
        over-ridden for superior results.
        """
        # We just assume that we have 200ms of lag, and cuts that much out.
        time.sleep((ms - 200) / 1000.)


### LoF slave bot

class SlaveBot(BotBase):
    
    """
    A slave bot, which forwards messages to a master bot.
    """
    
    is_slave = True
    
    def __init__(self, master, facing, *args):
        BotBase.__init__(self, *args)
        self.master = master
        self.facing = facing
    
    def go(self):
        if self.connect():
            self.face(self.facing)
            self.sit()
            self.main()
        else:
            log(ERROR, 'The %s slave failed to connect!' % self.account)
    
    def got_msg(self, being_id, msg):
        self.master.got_msg(being_id, msg, self)


### LoF master bot

class LOFBot(BotBase):
    
    """
    The official LoF bot.
    """
    
    version = __version__
    
    def __init__(self, *args, **kw):
        BotBase.__init__(self, *args, **kw)
        self.slavelist = []
    
    def spawn_slaves(self, slavedefs):
        """
        `slavedefs` -- An iterable of (account, channel, password, direction) 
                       groups
        """
        for nick, pswd, facing in slavedefs:
            slave = SlaveBot(self, facing, self.server, self.port, nick, pswd, self.same_ip)
            #slave.set_channel(channel)
            threaded(slave.go, ())
            self.slavelist.append(slave)
    
    def reset_commands(self):
        BotBase.reset_commands(self)
        self.required_mods = set(['listen'])
        self.filters = [LOFBot.catch_afk]
    
    def broadcast(self, message, skip_slave=None, skip_master=True, **kw):
        """
        Broadcast a message through the master and the slaves. 
        
        `message`     -- the message to broadcast.
        `skip_slave`  -- optional slave instance to skip; also causes the 
                         master to not be skipped.
        `skip_master` -- boolean flag defaulting to True determining whether or 
                         not the master is skipped.
        `**kw`        -- ignored
        """
        if skip_slave or not skip_master:
            self.msg(message)
        for slave in self.slavelist:
            if slave.ready and slave is not skip_slave:
                slave.msg(message)
    
    def got_emote(self, being_id, emote_id):
        BotBase.got_emote(self, being_id, emote_id)
        self.log(INFO, 'EMOTE: %s->%s' % (being_id, emote_id))
    
    def got_name_res(self, being_id, name):
        BotBase.got_name_res(self, being_id, name)
        self.log(INFO, 'NAME RES: %s is %s' % (being_id, name))
    
    def got_msg(self, being_id, msg, source_slave=None):
        self.log(INFO, 'MSG: %s: %s' % (being_id, msg))
        def cb(sender):
            BotBase.got_msg(self, sender, msg, being_id=being_id, 
                            skip_slave=source_slave)
        self.on_name_res(being_id, cb)
    
    def got_server(self, msg):
        BotBase.got_server(self, msg)
        self.log(INFO, 'SERVER: %s' % msg)
    
    def got_unknown(self, packet):
        packbody = ' '.join('%02x' % ord(c) for c in packet.data)
        self.log(PACKET, '**%04x**: %s' % (packet.packet_id, packbody))
    
    @staticmethod
    def catch_afk(client, nick, crawler):
        if crawler.normal(False).lower() == '*afk*:':
            return True


if __name__ == '__main__':
    ### Setup logging...
    
    heading = '=' * 5 + ' %s ' + '=' * 15
    
    # File outs
    _baslog = LOFFileLog(open('lofbot.log', 'a'), [INFO, IMPORTANT, ERROR], 2)
    _implog = LOFFileLog(open('lofbot.imp.log', 'a'), [IMPORTANT, ERROR], 2)
    _deblog = LOFFileLog(
      open('lofbot.deb.log', 'a'), [DEBUG, INFO, IMPORTANT, ERROR], 2
    )
    _netlog = LOFFileLog(open('lofbot.net.log', 'a'), [PACKET, INFO], 2)
    
    # Console outs
    _errlog = LOFFileLog(sys.stderr, [ERROR], 0)
    _outlog = LOFFileLog(sys.stdout, [INFO, IMPORTANT], 0)
    
    # Master
    log = LOFLogNode((_baslog, _implog, _deblog, _netlog, _outlog, _errlog))
    
    # stdio
    sys.stdout = OutToLog(log)
    #sys.stderr = OutToError(log)
    
    ### Load command-line arguments...
    
    changes = dict(both_enable=[], both_disable=[], master_enable=[], 
                   master_disable=[], slave_enable=[], slave_disable=[])
    
    use_lofd = False
    for arg in sys.argv[1:]:
        if arg.lower() in ('--lofd', '-l'):
            use_lofd = True
            break
    
    ### Setup bot classes...
    
    TMWAClient.set_log(log)
    BotBase.set_mod_conf(config.mod_conf)
    LOFBot.set_mods(config.master_mods)
    SlaveBot.set_mods(config.slave_mods)
    
    ### Build master...
    
    bot = LOFBot(server=config.server,
                 port=config.port,
                 account=config.account,
                 pswd=config.password,
                 # Whether or not to use the passed server IP/address for each 
                 # of the tmwAthena sub-servers. If boolean False, the IPs sent 
                 # during the connection process will be used instead.
                 same_ip=config.same_ip,
                 # The slot the character is in, a zero-based index
                 cindex=0)
    
    ### Go!
    
    try:
        log(IMPORTANT, heading % 'STARTING')
        if bot.connect():
            bot.spawn_slaves(config.slaves)
            bot.face(config.direction)
            bot.sit()
            bot.main()
        else:
            log(ERROR, 'Could not connect!')
    except Exception as e:
        sys.excepthook(*sys.exc_info())
        log(ERROR, 'BUG: %s' % str(e))
    finally:
        log(IMPORTANT, heading % 'STOPPING')
        log.close_children()
