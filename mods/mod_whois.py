from thread import allocate_lock

from taskit.log import INFO


# No commands...
command_bank = {}
# Just handlers
handlers = dict(remove='handle_remove', name_res='handle_name_res', 
                emote='handle_emote', msg='handle_msg')


def setup(client):
    # We only get the client here, but on_name_res() needs it every time
    client.on_name_res = lambda being_id, cb: on_name_res(client, being_id, cb)
    client.mod_whois_waiters = {}
    client.mod_whois_nmap = {}
    client.mod_whois_imap = {}
    client.mod_whois_lock = allocate_lock()


def on_name_res(client, being_id, cb):
    with client.mod_whois_lock:
        # Check if we've already resolved this ID
        name = client.mod_whois_imap.get(being_id)
        if name:
            # We have, no wait required
            cb(name)
        else:
            # Let's ad it to the list of waiters
            client.mod_whois_waiters.setdefault(being_id, []).append(cb)


def handle_remove(client, being_id, died):
    text = 'DIED:' if died else 'REMOVAL:'
    if being_id in client.mod_whois_imap:
        client.log(INFO, '%s %s (%s)' % (text, being_id, client.mod_whois_imap[being_id]))
    else:
        client.log(INFO, '%s %s' % (text, being_id))
        _whois(client, being_id)


def handle_name_res(client, being_id, name):
    with client.mod_whois_lock:
        for cb in client.mod_whois_waiters.pop(being_id, []):
            cb(name)
        name = name.lower()
        client.mod_whois_nmap[name] = being_id
        client.mod_whois_imap[being_id] = name


def handle_emote(client, being_id, *args):
    _whois(client, being_id)


def handle_msg(client, nick, msg, being_id, *args, **kw):
    _whois(client, being_id)


def _whois(client, being_id):
    if being_id not in client.mod_whois_imap:
        client.whois(being_id)
