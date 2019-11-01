# https://api.hitbtc.com/#socket-api-reference

import sys
if "../../Common" not in sys.path: sys.path.append("../../Common") # Desperation
if "../Exchanges/hitbtc" not in sys.path: sys.path.append("../Exchanges/hitbtc") # Desperation

import datetime as dt
import pytz 

from book import Book
from public_client import PublicClient
from order_book_base import OrderBookBase

class OrderBook(OrderBookBase):
    '''Live order book updated from the Websocket Feed'''
    
    def __init__(self, url, products, oneThreadPerProduct, log_to=None):
        OrderBookBase.__init__(self, url, products, oneThreadPerProduct)
        self._book = {product : Book(product) for product in self.products}
        self._client = PublicClient()
        self._log_to = log_to
        
        print('Init OrderBook. Create {}'.format(self._book.keys()))
        
    def on_subscribe(self, threadName):
        for product in self.products:
            msg = {'method': 'subscribeOrderbook', 'params': {'symbol': product},'id': 123}
            self.subscribe(threadName, msg)
        
        for product in self.products:
            msg = {'method': 'subscribeTrades', 'params': {'symbol': product},'limit': 100,'id': 123}
            self.subscribe(threadName, msg)

    def on_message(self, msg):
        ''' process the received message '''
        if self._log_to:
            try:
                self._log_to.write('{} : {} \n'.format(dt.datetime.now(), msg))
            except ValueError:
                pass  # I/O operation on closed file.
                
        self._workingProduct = None  
        
        try:
            if 'result' in msg:         #{'jsonrpc': '2.0', 'result': True, 'id': 123, 'threadName': 'MY_THREAD'} 
                return
                
            method = msg['method']
            
            if method == 'snapshotOrderbook' or method == 'updateOrderbook':
                dataMsg = msg['params']
                
                product = dataMsg['symbol']
                if product not in self._book:
                    return
                
                self._workingProduct = product
                self._book[product].setTradePriceSizeToZero()
                
                nowTime = dt.datetime.now(self._local_timezone)
                try:
                    exchTimeUTC = dt.datetime.strptime(dataMsg['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')       #'timestamp': '2019-10-31T20:38:45.563Z'}
                    exchTime = exchTimeUTC.replace(tzinfo=pytz.utc).astimezone(self._local_timezone)        # convert to lcoal time
                except:
                    exchTime = nowTime
                
                exchDly = (nowTime - exchTime).total_seconds();
                self._book[product].setExchDly(exchDly)
            
                sequence = dataMsg['sequence']
                
                if self._sequence[product] != -1:
                    if sequence <= self._sequence[product]:
                        # ignore older messages (e.g. before order book initialization from getProductOrderBook)
                        return
                    elif sequence > self._sequence[product] + 1:
                        errMsg = 'Error: messages missing seq# ({} - {}).'.format(sequence, self._sequence[product])
                        self.on_error(errMsg)
                        self.close()
                        return
                
                if method == 'snapshotOrderbook': 
                    self._book[product].doUpdateBook('buy', dataMsg['bid'])
                    self._book[product].doUpdateBook('sell', dataMsg['ask'])
                    self._sequence[product] = sequence
                elif method == 'updateOrderbook' and self._sequence[product] != -1:       # only update after snapshotOrderbook
                    self._book[product].doUpdateBook('buy', dataMsg['bid'])
                    self._book[product].doUpdateBook('sell', dataMsg['ask'])
                    self._sequence[product] = sequence
            
            elif method == 'snapshotTrades' or method == 'updateTrades':
                dataMsg = msg['params']
                
                product = dataMsg['symbol']
                if product not in self._book:
                    return
                
                self._workingProduct = product
                self._book[product].doUpdateTrade(dataMsg['data'])
            else:
                print('Unknown OrderBook::on_message() msg : {}'.format(msg))
    
        
            if (self._callbackHandler and self._workingProduct and self.isGood(self._workingProduct)):
                self._callbackHandler.on_message(self._workingProduct)
                    
        except Exception as e:
            print('ERROR OrderBook::on_message() error: {} msg : {}'.format(e, msg))
    
def main():
    import time

    class OrderBookConsole(OrderBook):
        ''' Logs real-time changes to the bid-ask spread to the console '''

#        def __init__(self, url='ws://api.hitbtc.com:80/market', products=['BTCUSD', 'ETHUSD'], oneThreadPerProduct=False, log_to=None):
        def __init__(self, url='wss://api.hitbtc.com/api/2/ws', products=['BTCUSD', 'ETHUSD'], oneThreadPerProduct=False, log_to=None):
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

#    fh = open("rawTick.log", "w")
    fh = None
    order_book = OrderBookConsole(log_to=fh)
    order_book.start()
    time.sleep(10)
    print('Close OrderBook')
    order_book.close()
    
if __name__ == '__main__':
    main()
