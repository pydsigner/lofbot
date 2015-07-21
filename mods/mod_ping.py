import time

command_bank = {}
periodic = ['ping_cb']


PING_EMOTE = 229    # the sum of the ordinal values of the chars in 'BOT' :P


def ping_cb(client):
    client.emote(PING_EMOTE)
