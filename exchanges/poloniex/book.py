import sys
if "../../Common" not in sys.path: sys.path.append("../../Common") # Desperation

import datetime as dt
from decimal import Decimal
from book_base import BookBase

class Book(BookBase):
    '''
    Store orders as a dictionary of prices. Each price has one size (no orderID's)
    This is an undicumented format. Hopefully whill not change going forward.
    Do not trade USD but rather something which convert to USD
    '''
    def __init__(self, product):
        BookBase.__init__(self, product)
        
    def doSnapShot(self, bids, asks):
        # convert to Decimal
        self._bids = { Decimal(k) : {-1: Decimal(v)} for (k,v) in bids.items()}
        self._asks = { Decimal(k) : {-1: Decimal(v)} for (k,v) in asks.items()}
        self.findBestBidAsk('buy')
        self.findBestBidAsk('sell')
        
    def doUpdateBook(self, side, price, size):
        queue = self._bids if side == 'buy' else self._asks
        
        if (size == Decimal(0)):
            # Remove order
            if price in queue:
                del queue[price]
                self.findBestBidAsk(side)
            else:
                print('ERROR: Expect price {} in dictionary to delete'.format(price))
        else:
            queue[price] = {-1 : size}
            self.setBestBidAsk(side, price)
            
    def doUpdateTrade(self, side, price, size):
        # looks like the orderBook is updated before the trade message is sent.
        #queue = self._bids if side == 'buy' else self._asks
        self.setTradePriceSize(price, size)
            
def main():
    book = Book('USDT_BTC')
    
    bids = {'98':'30', '100':'20', '99':'10'}
    asks = {'102':'20', '101':'10', '103':'30'}
    
    book.doSnapShot(bids, asks)
    
    print(('Best Bid/Ask Expect (100,101). {} {}'.format(book._bestBidPrice, book._bestAskPrice)))
    book.printBestBidAsk('Expect (20@100 10@101)') 
        
    bid1 = Decimal(100.5)
    bid2 = Decimal(100)
    ask1 = Decimal(100.6)
    ask2 = Decimal(101)
    
    sz0 = Decimal(0)
    sz1 = Decimal(1)
    sz2 = Decimal(2)
    
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
    book.doUpdateBook('buy', Decimal(98), sz0) 
    book.doUpdateBook('buy', Decimal(99), sz0) 
    book.printBestBidAsk('Expect (One side is empty)') 

if __name__ == '__main__':
    main()
    
    
# First we get the whole book. First ask and then bid.
#2017-09-05 15:19:23.843306 : [121, 126524908, [['i', {'orderBook': [{'4462.93333300': '0.00067221', '4483.40757209': '0.00099650'}, {'4220.99761990': '0.00016542', '1310.02481818': '0.02534000', '4288.50215552': '0.00269646'}], 'currencyPair': 'USDT_BTC'}]]]
# then messages like where 0 means ask and 1 means bid
#2017-09-05 15:19:23.850307 : [121, 126524910, [['o', 0, '4437.96755388', '0.00000000'], ['o', 0, '4437.96755387', '0.50000000']]]
#2017-09-05 15:19:23.850307 : [121, 126524911, [['o', 1, '4150.99999997', '0.11742329']]]
# can have trade messages embedded as well
#2017-09-06 13:08:19.305219 : [121, 126825432, [['o', 1, '4595.64637817', '0.00000000'], ['o', 1, '4595.64637816', '1.19149560'], ['t', '8136299', 0, '4595.64637817', '0.28327313', 1504721300], ['t', '8136300', 0, '4595.64637817', '0.10248649', 1504721300], ['t', '8136301', 0, '4595.64637817', '0.09999781', 1504721300], ['t', '8136302', 0, '4595.64637816', '0.07369191', 1504721300]]]
