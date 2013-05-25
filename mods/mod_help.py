"""
Full-featured `help` and `about` commands.
"""


command_bank = {'show_help': [True, '.help', 'help'],
                'show_about': [True, '.about', 'about']}


def handle_404(client, nick, cmd):
    """
    "Command not found" handler.
    """
    return ('`%s` is not a valid command. ' % cmd + 
            'See `.help` for a list of recognized commands.')


def show_help(client, nick, crawler):
    """
    `.help [commandname]` -- Get help on LoFBot commands. 
    If `commandname` is given, specific help is shown for that command; 
    otherwise, a list of all supported commands is shown.
    """
    args = crawler.chain.split()
    if args:
        # Make sure we have the . at the beginning removed (it shouldn't be 
        # passed)
        cmd = args[0].lstrip('.').strip().lower()
        try:
            doc = client.help_db['.' + cmd]
        except KeyError:
            return 'No such command as "%s"' % cmd
        return 'Help for %s (see `.help` for general help): %s' % (cmd, doc)
    return ('All LoFBot commands (see .`help` <cmd> for specific help): ' + 
            '  '.join(client.help_db))


def show_about(client, nick, *args):
    """
    Get information about this bot. Does not take arguments.
    """
    return ('I am LoFBot ' + client.version + ', '
            'written by Pyndragon for the Land of Fire tmwA server. Have fun!')
