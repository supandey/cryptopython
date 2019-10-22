import sys
if "../../Common" not in sys.path: sys.path.append("../../Common") # Desperation

import datetime as dt
from decimal import Decimal
from book_base import BookBase

class Book(BookBase):
    '''
    ITCH like. Orders are add/delete/modify. Know position in queue.
    Store orders as a dictionary of prices. Each price has a dictionary of orderIDs.
    '''
    def __init__(self, product):
        BookBase.__init__(self, product)
        
    def doOpen(self, side, price, size, orderID):
        # The order is now open on the order book.
        # This message will only be sent for orders which are not fully filled immediately.
        # remaining_size will indicate how much of the order is unfilled and going on the book.
        queue = self._bids if side == 'buy' else self._asks
        self.setBestBidAsk(side, price)
            
        if price in queue:
            priceDict = queue[price]
            priceDict[orderID] = size
        else:
            queue[price] = {orderID : size}
            
    def doDone(self, side, price, size, orderID):
        # The order is no longer on the order book.
        # There will be no more messages for this order_id after a done message.
        # market orders will not have a remaining_size or price field
        # done messages for orders which are not on the book should be ignored when maintaining a real-time order book.
        queue = self._bids if side == 'buy' else self._asks
        if price in queue:
            priceDict = queue[price]
            if orderID in priceDict:
                sizeInBook = priceDict[orderID]
                del priceDict[orderID]
                # validity check, make sure we have a consistent order book
                if size != sizeInBook:
                    print('Error: inconsistent order book size: local: {}, data: {}'.format(sizeInBook, size))
                    #self.reStart()
                    return False
            if (len(priceDict) == 0):
                del queue[price]
                if (side == 'buy' and price == self._bestBidPrice) or (side == 'sell' and price == self._bestAskPrice):
                    self.findBestBidAsk(side)
                    
        return True
                
    def doMatch(self, side, price, size, orderID):
        # A trade occurred between two orders.
        # The side field indicates the maker order side.
        queue = self._bids if side == 'buy' else self._asks
        if price in queue:
            self.setTradePriceSize(price, size)
            priceDict = queue[price]
            if orderID in priceDict:
                if priceDict[orderID] > size:
                    priceDict[orderID] -= size   # reduce the matched amount
                else:
                    del priceDict[orderID]
                    
                if (len(priceDict) == 0):
                    del queue[price]
                    if (side == 'buy' and price == self._bestBidPrice) or (side == 'sell' and price == self._bestAskPrice):
                        self.findBestBidAsk(side)  

    def doChange(self, side, price, size, orderID):
        # An order has changed.
        # change messages are sent anytime an order changes in size;
        # this includes resting orders (open) as well as received but not yet open.
        # change messages for received but not yet open orders can be ignored when building a real-time order book.
        # Any change message where the price is null indicates that the change message is for a market order.
        queue = self._bids if side == 'buy' else self._asks
        if price in queue:
            priceDict = queue[price]
            priceDict[orderID] = size   # set new size
        
def main():
    book = Book('BTC-USD')
    orderID = 1000
    origOrderID = orderID
    
    bid1 = Decimal(100)
    bid2 = Decimal(99)
    ask1 = Decimal(101)
    ask2 = Decimal(102)
    
    sz1 = Decimal(1)
    sz2 = Decimal(2)
    sz6 = Decimal(6)
    
    #bids
    book.doOpen('buy', bid1, sz1, orderID)
    orderID = orderID + 1
    book.doOpen('buy', bid1, sz2, orderID)
    orderID = orderID + 1
    book.doOpen('buy', bid2, sz1+sz2, orderID)
    orderID = orderID + 1
    book.doOpen('buy', bid2, sz2+sz2, orderID)
    
    #asks
    orderID = orderID + 1
    book.doOpen('sell', ask1, sz1+sz2, orderID)
    orderID = orderID + 1
    book.doOpen('sell', ask1, sz2+sz2, orderID)
    orderID = orderID + 1
    book.doOpen('sell', ask2, sz2+sz2, orderID)
    
    print(('Best Bid/Ask Expect (100,101). {} {}'.format(book.getBestBid()[0], book.getBestAsk()[0])))
    book.printBestBidAsk('Expect (3@100 7@101)') 
    
    # test change
    book.doChange('buy', bid1, sz6, origOrderID)
    book.printBestBidAsk('Expect (8@100 7@101)')
    
    # test done
    book.doDone('buy', bid2, sz1+sz2, origOrderID+2)
    print(('Best Bid/Ask Expect (100,101). {} {}'.format(book.getBestBid()[0], book.getBestAsk()[0])))
    # remove 2nd lvl bid
    book.doDone('buy', bid2, sz2+sz2, origOrderID+3)
    print(('Best Bid/Ask Expect (100,101). {} {}'.format(book.getBestBid()[0], book.getBestAsk()[0])))
    
    # remove top level ask
    book.doDone('sell', ask1, sz1+sz2, origOrderID+4)
    book.doDone('sell', ask1, sz2+sz2, origOrderID+5)
    print(('Best Bid/Ask Expect (100,102). {} {}'.format(book.getBestBid()[0], book.getBestAsk()[0])))
    
    book.printBestBidAsk('Expect (8@100 4@102)')
    
    # test match
    book.doMatch('buy', bid1, sz2, origOrderID)
    book.printBestBidAsk('Expect (6@100 4@102)')
    
    # add 2nd lvl bid again
    orderID = orderID + 1
    book.doOpen('buy', bid2, sz2, orderID)
    
    book.doMatch('buy', bid1, sz6, origOrderID)
    book.doMatch('buy', bid1, sz2, origOrderID+1)  # remove top bids
    book.printBestBidAsk('Expect (2@99 4@102)')
    
    # remove all bids
    book.doMatch('buy', bid2, sz2, orderID)
    book.printBestBidAsk('Expect (One side is empty)')

if __name__ == '__main__':
    main()
   
#2017-08-31 10:17:12.249944 {'type': 'open', 'product_id': 'BTC-USD', 'price': '4711.55000000', 'order_id': '2f73b85b-32dc-4e31-8360-60c3eb2a1a3f', 'time': '2017-08-31T15:17:12.112000Z', 'side': 'sell', 'sequence': 3929837380, 'remaining_size': '0.77000000'} 
#2017-08-31 10:17:12.249944 {'type': 'received', 'product_id': 'BTC-USD', 'order_id': '4a5c3ef6-962d-493d-89da-999d58ea809f', 'order_type': 'market', 'side': 'buy', 'time': '2017-08-31T15:17:12.119000Z', 'sequence': 3929837381, 'funds': '0.0099669680000000'} 
#2017-08-31 10:17:12.265544 {'type': 'match', 'product_id': 'BTC-USD', 'price': '4701.40000000', 'side': 'sell', 'time': '2017-08-31T15:17:12.119000Z', 'taker_order_id': '4a5c3ef6-962d-493d-89da-999d58ea809f', 'maker_order_id': '709a92a8-9c3b-4cc0-be63-30535e389c8a', 'trade_id': 20071998, 'sequence': 3929837382, 'size': '0.00000212'} 
#2017-08-31 10:17:12.265544 {'type': 'done', 'product_id': 'BTC-USD', 'side': 'buy', 'order_id': '4a5c3ef6-962d-493d-89da-999d58ea809f', 'time': '2017-08-31T15:17:12.119000Z', 'sequence': 3929837383, 'reason': 'filled'} 
