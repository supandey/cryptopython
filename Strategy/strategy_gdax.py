import sys
if "../Common" not in sys.path: sys.path.append("../Common") # Desperation
if "../Exchanges/gdax" not in sys.path: sys.path.append("../Exchanges/gdax") # Desperation

import datetime as dt
import time

from order_book import OrderBook 
from strategy_base import StrategyBase

# extenf Straegytegy Base here and call orders logic. Use RLock
class Strategy(StrategyBase):
    
    def __init__(self, fileName, orderBook, writeHeader):
        StrategyBase.__init__(self, fileName, orderBook, writeHeader)
        self._openOrder = False
        
        self._minIncr = 0.01
        self._scale_BTC = 10
        self._risk_BTC = 600
        self._profit_BTC = 800
        self._scratch_BTC = 200
        
        self._qty = 1;
        self._buyPrice = -1
        self._sellPrice = -1
        self._pnl = 0
        
    def on_message(self, product):
        StrategyBase.on_message(self, product)
        
        # do order logic here based on market data.
        # make sure to call once a second in _listen to monitor order health
        
        if self._openOrder == False:
            buy, sell, pB, pA = self.signalBuySell(self._scale_BTC, self._minIncr)
            
            if buy:
                self._buyPrice = pA
                self._openOrder == True
                self._pnl = self._pnl - self._buyPrice*self._qty
                
            if sell:
                self._sellPrice = pB
                self._openOrder == True
                self._pnl = self._pnl + self._sellPrice*self._qty
        
    def signalBuySell(self, scale, minIncr):
        
        df = self._dfData['BTC-USD']
        
        pA = df['pA'].iloc[-1] 
        pB = df['pB'].iloc[-1]
        spread = pA - pB
        
        sell = ((df['macdSignal'].iloc[-1] < -10*scale*minIncr) &
                (df['macd'].iloc[-1] < df['macdSignal'].iloc[-1] - scale*minIncr) &
                (spread < 3*minIncr))
    
        buy = ((df['macdSignal'].iloc[-1] > 10*scale*minIncr) &
                    (df['macd'].iloc[-1] > df['macdSignal'].iloc[-1] + scale*minIncr) &
                    (spread < 3*minIncr))
        
        return buy, sell, pB, pA
            

def main():
    
    #fh = open("tick.log", "w")
    fh = None
    
    fileName = 'Strategy_gdax_{}.log'.format(time.strftime('%Y%m%d_%H%M%S'))
    
    #timeToRunSec = 60*60*24    # 12 hours
    timeToRunSec = 60*60*5
    timeToSleep = 1            # 1 second
    
    timeStart = dt.datetime.now()
    dTime = 0
    cntLoop = 0
    dfData = None
    while dTime < timeToRunSec:
        products=['BTC-USD', 'ETH-USD', 'LTC-USD']
        orderBook = OrderBook(url='wss://ws-feed.gdax.com', products=products, oneThreadPerProduct=False, log_to=fh)
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