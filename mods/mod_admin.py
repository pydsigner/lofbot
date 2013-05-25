import time
import sys

import commands
import rebuild_prices


command_bank = {'admin': [True, '.admin']}


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
    Rotate `itr` `places` to the left. `itr` must be subscriptable.
    """
    return itr[places:] + itr[:places]


# A cheapo try-catch wrap around the "real" admin command
def admin(client, nick, crawler):
    """
    Administer the bot. Access is highly restricted. Those with access should 
    look at the `help` subcommand for more information.
    """
    try:
        return admin_inner(client, nick, crawler)
    except Exception:
        sys.excepthook(*sys.exc_info())
        return 'Something went wrong, try reading `.admin help`?'


def admin_inner(client, nick, crawler):
    if nick not in client.mod_conf['admin']['admins']:
        return 'You do not have administrator privileges!'
    
    try:
        cmd = crawler.normal().lower()
        text = crawler.chain
    except IndexError:
        cmd = 'help'
    
    ### Position #############
    
    if cmd == 'sit':
        client.sit()
    
    elif cmd == 'stand':
        client.stand()
    
    elif cmd == 'face':
        client.face(crawler.chain[0])
    
    ### Joke moves ###########
    
    elif cmd == 'spin':
        args = ['l', 's', '4'] if not text else text.split()
        
        rot = ['n', 'e', 's', 'w']
        rot = rotate(rot, rot.index(args[1][0].lower()))
        if args[0][0].lower() == 'l':
            rot.reverse()
        
        rot *= int(args[2])
        client.emote(10)
        time.sleep(.4)
        for d in rot:
            client.face(d)
            time.sleep(.1)
        time.sleep(.1)
        client.emote(115)
    
    
    elif cmd == 'juke':
        args = ['u', 's'] if not text else text.lower().split()
        e_up = args[0][0] == 'u'
        s_dir = args[1][0]
        f2 = 'n' if s_dir in 'ew' else 'w'
        f3 = 's' if s_dir in 'ew' else 'e'
        
        main = ['d', s_dir, '.5', '122', '1.']
        
        routine = ['u', 'd', 'u', 'd', 'u', f2, s_dir, f2, s_dir, 
                   f3, s_dir, f3, s_dir, 'd', 'u', 'd', '127']
        routine += ['u'] if e_up else []
        for p in routine:
            main.append(p)
            main.append('.2')
        
        for p in main:
            if '.' in p:
                time.sleep(float(p))
            elif p.isdigit():
                client.emote(int(p))
            elif p == 'u':
                client.stand()
            elif p == 'd':
                client.sit()
            else:
                client.face(p)
    
    ### Communications #######
    
    elif cmd == 'emote':
        client.emote(crawler.chain)
    
    elif cmd == 'say':
        client.msg(crawler.chain)
    
    elif cmd == 'whisper':
        # Need the last arg first :-/
        crawler.flip()
        to = crawler.quoted()
        crawler.flip()
        client.whisper(to, crawler.chain)
    
    ### Interaction ##########
    
    elif cmd == 'attack':
        whom = crawler.quoted()
        being_id = client.mod_whois_nmap.get(whom)
        if not being_id:
            if whom.isdigit():
                being_id = int(whom)
            else:
                return 'Sorry, I don\'t know that name.'
        
        name = client.mod_whois_imap.get(being_id)
        if name:
           more = ' (%s)' % name
        else:
            more = ''
            client.whois(being_id)
        
        text = crawler.chain
        keep = not text or text[0].lower() in 'yt'
        client.attack(being_id, keep)
        return 'Attacking %s%s!' % (being_id, more)
    
    
    elif cmd == 'goto':
        x, y = text.split()
        client.goto(int(x), int(y))
    
    ### Information ##########
    
    elif cmd == 'names':
        return ',\n'.join(
          ', '.join('%s=%s' % pair for pair in ten) 
          for ten in isection(client.mod_whois_imap.items(), 10)
        )
    
    ### Resetters ############
    
    elif cmd == 'respawn':
        client.respawn()
    
    elif cmd == 'refresh':
        if rebuild_prices.rebuild():
            return 'Successfully rebuilt TMW price DB!'
        else:
            return 'Rebuilding the TMW price DB failed!'
    
    elif cmd == 'reload':
        for mod in client.installed_mods.values():
            reload(mod)
        commands.setup_commands(client)
        
        return 'Successfully reloaded all mods installed on this bot.'
    
    ### Help #################
    
    elif cmd == 'help':
        return '\n'.join([
          '`sit` to sit; `stand` to stand; '
          '`face n|s|e|w` to face a particular direction;',
          
          '`spin [l|r] [n|s|e|w] [num]` to make the bot spin rapidly; '
          '`juke [u|d] [n|s|e|w]` to execute a lame move sequence;',
          
          '`emote <number>` to display an emote; '
          '`say <some message>` to say something; '
          '`whisper <some thing> to <player>` to whisper to a player;',
          
          '`goto <x> <y>` to move the bot;',
          
          '`names` to see all the names that the bot recognizes;',
          
          '`respawn` to respawn; '
          '`refresh` to update the db of TMW prices (long!); '
          '`reload` to reload all mods installed on this bot.'
        ])
    
    else:
        return 'Unknown command `%s`; see the `help` sub-command.' % cmd
