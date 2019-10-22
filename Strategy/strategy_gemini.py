import sys
if "../Common" not in sys.path: sys.path.append("../Common") # Desperation
if "../Exchanges/gemini" not in sys.path: sys.path.append("../Exchanges/gemini") # Desperation

import datetime as dt
import time

from order_book import OrderBook 
from strategy_base import StrategyBase

# extenf Straegytegy Base here and call orders logic. Use RLock
class Strategy(StrategyBase):
    
    def __init__(self, fileName, orderBook, writeHeader):
        StrategyBase.__init__(self, fileName, orderBook, writeHeader)
        self._openOrder = False
        
    def on_message(self, product):
        StrategyBase.on_message(self, product)
        
        print('Enter on_message')
        
        # do order logic here based on market data.
        # make sure to call once a second in _listen to monitor order health

def main():
    
    #fh = open("tick.log", "w")
    fh = None
    
    fileName = 'Strategy_gemini_{}.log'.format(time.strftime('%Y%m%d_%H%M%S'))
    
    #timeToRunSec = 60*60*24    # 12 hours
    timeToRunSec = 60
    timeToSleep = 1            # 1 second
    
    timeStart = dt.datetime.now()
    dTime = 0
    cntLoop = 0
    dfData = None
    while dTime < timeToRunSec:
        products=['btcusd', 'ethusd']
        orderBook = OrderBook(url='wss://api.gemini.com/v1/marketdata/', products=products, oneThreadPerProduct=True, log_to=fh)
        strategy = Strategy(fileName, orderBook, writeHeader = True if cntLoop == 0 else False)
        orderBook.setCallbackHandler(strategy)
        strategy.start()
        
        try:
            while not orderBook.isClosed() and dTime < timeToRunSec:
                time.sleep(timeToSleep)
                dTime = (dt.datetime.now() - timeStart).total_seconds()
        except KeyboardInterrupt:
            strategy.close()
            print('Exit tickLogger loop')
            break
          
        dfData = strategy.getDf();
        strategy.close()
        cntLoop = cntLoop  + 1
        
    for product in dfData:
        print('\n\n {} \n {}'.format(product, dfData[product].describe()))
        
    return dfData
    
if __name__ == '__main__':
    dfData = main()