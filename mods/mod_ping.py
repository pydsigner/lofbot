"""
Mod Ping is an LoFBot mod that allows detecting server lag and disconnections. 
It operates off of the principle that one's own emotes should be returned from 
the server in a reasonable period of time. By using a high, invisible emote 
like ManaPlus's trade alert, the ping operates on un-used bandwidth and avoids 
visually spamming players.
"""

import time

from taskit.log import IMPORTANT


command_bank = {'bot_lag': [True, '.lag', '.bot_lag']}
handlers = dict(emote='check_ping')
periodic = ['ping_cb']


PING_EMOTE = 229    # the sum of the ordinal values of the chars in 'BOT' :P


def setup(client):
    client.ping_lag = None
    client.ping_sent = None


def ping_cb(client):
    # Oh dear! We didn't get our reply in a good period of time, currently 15 
    # seconds. It could be killer lag (or not), but probably the server 
    # connection has been lost.
    if client.ping_lag is None and client.ping_sent:
        client.log(IMPORTANT, 'Emote ping timed out!')
        client.done = True
    
    client.ping_lag = None
    client.ping_sent = time.time()
    client.emote(PING_EMOTE)


def check_ping(client, being_id, emote_id):
    if being_id == client.account_id and emote_id == PING_EMOTE:
        stamp = time.time()
        # Micro seconds
        client.ping_lag = int((stamp - client.ping_sent) * 1000)


def bot_lag(client, nick, crawler):
    """
    `.lag`: get an indicator of how much lag there is. Does not allow for lag 
    caused by the internet/LAN.
    """
    if client.ping_lag is None:
        return 'The ping time has not yet been calculated, check again soon.'
    return 'Last emote ping time for this bot: %s ms' % client.ping_lag
