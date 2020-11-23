import sys
if "../Common" not in sys.path: sys.path.append("../Common") # Desperation
if "../Exchanges/gemini" not in sys.path: sys.path.append("../Exchanges/gemini") # Desperation

import datetime as dt
import time

from order_book import OrderBook 
from tick_logger_base import TickLoggerBase

def main():
    
    #fh = open("tick.log", "w")
    fh = None
    
    fileName = 'Tick_gemini_{}.log'.format(time.strftime('%Y%m%d_%H%M%S'))
    
    timeToRunSec = 60*60*24    # 12 hours
    timeForReconnect = 60*60*1 # 1 hour
    timeToSleep = 1            # 1 second
    
    timeStart = dt.datetime.now()
    timeReconnect = dt.datetime.now()
    dTime = 0
    dTimeReconnect = 0
    cntLoop = 0
    while dTime < timeToRunSec:
        products=['btcusd', 'ethusd', 'ltcusd', 'ethbtc']
        orderBook = OrderBook(url='wss://api.gemini.com/v1/marketdata/', products=products, oneThreadPerProduct=True, log_to=fh)
        tickLogger = TickLoggerBase(fileName, orderBook, writeHeader = True if cntLoop == 0 else False)
        tickLogger.start()
        
        try:
            while not orderBook.isClosed() and dTime < timeToRunSec:
                time.sleep(timeToSleep)
                dTime = (dt.datetime.now() - timeStart).total_seconds()
                dTimeReconnect = (dt.datetime.now() - timeReconnect).total_seconds()
                
                if dTimeReconnect > timeForReconnect:
                    timeReconnect = dt.datetime.now()
                    dTimeReconnect = 0
                    print('Reconnect {}'.format(timeReconnect))
                    break
    
        except KeyboardInterrupt:
            tickLogger.close()
            print('Exit tickLogger loop')
            break
            
        tickLogger.close()
        cntLoop = cntLoop  + 1
    
if __name__ == '__main__':
    main()
