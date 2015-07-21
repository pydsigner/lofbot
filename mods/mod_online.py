from time import time, gmtime, strftime

from taskit.threaded import allocate_lock
import requests

from schema import Sighting, SingleStat, commit_and_close, close_connection


command_bank = {'online': [True, '.online'], 'seen': [True, '.seen', 'seen'], 
		'recent': [True, '.recent']}
periodic = ['get_playerlist', 'refresh_sightings']


def setup(client):
    client.mod_online_lock = allocate_lock()
    client.online_players = []
    if not SingleStat.get(ref='mod_online.count'):
        SingleStat(dict(ref='mod_online.count', data='0')).add()
        commit_and_close()


### Online players


def get_playerlist(client):
    """
    Refresh the playerlist. Thread-safe.
    """
    do = not client.mod_online_lock.locked()
    
    # Have to wait for the lock anyways, because we want the playerlist to have 
    # been updated immediately before this function returns.
    with client.mod_online_lock:
        if do:
            try:
                raw = requests.get(client.mod_conf['online']['url']).text
            except Exception as e:
                # Get the message from the `gaierror`
                print('Could not fetch online list because: %s' % e)
                # Can't decipher anything now!
                return
            
            # Messy decipherage. To see what's going on just look at the file, 
            # as it explains pretty well what we are scraping and why we are 
            # doing it *this* way...
            # At least, it does if you stare at it long enough >:D
            raw = raw.split('-' * 30)[1].split('\n\n')[0].split('\n')
            players = [p.strip('(GM) ').strip().lower() for p in raw if p]
            
            client.online_players = players


def online(client, nick, crawler):
    """
    `.online [player]` -- get the entire online list, or whether or not a 
    particular player is online.
    """
    text = crawler.chain
    if text:
        if text.lower() in client.online_players:
            return '%s is online.' % text
        else:
            return '%s is offline.' % text
    else:
        return ', '.join(client.online_players)


### Sightings


def _is_bot(name):
    return 'bot' in name or name in ['manamarket']


def refresh_sightings(client):
    """
    Refresh the list of player sightings.
    """
    for p in client.online_players:
        if _is_bot(p):
            continue
        
        s = Sighting.get(player=p)
        if not s:
            s = Sighting(dict(player=p, time=0, count=0))
            s.add()
        s.count += 1
        s.time = time()
    
    stats = SingleStat.get(ref='mod_online.count')
    stats.data = str(int(stats.data) + 1)
    commit_and_close()


def time_msg(time, client, player):
    if player in client.online_players:
        return 'just now'
    else:
        return strftime('at %H:%M:%S on %d %B %Y', gmtime(time))


def count_msg(count, ticks):
    if count == ticks:
        return 'every time'
    return str(round(count * 100. / ticks, 1)) + '% of the time'


def seen(client, nick, crawler):
    """
    `.seen <player>|(most [num:5])` -- get the last time the given player was 
    seen, or a list of the most seen players.
    """
    if crawler.chain:
        pl = crawler.quoted()
        a0 = pl.lower()
    else:
        a0 = 'most'
    
    if _is_bot(a0):
        return 'That isn\'t important!'
    
    ticks = int(SingleStat.get(ref='mod_online.count').data)
    
    if a0 == 'most':
        arg = crawler.chain.strip()
        top = int(arg) if (arg and arg.isdigit()) else 5
        # Show max of ten entries
        top = min(top, 10)
        
        # Inefficient -_-
        L = list(Sighting.all())
        L.sort(key=lambda sighting: sighting.count, reverse=True)
        
        msg = ''
        new = True
        for s in L[:top]:
            pl = s.player
            msg += ('Last seen %s, ' % time_msg(s.time, client, pl) + 
                    '%s was seen %s;' % (pl, count_msg(s.count, ticks)) + 
                    (' ' if new else '\n'))
            
            new = not new
        
    else:
        s = Sighting.get(player=a0)
        if not s:
            return 'Sorry, but I haven\'t ever seen %s.' % pl
        msg = 'I last saw %s %s. ' % (pl, time_msg(s.time, client, a0))
        msg += 'I saw %s %s. ' % (pl, count_msg(s.count, ticks))
    
    close_connection()
    return msg

def recent(client, nick, crawler):
    """
    `.recent [number:5]` -- get a list of the most recently online players.
    """
    number = int(crawler.chain) if crawler.chain else 5
    number = min(number, 20)    # Need a maximum!
    L = list(Sighting.all())
    L.sort(key=lambda sighting: sighting.time, reverse=True)
    
    msg = ''
    new = True
    for s in L[:number]:
        pl = s.player
        msg += '%s was last seen %s' % (pl, time_msg(s.time, client, pl))
        msg += ', ' if new else ';\n'
        
        new = not new
    
    close_connection()
    return msg[:-2] + '.'
