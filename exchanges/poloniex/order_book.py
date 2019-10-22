import sys
if "../../Common" not in sys.path: sys.path.append("../../Common") # Desperation
if "../Exchanges/poloniex" not in sys.path: sys.path.append("../Exchanges/poloniex") # Desperation

import datetime as dt
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
        self._currencyDict = {}
        
    def on_subscribe(self, threadName):
        for product in self.products:
            msg = {'command': 'subscribe', 'channel': product}
            self.subscribe(threadName, msg)

    def on_message(self, msg):
        ''' process the received message '''
        if self._log_to:
            try:
                self._log_to.write('{} : {} \n'.format(dt.datetime.now(), msg))
            except ValueError:
                pass  # I/O operation on closed file.
                
        if (len(msg) < 3):      # skip heartbeats,.... ie [1010]
            return
            
        productID = msg[0]
        sequence = msg[1]
        msgBody = msg[2]
        
        product = self._currencyDict.get(productID, None)
        self._workingProduct = product
        
        for data in msgBody:
            dataType = data[0]
            if (dataType == 'i'):
                dataDict = data[1]
                self.getSnapShot(productID, sequence, dataDict)
            elif (self._sequence[product] != -1):
                
                if sequence <= self._sequence[product]:
                    # ignore older messages (e.g. before order book initialization from getProductOrderBook)
                    return
                elif sequence > self._sequence[product] + 1:
                    errMsg = 'Error: messages missing ({} - {}). Re-initializing websocket.'.format(sequence, self._sequence[product])
                    self.on_error(errMsg)
                    self.close()
                
                self._book[product].setTradePriceSizeToZero()
                
                if (dataType == 'o'):
                    side = int(data[1])
                    price = Decimal(data[2])
                    size = Decimal(data[3])
                    self._book[product].doUpdateBook('buy' if side == 1 else 'sell', price, size)
                elif (dataType == 't'):
                    side = int(data[2])
                    price = Decimal(data[3])
                    size = Decimal(data[4])
                    self._book[product].doUpdateTrade('buy' if side == 1 else 'sell', price, size)
        
        if (product != None):
            self._sequence[product] = sequence
            self.isGood(product)
        
        if (self._callbackHandler and self._workingProduct and self.isGood(self._workingProduct)):
            self._callbackHandler.on_message(self._workingProduct)
    
    def getSnapShot(self, productID, sequence, dataDict):
        
        self._currencyDict[productID] = dataDict['currencyPair']
        product = self._currencyDict[productID]
        self._sequence[product] = sequence
        
        asks = dataDict['orderBook'][0]
        bids = dataDict['orderBook'][1]
        self._book[product].doSnapShot(bids, asks)
    
def main():
    import time

    class OrderBookConsole(OrderBook):
        ''' Logs real-time changes to the bid-ask spread to the console '''

        def __init__(self, url='wss://api2.poloniex.com', products=['BTC_XMR', 'USDT_REP'], oneThreadPerProduct=False, log_to=None):
        #def __init__(self, url='wss://api2.poloniex.com', products=['BTC_XMR'], oneThreadPerProduct=False, log_to=None):
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
    