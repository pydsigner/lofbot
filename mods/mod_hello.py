"""
A mod that causes the bot to respond with friendliness to greetings.
"""


command_bank = {
  'say_hi': [False, 'hiya', 'heya', 'howdy', 'hello', 'hola', 'hi']
}


def say_hi(client, nick, crawler):
    return 'Hiya %s!' % nick
