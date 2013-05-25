from thread import allocate_lock


# No commands...
command_bank = {}
# Just handlers
handlers = dict(remove='handle_remove', name_res='handle_name_res', 
                emote='handle_emote', msg='handle_msg')


def setup(client):
    client.mod_whois_nmap = {}
    client.mod_whois_imap = {}
    client.mod_whois_lock = allocate_lock()


def handle_remove(client, being_id, died):
    text = 'DIED:' if died else 'REMOVAL:'
    if being_id in client.mod_whois_imap:
        print text, being_id, '(%s)' % client.mod_whois_imap[being_id]
    else:
        print text, being_id
        _whois(client, being_id)


def handle_name_res(client, being_id, name):
    name = name.lower()
    with client.mod_whois_lock:
        client.mod_whois_nmap[name] = being_id
        client.mod_whois_imap[being_id] = name


def handle_emote(client, being_id, *args):
    _whois(client, being_id)


def handle_msg(client, nick, msg, being_id, *args, **kw):
    _whois(client, being_id)


def _whois(client, being_id):
    if being_id not in client.mod_whois_imap:
        client.whois(being_id)
