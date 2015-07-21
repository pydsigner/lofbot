"""
LOF BOT COMMANDS
================

This module provides the mod_command inteface for LoF bot.
"""

import string
import sys

from taskit.log import ERROR


class MissingRequirementsError(Exception):
    
    """
    Exception raised when all mod requirements are not met.
    """
    
    def __init__(self, missing):
        text = 'Missing requirements: ' + ', '.join(missing)
        Exception.__init__(self, text)


def evaluate(client, nick, msg):
    msg = msg.strip()
    # Strip text colors
    if msg.startswith('##'):
        msg = msg[3:]
    
    # Ignore empty messages
    if not msg:
        return ''
    
    # Catch an easy-to-make, hard-to-sight typo, plus translate some command 
    # expressions into our format
    if msg[0] in ',!@~':
        msg = '.' + msg[1:]
    
    crawler = Crawler(msg)
    
    for f in client.filters:
        res = f(client, nick, crawler)
        if res is None:
            # Do nothing
            continue
        elif res is False:
            # Choke
            return 'Illegal input!'
        elif res is True:
            # Finish
            return
        else:
            # This ought to be a string, so don't worry about collisions with 
            # the standard crowd above
            return res
    
    cmd = crawler.normal().lower()
    
    if not cmd in client.command_db:
        return client.cb_404(client, nick, cmd)
    
    try:
        return client.command_db[cmd](client, nick, crawler)
    except ValueError as e:
        return 'Error! -- ' + (e.message or 'unknown cause')


def parse_help(func):
    """
    Turn an indented, newline-padded, 80-char justified docstring into a normal 
    line of text.
    """
    # Grab the raw doc
    doc = func.__doc__
    
    # Check for non-existent documentation and return a 404 message of sorts
    if not doc:
        return 'Woops, there isn\'t any documentation for this command!'
        
    # Strip away extra newlines
    doc = doc.strip()
    # Split on (and remove) the newlines
    doc = doc.split('\n')
    # Clean out the leading space on each line, merge the lines, and return
    return ' '.join(L.strip() for L in doc)


def setup_commands(bot):
    """
    Initialize or refresh the command setup for a bot.
    """
    # Reset the bot's command setup
    bot.reset_commands()
    # Load enabled mods
    for mod in bot.enabled_mods:
        try:
            full = 'mod_%s' % mod
            m = getattr(__import__('mods.%s' % full), full)
        except Exception:
            bot.log(ERROR, 'Importing the %s mod failed!' % mod)
            sys.excepthook(*sys.exc_info())
            continue
        
        try:
            bot.installed_mods[mod] = m
            # Check for a 404 handler, and replace the current one if there is
            p404 = getattr(m, 'handle_404', None)
            if p404:
                bot.cb_404 = p404
            
            # Check for a setup function, and run it if there is
            setup = getattr(m, 'setup', None)
            if setup:
                setup(bot)
            
            # Required command bank
            for cmd in m.command_bank:
                # Get the actual function
                func = getattr(m, cmd)
                # Get the args for the command
                data = m.command_bank[cmd]
                # If data[0] is true, mod_help will recognize this command
                if data[0]:
                    bot.help_db[data[1]] = parse_help(func)
                # Get the main name and aliases inserted
                for alias in data[1:]:
                    bot.command_db[alias] = func
            
            # Helper function for optional nameless multiples
            def add_optional(olist, name):
                olist.extend(getattr(m, f) for f in getattr(m, name, ()))
            
            # Optional filters are loaded and added to the list
            add_optional(bot.filters, 'filters')
            
            # Ditto for time-cycle callbacks
            add_optional(bot.periodic_cbs, 'periodic')
            
            # Handlers are the same, but structured as a dict with
            # "type": "single function-name" items
            handlers = getattr(m, 'handlers', None)
            if handlers:
                for cbtype in handlers:
                    bot.handlers[cbtype].append(getattr(m, handlers[cbtype]))
            
            # Register any requirements
            # NOTE: By putting this at the end, we avoid the possibility of 
            # getting fake requires.
            reqs = getattr(m, 'requires', None)
            if reqs:
                bot.required_mods.update(reqs)
        except Exception:
            bot.log(ERROR, 'Unable to install the %s mod!' % mod)
            del bot.installed_mods[mod]
            sys.excepthook(*sys.exc_info())
    
    missing = bot.required_mods - set(bot.installed_mods)
    if missing:
        raise MissingRequirementsError(missing)
    
    # And now for the post-install triggers.
    for mod, m in bot.installed_mods.items():
        post = getattr(m, 'post_prepare', None)
        if post:
            try:
                post(bot)
            except Exception:
                bot.log(ERROR, 'Unable to post-prepare the %s mod!' % mod)
                sys.excepthook(*sys.exc_info())


class Crawler(object):
    def __init__(self, text):
        self.text = self.chain = text
    
    def __nonzero__(self):
        return bool(self.chain)
    __bool__ = __nonzero__
    
    def __len__(self):
        # Something of a stupid and slow evaluation :-/
        return len(self.chain.split())
    
    def flip(self):
        self.chain = self.chain[::-1]
    
    def normal(self, consume=True):
        # Speed and ease
        chain = self.chain
        if not chain:
            raise ValueError('parsing error: nothing left to parse!')
        
        res = chain.split(None, 1)
        if len(res) == 1:
            content, more = res[0], ''
        else:
            content, more = res
        
        if consume:
            self.chain = more
        
        return content

    def quoted(self, consume=True):
        # Speed and ease
        chain = self.chain
        if not chain:
            raise ValueError('parsing error: nothing left to parse!')
        
        if chain[0] != '"':
            return self.normal(consume=consume)
        
        pos = 1
        clen = len(chain)
        while clen > pos:
            pp = pos + 1
            if chain[pos] == '\\':
                # Ignore following character
                pos += 2
            elif chain[pos] == '"' and (clen == pp or chain[pp] == ' '):
                # Skip the quotes
                content, more = chain[1:pos], chain[pp:]
                if consume:
                    self.chain = more.strip()
                return content
            else:
                pos = pp
        
        raise ValueError('parsing error: missing close quotes!')
