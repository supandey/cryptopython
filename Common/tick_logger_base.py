import datetime as dt
import logging
import errno
import os

class TickLoggerBase:
    ''' Logs real-time changes to the bid-ask spread to file '''

    def __init__(self, fileName, orderBook, writeHeader):
        
        self._orderBook = orderBook
        orderBook.setCallbackHandler(self)
        
        # latest values of bid-ask spread
        self._bP = {product: None for product in orderBook.products}
        self._aP = {product: None for product in orderBook.products}
        self._bS = {product: None for product in orderBook.products}
        self._aS = {product: None for product in orderBook.products}
        self._msgCnt = 0;
        self._timeStart = dt.datetime.now()
        self._dTimeToConsoleInSeconds = 300
        
        self._logger = self._get_logger(fileName)
        if writeHeader: 
            self._logger.info(orderBook.niceOutputHeader(orderBook.products[0]))
            print('{} Start TickLogger - Log every {} seconds to console'.format(dt.datetime.now(), self._dTimeToConsoleInSeconds))

    def on_message(self, product):
        
        # Calculate newest bid-ask spread
        bS, bP, aP, aS = self._orderBook.getTopBidAsk(product)
        aIQ = self._orderBook.getAIQ(product)

        if (self._bP[product] == bP and 
            self._aP[product] == aP and 
            self._bS[product] == bS and 
            self._aS[product] == aS and 
            aIQ < 1):
            # If there are no changes to the bid-ask spread since the last update, no need to print
            pass
        else:
            # If there are differences, update the cache
            self._msgCnt = self._msgCnt + 1
            self._bP[product] = bP
            self._aP[product] = aP
            self._bS[product] = bS
            self._aS[product] = aS
            
            self._logger.info(self._orderBook.niceOutput(product))
            
            nowTime = dt.datetime.now()
            if (nowTime-self._timeStart).total_seconds() > self._dTimeToConsoleInSeconds:
                self._timeStart = nowTime
                print(self._orderBook.niceOutput(product))
            
    def _get_logger(self, fileName):
        '''get a logger with name of the instance'''
        
        if os.path.exists(fileName):
            os.remove(fileName)
            
        try:
        	os.makedirs('data')
        except OSError as exception:
        	if exception.errno != errno.EEXIST:
        		raise
        
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        formatterFH = logging.Formatter('%(message)s')
        
        file_handler = logging.FileHandler('data\\'+fileName)
        file_handler.setFormatter(formatterFH)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        
        return logger

    def on_close(self):
        
        print('{} TickLoggerBase::on_close'.format(dt.datetime.now()))
        handlers = self._logger.handlers[:]
        for handler in handlers:
            handler.close()
            self._logger.removeHandler(handler)
            
    def start(self):
        self._orderBook.start()
        
    def close(self):
        self._orderBook.close()
    
def main():
    import time
    
    import sys
    #if "../Exchanges/gdax" not in sys.path: sys.path.append("../Exchanges/gdax") # Desperation
    #if "../Exchanges/hitbtc" not in sys.path: sys.path.append("../Exchanges/hitbtc") # Desperation
    if "../Exchanges/bitfinex" not in sys.path: sys.path.append("../Exchanges/bitfinex") # Desperation
    from order_book import OrderBook 
    
    #fh = open("tick.log", "w")
    fh = None
    
    fileName = 'Tick_Gdax_{}.log'.format(time.strftime('%Y%m%d_%H%M%S'))
    
    timeToRunSec = 60    # 12 minutes
    timeToSleep = 1          #1 second
    
    timeStart = dt.datetime.now()
    dTime = 0
    cntLoop = 0
    while dTime < timeToRunSec:
        orderBook = OrderBook(url='wss://api2.bitfinex.com:3000/ws', products=['BTCUSD', 'ETHUSD'], oneThreadPerProduct=False, log_to=fh)
        tickLogger = TickLoggerBase(fileName, orderBook, writeHeader = True if cntLoop == 0 else False)
        tickLogger.start()
        
        while not orderBook.isClosed() and dTime < timeToRunSec:
            time.sleep(timeToSleep)
            dTime = (dt.datetime.now() - timeStart).total_seconds()
            
        tickLogger.close()
        cntLoop = cntLoop  + 1
    
#products=['BTCUSD', 'ETHUSD', 'LTCUSD', 'ETHBTC', 'LTCBTC', 'DASHUSD', 'XMRUSD', 'ZECUSD']
#orderBook = OrderBook(url='ws://api.hitbtc.com:80/market', products=products, oneThreadPerProduct=False, log_to=fh)
        
#orderBook = OrderBook(url='wss://ws-feed.gdax.com', products=['BTC-USD', 'ETH-USD'], oneThreadPerProduct=False, log_to=fh)
#tickLogger = TickLoggerBase(fileName, orderBook, writeHeader = True if cntLoop == 0 else False)
        
#products=['BTCUSD', 'ETHUSD']
#orderBook = OrderBook(url='wss://api2.bitfinex.com:3000/ws', products=products, oneThreadPerProduct=False, log_to=fh)
    
if __name__ == '__main__':
    main()



