import sys
if "../Common" not in sys.path: sys.path.append("../Common") # Desperation
if "../Exchanges/bitfinex" not in sys.path: sys.path.append("../Exchanges/bitfinex") # Desperation

import datetime as dt
import time

from order_book import OrderBook 
from tick_logger_base import TickLoggerBase

def main():
    
    #fh = open("tick.log", "w")
    fh = None
    
    fileName = 'Tick_bitfinex_{}.log'.format(time.strftime('%Y%m%d_%H%M%S'))
    
    timeToRunSec = 60*60*24    # 12 hours
    timeToSleep = 1            # 1 second
    
    timeStart = dt.datetime.now()
    dTime = 0
    cntLoop = 0
    while dTime < timeToRunSec:
        products=['BTCUSD', 'ETHUSD', 'LTCUSD', 'OMGUSD', 'IOTAUSD', 'ETHBTC', 'LTCBTC', 'OMGBTC', 'IOTABTC', 'EOSUSD', 'XRPUSD', 'SANUSD']
        #products=['BTCUSD', 'ETHUSD']
        orderBook = OrderBook(url='wss://api2.bitfinex.com:3000/ws', products=products, oneThreadPerProduct=False, log_to=fh)
        tickLogger = TickLoggerBase(fileName, orderBook, writeHeader = True if cntLoop == 0 else False)
        tickLogger.start()
        
        try:
            while not orderBook.isClosed() and dTime < timeToRunSec:
                time.sleep(timeToSleep)
                dTime = (dt.datetime.now() - timeStart).total_seconds()
        except KeyboardInterrupt:
            tickLogger.close()
            print('Exit tickLogger loop')
            break
            
        tickLogger.close()
        cntLoop = cntLoop  + 1
    
if __name__ == '__main__':
    main()
