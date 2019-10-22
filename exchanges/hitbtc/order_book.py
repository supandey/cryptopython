import sys
if "../../Common" not in sys.path: sys.path.append("../../Common") # Desperation
if "../Exchanges/hitbtc" not in sys.path: sys.path.append("../Exchanges/hitbtc") # Desperation

import datetime as dt

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
        pass  # subscribe We always get all symbols 

    def on_message(self, msg):
        ''' process the received message '''
        if self._log_to:
            try:
                self._log_to.write('{} : {} \n'.format(dt.datetime.now(), msg))
            except ValueError:
                pass  # I/O operation on closed file.
                
        self._workingProduct = None  
        
        try:
            if ('MarketDataSnapshotFullRefresh' in msg):
                dataMsg = msg['MarketDataSnapshotFullRefresh']
                product = dataMsg['symbol']
                
                if (product in self.products):
                    
                    sequence = dataMsg['snapshotSeqNo']
                    timestampInMS = dataMsg['timestamp']
                    asks = dataMsg['ask']
                    bids = dataMsg['bid']
                    
                    nowTime = dt.datetime.now()
                    try:
                        exchTime = dt.datetime.fromtimestamp(timestampInMS / 1000)  # thisis local
                    except:
                        exchTime = nowTime
                    
                    exchDly = (nowTime - exchTime).total_seconds();
                    self._book[product].setExchDly(exchDly)
                    
                    self._workingProduct = product
                    self._sequence[product] = sequence
                    self._book[product].doSnapShot(bids, asks)
                    
            elif ('MarketDataIncrementalRefresh' in msg):
                dataMsg = msg['MarketDataIncrementalRefresh']
                product = dataMsg['symbol']
                
                if (product in self.products and self._sequence[product] != -1):
                    sequence = dataMsg['seqNo']
                   
                    if sequence <= self._sequence[product]:
                        # ignore older messages (e.g. before order book initialization from getProductOrderBook)
                        return
                    elif sequence > self._sequence[product] + 1:
                        print('Error: messages missing ({} - {}). Re-initializing websocket.'.format(sequence, self._sequence[product]))
                        self._book[product].initialize()
                        return
                    
                    timestampInMS = dataMsg['timestamp']
                    nowTime = dt.datetime.now()
                    try:
                        exchTime = dt.datetime.fromtimestamp(timestampInMS / 1000)  # thisis local
                    except:
                        exchTime = nowTime
                    
                    exchDly = (nowTime - exchTime).total_seconds();
                    self._book[product].setExchDly(exchDly)
                    
                    asks = dataMsg['ask']
                    bids = dataMsg['bid']
                    trades = dataMsg['trade']
                    
                    self._book[product].setTradePriceSizeToZero()
                    self._workingProduct = product
                    self._sequence[product] = sequence
                    self._book[product].doUpdateBook('buy', bids)
                    self._book[product].doUpdateBook('sell', asks)
                    self._book[product].doUpdateTrade(trades)
                    
            if (self._callbackHandler and self._workingProduct and self.isGood(self._workingProduct)):
                self._callbackHandler.on_message(self._workingProduct)
                    
        except Exception as e:
            print('ERROR OrderBook::on_message() error: {} msg : {}'.format(e, msg))
    
def main():
    import time

    class OrderBookConsole(OrderBook):
        ''' Logs real-time changes to the bid-ask spread to the console '''

        def __init__(self, url='ws://api.hitbtc.com:80/market', products=['BTCUSD', 'ETHUSD'], oneThreadPerProduct=False, log_to=None):
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
