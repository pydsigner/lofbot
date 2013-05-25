import urllib
import urllib2


command_bank = {'translate': [True, '.translate', 'translate']}

opener = urllib2.build_opener()
opener.addheaders = [
  ('User-Agent', 
   'Mozilla/5.0(X11; U; Linux i686)Gecko/20071127 Firefox/2.0.0.11')]


def translate(client, nick, crawler):
    """
    `translate <some text> into <language>` -- translate text.
    """
    args = crawler.chain.split()
    if len(args) < 3:
        return 'Bad args. See `.help translate`.'
    lang = urllib.quote(args[-1])
    text = urllib.quote(' '.join(args[:-2]))
    
    raw = opener.open(
      'http://translate.google.com/translate_a/t?' +
      'client=t&hl=en&sl=auto&tl=%s&multires=1' % lang + 
      '&otf=1&ssel=0&tsel=0&uptl=en&sc=1&text=%s' % text).read()
    
    return raw.split('"')[1]
