import time
import string

from schema import Message, close_connection, get_connection


command_bank = {'tell': [True, '.tell', '.ask', 'tell', 'ask']}
periodic = ['tell_cb']
requires = ['online']

t_sym_nicks = {
   'kk': 'keekeekat', 'keekee': 'keekeekat', 'pyn': 'pyndragon', 
   'bb': 'bunnybear', 'uru': 'urubamba', 'oz': 'ozthokk', 
   'satin': 'satin_n_lace', 'elen': 'elen_batt_leon'
}


def tell_cb(client):
    if Message.count():
        for player in client.online_players:
            for msg in Message.filter(recipient=player):
                client.whisper(player, msg.text)
                msg.remove()
        get_connection().commit()
    
    close_connection()


def tell(client, nick, crawler):
    """
    `.tell <nick>|all <some thing>` -- send a message to a possibly 
    offline player, or to everyone listening.
    """
    try:
        rec = crawler.quoted().lower()
        msg = crawler.chain
    except ValueError:
        return 'You must specify a recipient and a message.'
    
    # Check for broadcast, which requires mod_listen. As a very optional 
    # feature, though
    
    if rec in ['*', 'all']:
        lmod = client.installed_mods.get('listen')
        if lmod:
            return lmod.forward(nick, msg)
        else:
            return 'This feature requires mod_listen, which is not available.'
    
    # Check for sym-nick
    rec = t_sym_nicks.get(rec, rec)
    
    # Refresh the playerlist to avoid droppage
    client.installed_mods['online'].get_playerlist(client)
    if rec in client.online_players:
        client.whisper(rec, '%s says to tell you: "%s"' % (nick, msg))
        return 'Sent.'
    
    text = (time.strftime('At %H:%M:%S on %d %B %Y, ', time.gmtime()) + 
            '%s said to tell you: "%s"' % (nick, msg)
           )
    
    Message(dict(text=text, recipient=rec)).add()
    get_connection().commit()
    close_connection()
    
    return 'Saved.       If you\'re wondering what that means, it means the person you are trying to send a message to is offline and the message will be saved until they come online again.'
