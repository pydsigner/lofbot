###                                                                 ##
# Edit to suit your configuration needs, then rename it `config.py`. #
##                                                                 ###

### Server configuration #####

server = 'localhost'
port = 6901
same_ip = True

### Bot lists ################

master = ('GeorgeBot', 'channel_0', 'my_p@ssw0rd_is_dud3', 'North')

slaves = [('GeorgeBot_s1', 'channel_s1', 'cH33z3_Gr1n_4_u', 'East'), 
          ('GeorgeBot_s2', 'channel_s2', 'Lo57_1337!_5oS', 'West')]

### Mod lists ################

master_mods = ['ping', 'online', 'tell', 'listing', 'translate', 'listen', 
               'admin', 'hello', 'price', 'phenny_wiktionary', 'whois', 'help']
slave_mods = ['admin', 'whois', 'slave_help']

### Mod configuration ########

mod_conf = {
  'online': {'url': 'http://localhost:8000/online.txt'}, 
  
  'admin': {'admins': ['o11c', 'Pihro', 'Captain Crow', 'George']},
  
  'listing': {'page': 10, 'max': 5}
}
