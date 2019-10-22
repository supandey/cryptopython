#
# Based on https://github.com/veox/python3-krakenex/blob/master/krakenex/api.py
#

import sys
if "../../Common" not in sys.path: sys.path.append("../../Common") # Desperation
if "../Exchanges/kraken" not in sys.path: sys.path.append("../Exchanges/kraken") # Desperation

import datetime as dt

from book import Book
from public_client import PublicClient
from order_rest_base import OrderBookRestBase

class OrderBook(OrderBookRestBase):
    '''Live order book updated from the Websocket Feed'''
    
    def __init__(self, url, products, intervalSec, log_to=None):
        OrderBookRestBase.__init__(self, url, products, intervalSec)
        self._book = {product : Book(product) for product in self.products}
        self._client = PublicClient()
        
    def on_open(self, threadName):
        return ('Depth', {'pair': threadName})

    def on_message(self, data):
        ''' process the received message '''
        if self._log_to:
            try:
                self._log_to.write('{} {} \n'.format(dt.datetime.now(), str(data)))
            except ValueError:
                pass  # I/O operation on closed file.
                
        errorMsg = data['error']
        if len(errorMsg) > 0:
            print('ERROR: {}'.format(errorMsg))
            self.on_error()
        
        resultDict = data['result']
        for key, value in resultDict.items():
            product = key
            asksList = value['asks']
            bidsList = value['bids']
            
            self._book[product].doUpdate(bidsList, asksList)
            self._workingProduct = product
            
        self.isGood(product)
        
        if (self._callbackHandler and self._workingProduct and self.isGood(self._workingProduct)):
            self._callbackHandler.on_message(self._workingProduct)
    
def main():
    import time

    class OrderBookConsole(OrderBook):
        ''' Logs real-time changes to the bid-ask spread to the console '''

        def __init__(self, url='https://api.kraken.com', products=['XETHZUSD', 'XXBTZUSD'], intervalSec=1, log_to=None):
            OrderBook.__init__(self, url, products, intervalSec, log_to=log_to)

            # latest values of bid-ask spread
            self._bP = {product: None for product in self.products}
            self._aP = {product: None for product in self.products}
            self._bS = {product: None for product in self.products}
            self._aS = {product: None for product in self.products}

        def on_message(self, message):
            OrderBook.on_message(self, message)
            
            product = self._workingProduct
            
            if (product == -1 or not self.isGood(product)):
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
