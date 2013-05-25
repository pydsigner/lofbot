from schema import Listing, close_connection


command_bank = {'listing': [True, '.listing', '.list', 'list']}

l_disp = '(%(id)s) %(seller)s: %(quantity)s %(item)s %(word)s %(price)sgp'


def format_listing(listing, tell_more=False):
    t_count = Listing.count()
    s_count = len(listing)
    if t_count > s_count and tell_more:
        msg = '(Showing %s results out of %s)\n' % (s_count, len(t_count))
    else:
        msg = ''
    msg += ' | '.join(l_disp % i for i in listing)
    
    close_connection()
    return msg or 'There are no items listed!'


def sub_show(client, nick, *args):
    l_page = client.mod_conf['listing']['page']
    if args:
        tell_more = False
        key = args[0].title()
        if key.isdigit():
            start = int(key) * l_page
            parts = list(Listing.all())[start:start + l_page]
        elif key == 'mine':
            parts = list(Listing.filter(seller=nick))
        elif key == 'only':
            t = ' '.join(args[1:])
            if not t:
                return 'The "show only" sub-command requires an item type!'
            parts = list(Listing.filter(item=t.title()))
        elif key == 'all':
            parts = list(Listing.all())
        else:
            return ('I don\'t know what you\'re trying to do, but you '
                    'might want to take a look at the "help" sub-command!')
    else:
        parts = list(Listing.all())[:l_page]
        tell_more = True
    
    return format_listing(parts, tell_more)


def sub_add(client, nick, *args):
    if len(args) < 4 or not (args[0].isdigit() and args[-1].isdigit()):
        return ('Bad arguments! See the sub-command "help".')
    
    if Listing.count(seller=nick) >= client.mod_conf['listing']['max']:
        close_connection()
        return ('You have too many items listed! Use the "remove" sub-command '
                'alongside "show mine" to remove an item first.')
    
    p = int(args[-1])
    n = int(args[0])
    t = ' '.join(args[1:-2])
    w = args[-2]
    Listing(dict(seller=nick, quantity=n, price=p, item=t.lower(), word=w)
            ).add()
    close_connection()


def listing(client, nick, crawler):
    """
    Classifieds for LoF. See the "help" sub-command for more information.
    """
    args = crawler.chain.split()
    try:
        cmd = args.pop(0).lower()
    except IndexError:
        cmd = 'show'
    
    if cmd == 'show':
        return sub_show(client, nick, *args)
    
    elif cmd == 'add':
        return sub_add(client, nick, *args)
    
    elif cmd == 'remove':
        if len(args) != 1 or not args[0].isdigit():
            return 'The "remove" sub-command requires a numeric id!'
        
        item = int(args[0])
        # one or zero matches
        match = Listing.get(seller=nick, id=item)
        if not match:
            return 'You don\'t have an item with that id!'
        match.remove()
        close_connection()
    
    elif cmd == 'help':
        return ('Use: '
                '`show [<page> | only <item name> | mine | all]` '
                 'to display a page of listings, whether a certain '
                 '(defaults to the first) page of all of results, '
                 'all items of a certain type, all of your own items, '
                 'or every single item;\n'
                
                '`add <number> <item name>` at <price>'
                 'to add an item to the listings;\n'
                
                '`remove` <id> to remove one of your items.')
    
    else:
        return ('`%s` is not a valid sub-command; '
                'see the `help` sub-command for more details.') % cmd
