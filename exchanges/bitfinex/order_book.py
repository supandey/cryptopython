import sys
if "../../Common" not in sys.path: sys.path.append("../../Common") # Desperation
if "../Exchanges/bitfinex" not in sys.path: sys.path.append("../Exchanges/bitfinex") # Desperation

import datetime as dt
from decimal import Decimal
from decimal import localcontext

from book import Book
from public_client import PublicClient
from order_book_base import OrderBookBase

class OrderBook(OrderBookBase):
    '''Live order book updated from the Websocket Feed'''
    
    def __init__(self, url, products, oneThreadPerProduct, log_to=None):
        OrderBookBase.__init__(self, url, products, oneThreadPerProduct)
        self._book = {product : Book(product) for product in self.products}     # ignore leading "t" which is not in data returned (tBTCUSD)
        self._client = PublicClient()
        self._currencyDictBook = {}
        self._currencyDictTrade = {}
        self._log_to = log_to
            
        #decimal.getcontext().prec = 8
        print('Init OrderBook. Create {}'.format(self._book.keys()))
        
    def on_subscribe(self, threadName):
        # subscribe
        for product in self.products:
            #msg = {'event': 'subscribe', 'channel': 'book', 'pair': product, 'prec': 'R0'} #provides updates via order ID.
#            msg = {'event': 'subscribe', 'channel': 'book', 'pair': 't'+product, 'len' : 100, 'flags': 8+65536}   # need to add 't' to subscribe
            msg = {'event': 'subscribe', 'channel': 'book', 'symbol': 't'+product, 'len' : 100, 'flags': 8+65536}   # need to add 't' to subscribe
            self.subscribe(threadName, msg)
        
        for product in self.products:
#            msg = {'event': 'subscribe', 'channel': 'trades', 'pair': 't'+product}           # need to add 't' to subscribe
            msg = {'event': 'subscribe', 'channel': 'trades', 'symbol': 't'+product} 
            self.subscribe(threadName, msg)

    def on_message(self, msg):
        ''' process the received message '''
        if self._log_to:
            try:
                self._log_to.write('{} : {} \n'.format(dt.datetime.now(), msg))
            except ValueError:
                pass  # I/O operation on closed file.
                
        if (type(msg) is dict):
            
            if ('chanId' in msg):
                productID = int(msg['chanId'])
                channel = msg['channel']  #trades or book
                product = msg['pair']
                event = msg['event']
                
                if (event == 'subscribed' and channel == 'book'):
                    self._currencyDictBook[productID] = product
                    print('Book mapping: {}'.format(self._currencyDictBook))
                elif (event == 'subscribed' and channel == 'trades'):
                    self._currencyDictTrade[productID] = product
                    print('Trade mapping: {}'.format(self._currencyDictTrade))
                elif (event == 'error'):
                    print('ERROR: {}'.format(msg))
                    return
                
        elif (type(msg) is list):
            
            productID = int(msg[0])
            
            try:
                if (productID in self._currencyDictBook):
                    
                    product = self._currencyDictBook[productID]
                    self._workingProduct = product
                    
                    if (msg[1] == 'hb'):
                        return
                    elif (type(msg[1]) is list):
                        lMsg = msg[1] 
                        
                        if (type(lMsg[0]) is list):                        # breaking change. everything is a list or list of lists now
                            self._book[product].doSnapShot(lMsg)
                        else:
                            with localcontext() as ctx:
                                ctx.prec = 8   #double to float is odd
                                
                                price = Decimal(lMsg[0])+0   #trick to get to round
                                count = lMsg[1]
                                size = Decimal(lMsg[2])+0   #trick to get to round
                                side = 'buy' if size > 0 else 'sell'
                                
                                self._book[product].setTradePriceSizeToZero()
                                
                                if (count == 0):
                                    if self._book[product].doUpdateBook(side, price, 0) == False:
                                        self.on_error('Missing price')
                                        self.close()
                                else:
                                    if self._book[product].doUpdateBook(side, price, abs(size)) == False:
                                        self.on_error('Missing price')
                                        self.close()
                    else:
                        print('UNKNOWN type order_book.on_message(): msg: {}'.format(msg))
                        
                elif (productID in self._currencyDictTrade):
                    
                    if msg[1] == 'te':
                        product = self._currencyDictTrade[productID]
                        self._workingProduct = product
                        self._book[product].setTradePriceSizeToZero()
                        
                        with localcontext() as ctx:
                            ctx.prec = 8   #double to float is odd
                            
                            lMsg = msg[2]  # breaking change. rest of data is not a list  [91, 'te', [397614371, 1572466610566, 0.05665804, 9220.02494116]]
                            
                            price = Decimal(lMsg[3])+0   #trick to get to round
                            size = Decimal(lMsg[2])+0   #trick to get to round
                            side = 'buy' if size > 0 else 'sell'
                            self._book[product].doUpdateTrade(side, price, abs(size))
                    
#                    if (msg[1] == 'hb' or msg[1] == 'tu' or type(msg[1]) is list):
#                        return
                    
                    
            except Exception as e:
                print('ERROR order_book.on_message(): {} msg: {}'.format(e, msg))
                
        else:
            print('unknown message {}'.format(msg))
        
        if (self._callbackHandler and self._workingProduct and self.isGood(self._workingProduct)):
            self._callbackHandler.on_message(self._workingProduct)
    
def main():
    import time

    class OrderBookConsole(OrderBook):
        ''' Logs real-time changes to the bid-ask spread to the console '''

        def __init__(self, url='wss://api-pub.bitfinex.com/ws/2', products=['BTCUSD', 'ETHUSD'], oneThreadPerProduct=False, log_to=None):
#        def __init__(self, url='wss://api2.bitfinex.com:3000/ws', products=['tBTCUSD', 'tETHUSD'], oneThreadPerProduct=False, log_to=None):
        #def __init__(self, url='wss://api2.bitfinex.com:3000/ws', products=['BTC_XMR'], log_to=None):
            OrderBook.__init__(self, url, products, oneThreadPerProduct, log_to=log_to)

            # latest values of bid-ask spread
            self._bP = {product: None for product in self.products}     # ignore leading "t" which is not in data returned
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

#    fh = open("rawTick.log", "w")
    fh = None
    order_book = OrderBookConsole(log_to=fh)
    order_book.start()
    time.sleep(10)
    print('Close OrderBook')
    order_book.close()
    
if __name__ == '__main__':
    main()
