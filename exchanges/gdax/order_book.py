#
# Based on https://github.com/danpaquin/gdax-python and https://github.com/Seratna/GDAX-python
#

#from IPython.core.debugger import Pdb
#Pdb().set_trace()


import sys
if "../../Common" not in sys.path: sys.path.append("../../Common") # Desperation
if "../Exchanges/gdax" not in sys.path: sys.path.append("../Exchanges/gdax") # Desperation

import datetime as dt
import pytz 
from decimal import Decimal

from book import Book
from public_client import PublicClient
from order_book_base import OrderBookBase

class OrderBook(OrderBookBase):
    '''Live order book updated from the Websocket Feed'''
    
    def __init__(self, url, products, oneThreadPerProduct, log_to=None):
        OrderBookBase.__init__(self, url, products, oneThreadPerProduct)
        self._book = {product : Book(product) for product in self.products}
        self._client = PublicClient()
        
    def on_subscribe(self, threadName):
        msg = {'type': 'subscribe', 'product_ids': self.products, 'channels':['full']}
        self.subscribe(threadName, msg)

    def on_message(self, data):
        ''' process the received message '''
        if self._log_to:
            try:
                self._log_to.write('{} {} \n'.format(dt.datetime.now(), str(data)))
            except ValueError:
                pass  # I/O operation on closed file.
            
        msg_type = data['type']  # get message type
        if msg_type == 'heartbeat' or msg_type == 'subscriptions':  # ignore heartbeat msg
            return
        
        product = data['product_id']
        sequence = data['sequence']
        self._workingProduct = product
        
        if self._sequence[product] == -1:
            self.getSnapShot(product)
        
        if sequence <= self._sequence[product]:
            # ignore older messages (e.g. before order book initialization from getProductOrderBook)
            return
        elif sequence > self._sequence[product] + 1:
            errMsg = 'Error: messages missing ({} - {}). Get snapShot.'.format(sequence, self._sequence[product])
            self.on_error(errMsg)
            self.getSnapShot(product)
            return
        
        nowTime = dt.datetime.now(self._local_timezone)
        try:
            exchTimeUTC = dt.datetime.strptime(data['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
            exchTime = exchTimeUTC.replace(tzinfo=pytz.utc).astimezone(self._local_timezone)        # convert to lcoal time
        except:
            exchTime = nowTime
        
        exchDly = (nowTime - exchTime).total_seconds();
        self._book[product].setExchDly(exchDly)
        self._book[product].setTradePriceSizeToZero()
        
        side = data['side']     # buy or sell
        
        if msg_type == 'received':
            # This message is emitted for every single valid order as soon as
            # the matching engine receives it whether it fills immediately or not.
            pass

        elif msg_type == 'open':
            # The order is now open on the order book.
            # This message will only be sent for orders which are not fully filled immediately.
            # remaining_size will indicate how much of the order is unfilled and going on the book.
            price = Decimal(data['price'])
            orderID = data['order_id']
            size = Decimal(data['remaining_size'])
            self._book[product].doOpen(side, price, size, orderID)

        elif msg_type == 'done':
            # The order is no longer on the order book.
            # There will be no more messages for this order_id after a done message.
            # market orders will not have a remaining_size or price field
            # done messages for orders which are not on the book should be ignored when maintaining a real-time order book.
            if 'price' in data:
                price = Decimal(data['price'])
                orderID = data['order_id']
                size = Decimal(data['remaining_size'])
                if (not self._book[product].doDone(side, price, size, orderID)):
                    self.on_error('Inconsistant order book. Get snapshot')
                    self.getSnapShot(product)
                    return
                            
        elif msg_type == 'match':
            # A trade occurred between two orders.
            # The side field indicates the maker order side.
            price = Decimal(data['price'])
            orderID = data['maker_order_id']
            size = Decimal(data['size'])
            self._book[product].doMatch(side, price, size, orderID)

        elif msg_type == 'change':
            # An order has changed.
            # change messages are sent anytime an order changes in size;
            # this includes resting orders (open) as well as received but not yet open.
            # change messages for received but not yet open orders can be ignored when building a real-time order book.
            # Any change message where the price is null indicates that the change message is for a market order.
            if 'price' in data and data['price']:  # Change msg for limit orders will always have a price specified.
                price = Decimal(data['price'])
                orderID = data['order_id']
                size = Decimal(data['new_size'])
                self._book[product].doChange(side, price, size, orderID)

        elif msg_type == 'error':
            # If you send a message that is not recognized or an error occurs,
            # the error message will be sent and you will be disconnected.
            errMsg = 'Error: received error message: {}'.format(data['message'])
            self.on_error(errMsg)
            self.close()
            return

        else:
            print('Error: unexpected message type: {}'.format(msg_type))
        
        self._sequence[product] = sequence
        self.isGood(product)
        
        if (self._callbackHandler and self._workingProduct and self.isGood(self._workingProduct)):
            self._callbackHandler.on_message(self._workingProduct)
    
    def getSnapShot(self, product):
        res = self._client.get_product_order_book(product_id=product, level=3)
        for bid in res['bids']:
            price = Decimal(bid[0])
            size = Decimal(bid[1])
            orderID = bid[2]
            self._book[product].doOpen('buy', price, size, orderID)
                
        for ask in res['asks']:
            price = Decimal(ask[0])
            size = Decimal(ask[1])
            orderID = ask[2]
            self._book[product].doOpen('sell', price, size, orderID)
            
        self._sequence[product] = res['sequence']
    
def main():
    import time

    class OrderBookConsole(OrderBook):
        ''' Logs real-time changes to the bid-ask spread to the console '''

        def __init__(self, url='wss://ws-feed.gdax.com', products=['BTC-USD', 'ETH-USD'], oneThreadPerProduct=False, log_to=None):
        #def __init__(self, url='wss://ws-feed.gdax.com', products=['LTC-BTC'], oneThreadPerProduct=False, log_to=None):
            OrderBook.__init__(self, url, products, oneThreadPerProduct, log_to=log_to)

            # latest values of bid-ask spread
            self._bP = {product: None for product in self.products}
            self._aP = {product: None for product in self.products}
            self._bS = {product: None for product in self.products}
            self._aS = {product: None for product in self.products}

        def on_message(self, message):
            OrderBook.on_message(self, message)
            
            product = self._workingProduct
            
            if (product == None or not self.isGood(product)):
                return;
            
            # Calculate newest bid-ask spread
            bS, bP, aP, aS = self.getTopBidAsk(product)

            if (self._bP[product] == bP and 
                self._aP[product] == aP and 
                self._bS[product] == bS and 
                self._aS[product] == aS):
                # If there are no changes to the bid-ask spread since the last update, no need to print
                pass
            else:
                # If there are differences, update the cache
                self._bP[product] = bP
                self._aP[product] = aP
                self._bS[product] = bS
                self._aS[product] = aS
                print('{} {} \t bid: {:.5f} @ {}\task: {:.5f} @ {}'
                      .format(dt.datetime.now(), product, bS, bP, aS, aP))
                
        def on_close(self):
            OrderBook.on_close(self)
            print("-- Goodbye! --")

    #fh = open("rawTick.log", "w")
    fh = None
    order_book = OrderBookConsole(log_to=fh)
    order_book.start()
    time.sleep(10)
    print('Close OrderBook')
    order_book.close()
    
if __name__ == '__main__':
    main()
