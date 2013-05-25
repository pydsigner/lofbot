"""
wiktionary.py - Phenny Wiktionary Module
Copyright 2009, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/

--------------------
Modified and PEP8'ed for LoFBot by Daniel Foerster 2012-2013.
"""

import re
import urllib


command_bank = {'wiktionary': [True, '.wiktionary', '.w']}

uri = 'http://en.wiktionary.org/w/index.php?title=%s&printable=yes'
r_tag = re.compile(r'<[^>]+>')
r_ul = re.compile(r'<ul>.*?</ul>', re.I | re.M | re.S)


def text(html): 
    text = r_tag.sub('', html).strip()
    text = text.replace('\n', ' ')
    text = text.replace('\r', '')
    text = text.replace('(intransitive', '(intr.')
    text = text.replace('(transitive', '(trans.')
    return text


def scrape(word): 
    u = urllib.urlopen(uri % urllib.quote(word.encode('utf-8')))
    data = r_ul.sub('', u.read())
    u.close()
    
    mode = None
    etymology = None
    definitions = {}
    for line in data.splitlines(): 
        if 'id="Etymology"' in line: 
            mode = 'etymology'
        elif 'id="Noun"' in line: 
            mode = 'noun'
        elif 'id="Verb"' in line: 
            mode = 'verb'
        elif 'id="Adjective"' in line: 
            mode = 'adjective'
        elif 'id="Adverb"' in line: 
            mode = 'adverb'
        elif 'id="Interjection"' in line: 
            mode = 'interjection'
        elif 'id="Particle"' in line: 
            mode = 'particle'
        elif 'id="Preposition"' in line: 
            mode = 'preposition'
        elif 'id="' in line: 
            mode = None
        
        elif (mode == 'etmyology') and ('<p>' in line): 
            etymology = text(line)
        elif (mode is not None) and ('<li>' in line): 
            definitions.setdefault(mode, []).append(text(line))
        
        if '<hr' in line: 
            break
    
    return etymology, definitions


parts = ('preposition', 'particle', 'noun', 'verb', 
   'adjective', 'adverb', 'interjection')


def format(word, definitions, number=2): 
    result = '%s' % word.encode('utf-8')
    for part in parts: 
        if definitions.has_key(part): 
            defs = definitions[part][:number]
            result += u' \u2014 '.encode('utf-8') + ('%s: ' % part)
            n = ['%s. %s' % (i + 1, e.strip(' .')) for i, e in enumerate(defs)]
            result += ', '.join(n)
    
    return result.strip(' .,')


def wiktionary(client, nick, crawler): 
    """
    Look up a word on Wiktionary. Takes one argument -- the word to define.
    """
    if not crawler:
        return 'Nothing to define; see `.help w`.'
    # Nothing to lose by doing this...
    word = crawler.quoted()
    
    etymology, definitions = scrape(word)
    if not definitions: 
        return 'Couldn\'t get any definitions for %s.' % word
    
    result = format(word, definitions)
    if len(result) < 100: 
        result = format(word, definitions, 3)
    if len(result) < 100: 
        result = format(word, definitions, 5)
    
    if len(result) > 240: 
        result = result[:235] + '[...]'
    return result
