import json

from schema import Listener, get_connection, close_connection


command_bank = {'forward': [True, '.forward', '.f', 'forward'],
                'listen': [True, '.listen'],
                'ignore': [True, '.ignore', '.block'],
                }
filters = ['check_special']
handlers = dict(msg='listen_cb')
requires = ['online']

f_message = '<%s> %s'
f_action = '* %s %s'


def expand(nick, msg):
    """
    Expand a message into one including the speaker's nick.
    """
    if msg[0] == '*' and msg[-1] == '*':
        return f_action % (nick, msg[1:-1].strip())
    return f_message % (nick, msg)


def listen_cb(client, nick, msg, **kw):
    """
    Handle pumping a message out.
    """
    msg = expand(nick, msg)
    client.broadcast(msg, **kw)
    for listener in Listener.filter(listening=True):
        name = listener.listener
        ignores = json.loads(listener.ignores)
        if nick != name and nick.lower() not in ignores and name.lower() in client.online_players:
            client.whisper(name, msg)


def check_special(client, nick, crawler):
    text = crawler.chain

    # Just in case this person's AFK message ends with an asterisk...
    if text.startswith('*AFK*:'):
        return

    if ((text.startswith('*') and text.endswith('*')) or
        (text.startswith('[@@') and text.endswith('@@]'))):
        # Could be /me or /url
        forward(client, nick, crawler)
        return True


def forward(client, nick, crawler, **kw):
    """
    .forward <some message> -- chime into a conversation remotely.
    """
    # We don't need to do any parsing, just pass it along :)
    listen_cb(client, nick, crawler.chain, skip_master=False)


def listen(client, nick, crawler):
    """
    .listen [true|false|yes|no] -- Set/get your listening status.
    """
    text = crawler.chain
    do_listen = text[0].lower() in 'yt' if text else None

    listener = Listener.get(listener=nick)
    if not listener:
        do_listen = False if do_listen is False else True
        Listener(dict(listener=nick, listening=do_listen, ignores='[]')).add()
    elif do_listen is None:
        do_listen = listener.listening
    else:
        listener.listening = do_listen

    get_connection().commit()
    close_connection()

    return 'You are%s listening.' % ('' if do_listen else 'n\'t')


def ignore(client, nick, crawler):
    """
    .ignore [<nick> true|false|yes|no] -- View or modify ignore list
    """
    listener = Listener.get(listener=nick)

    # Return current ignore list if no args are passed
    if not crawler.chain:
        return listener.ignores

    nick = crawler.quoted().lower()
    remainder = crawler.chain.lower()

    block = remainder[0] in 'yt' if remainder else True

    current = set(json.loads(listener.ignores))
    if block:
        current.add(nick)
    else:
        if nick in current:
            current.remove(nick)

    if current == set(json.loads(listener.ignores)):
        return 'No ignore changes made.'

    listener.ignores = json.dumps(list(current))
    get_connection().commit()
    close_connection()

    msg = 'Ignoring %s' if block else 'Unignoring %s.'
    return msg % nick
