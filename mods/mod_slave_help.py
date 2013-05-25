"""
Slave-oriented help services.
"""


command_bank = {
  'show_about': [True, '.about', 'about'],
  'say_hi': [False, 'hiya', 'heya', 'howdy', 'hello', 'hola', 'hi']
}


def handle_404(client, nick, cmd):
    """
    "Command not found" handler for slaves.
    """
    return (
      '`%s` is not a valid command for this slave. ' % cmd + 
      'Since slaves have a limited command set to save resources -- ' 
      'and to avoid redundancy with the master bot and each other -- ' 
      'you might want to try your command on %s, ' % client.master.account + 
      'the master of this slave bot.')


def say_hi(self, client, nick, crawler):
    return ('Hiya, %s! Unless you are an admin, ' % nick + 
            'you should probably direct your whispers to my master, ' + 
            client.master.account + '.')


def show_about(self, client, nick, crawler):
    """
    Get information about this bot. Does not take arguments.
    """
    ac = client.master.account
    vr = client.master.version
    return (
      'I am a slave of %s, an instance of Pyndragon\'s LoFBot %s.' % (ac, vr) + 
      'You should direct your commands to said bot character. Have fun!'
    )
