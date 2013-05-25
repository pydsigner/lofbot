import urllib
import time
import sys

from schema import Price, get_connection, close_connection


def rebuild(local=False):
    opened = False
    try:
        start = time.time()
        Price.clear_table()
        
        if local:
            f = open('manamarket.html')
        else:
            f = urllib.urlopen('http://manamarket.sagdas.net/manamarket.html')
        opened = True
        
        for L in f:
            L = L.strip()
            if L == '</table>':
                # We're done :)
                break
            # In the name of speed... (rather than .startswith())
            elif L[:4] != '<tr>':
                continue
            
            # chop off the "<tr> <td>" (9 chars) at the beginning, split at the 
            # cell borders ("</td> <td>"), and keep the first 3 rows, which 
            # will be completely de-HTMLed :)
            keep = L[9:].split('</td> <td>')[:3]
            
            # Create and add the entry
            Price({'item': keep[0], 
                   'quantity': int(keep[1].replace(',', '')), 
                   'price': int(keep[2].replace(',', ''))
                  }).add()
    
    except Exception:
        # Output the error
        sys.excepthook(*sys.exc_info())
        w, success = 'failed', False
        get_connection().rollback()
    else:
        w, success = 'has been completed', False
        get_connection().commit()
    
    if opened:
        f.close()
    
    taken = time.time() - start
    print 'Rebuilding the TMW price database %s after %s seconds.' % (w, taken)
    close_connection()
    return success


if __name__ == '__main__':
    rebuild(True)
