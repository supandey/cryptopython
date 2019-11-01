# https://docs.bitfinex.com/reference#ws-public-ticker

import sys
if "../../Common" not in sys.path: sys.path.append("../../Common") # Desperation

from decimal import Decimal
from decimal import localcontext
from book_base import BookBase

class Book(BookBase):
    '''
    Store orders as a dictionary of prices. Each price has one size (no orderID's)
    Assume all prices and sizes are Decimal to ease comparisons. Else code will break.
    Prices are sent at 1 cent ersolution but trades are to 8 decimal places. Perhaps submit orders at better resolution?
    '''
    def __init__(self, product):
        BookBase.__init__(self, product)
        
    def doSnapShot(self, msgBody):
        with localcontext() as ctx:
            ctx.prec = 8   #double to float is odd
            
            for data in msgBody:
                price = Decimal(data[0])+0   #trick to get to round
                count = data[1]
                size = Decimal(data[2])+0   #trick to get to round
                if (count > 0):
                    if (size > 0):
                        self._bids[price] = {-1 : size}  # no orderID (ITCH). CME like
                    else:
                        self._asks[price] = {-1: abs(size)}
                    
        self.findBestBidAsk('buy')
        self.findBestBidAsk('sell')
        self.isGood()
        
    def doUpdateBook(self, side, price, size):
        queue = self._bids if side == 'buy' else self._asks
        
        if (size == 0):
            # Remove order
            if price in queue:
                del queue[price]
                self.findBestBidAsk(side)
            else:
                print('ERROR: Expect price {} in dictionary to delete'.format(price))
                return False
        else:
            queue[price] = {-1 : size}  # no orderID (ITCH). CME like    
            self.setBestBidAsk(side, price)
            
        return self.isGood()
            
    def doUpdateTrade(self, side, price, size):
        # looks like the orderBook is updated before the trade message is sent.
        #queue = self._bids if side == 'buy' else self._asks
        self.setTradePriceSize(price, size)
    
def main():
    book = Book('USDT_BTC')
    
    dataBidAsk = [[98, 1, 30], [100, 1, 20], [99, 1, 10],
                  [102, 1, -20], [101, 1, -10], [103, 1, -30]]
    
    book.doSnapShot(dataBidAsk)
    
    print(('Best Bid/Ask Expect (100,101). {} {}'.format(book._bestBidPrice, book._bestAskPrice)))
    book.printBestBidAsk('Expect (20@100 10@101)') 
        
    bid1 = 100.5
    bid2 = 100
    ask1 = 100.6
    ask2 = 101
    
    sz0 = 0
    sz1 = 1
    sz2 = 2
    
    #bids
    book.doUpdateBook('buy', bid1, sz1)    #add better bid
    book.doUpdateBook('buy', bid2, sz2)
    book.printBestBidAsk('Expect (1@100.5 10@101)') 
    book.doUpdateBook('buy', bid1, sz0)    #remove best bid
    book.printBestBidAsk('Expect (2@100 10@101)') 
    
    #asks
    book.doUpdateBook('sell', ask1, sz1)    #add better ask
    book.doUpdateBook('sell', ask2, sz2)
    book.printBestBidAsk('Expect (2@100 1@100.6)') 
    book.doUpdateBook('sell', ask1, sz0)    #remove best ask
    book.printBestBidAsk('Expect (2@100 2@101)  ') 
    
    #remore all bids
    book.doUpdateBook('buy', bid2, sz0) 
    book.doUpdateBook('buy', 98, sz0) 
    book.doUpdateBook('buy', 99, sz0) 
    book.printBestBidAsk('Expect (One side is empty)') 

if __name__ == '__main__':
    main()
    
#2017-09-14 13:47:24.181513 : [26586, 'hb']
#2017-09-14 13:47:24.183513 : [55, 'tu', '12067801-BTCUSD', 66333885, 1505414843, 3362.1, 0.27901986]
#2017-09-14 13:47:24.250520 : [79, [3358.3, 0, 1]]
#2017-09-14 13:47:24.250520 : [79, [3358, 0, 1]]
#2017-09-14 13:47:24.250520 : [79, [3356.2, 0, 1]]
#2017-09-14 13:47:24.251520 : [79, [3347.8, 0, 1]]
#2017-09-14 13:47:24.251520 : [79, [3335, 0, 1]]