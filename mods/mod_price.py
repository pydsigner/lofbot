from schema import Price, close_connection


command_bank = {'tmw_price': [True, '.tmw-price', '.tmw_price', 'tmw-price']}


def tmw_price(client, nick, crawler):
    """
    .tmw-price ["for"] <some item> -- get the TMW server price for an item, 
    based on the ~600,000 item online history of the ManaMarket bot.
    """
    if crawler.normal(False).lower() == 'for':
        # Consume it
        crawler.normal()
    
    item = crawler.chain.title()
    if not item:
        return '`tmw-price` requires an item argument!'
    
    cheap = expensive = total = items = records = 0
   
    for record in Price.filter(item=item):
        if not cheap or record.price < cheap:
            cheap = record.price
        if record.price > expensive:
            expensive = record.price
        total += record.quantity * record.price
        items += record.quantity
        records += 1
    
    close_connection()
    
    if not records:
        return 'I see no %s in the records.' % item
    
    average = total // items
    reps = (items, records, cheap, expensive)
    insert = 'over %s items in %s records, min %s, max %s' % reps
    return 'price for %s: %sgp (%s)' % (item, average, insert)
