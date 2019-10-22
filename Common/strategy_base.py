import datetime as dt
import logging
import errno
import os
import pandas as pd

class StrategyBase:
    ''' Gets order book and calculate some variables. Call MA every X seconds '''

    def __init__(self, fileName, orderBook, writeHeader):
        
        self._orderBook = orderBook
        self._products = orderBook.products
        self._minIncr = 0.01
        
        # latest values of bid-ask spread
        self._bP = {product: None for product in self._products}
        self._aP = {product: None for product in self._products}
        self._bS = {product: None for product in self._products}
        self._aS = {product: None for product in self._products}
        self._msgCnt = 0;
        self._timeLastLogToConsole = dt.datetime.now()
        self._timeLastUpdate = {product: dt.datetime.now() for product in self._products} 
        self._dTimeToConsoleInSeconds = 5
        self._dTimeToDF = 1;
        self._maShortEMA = 2./(100+1)
        self._maLongEMA = 2./(200+1)
        self._macdSignalEMA = 2./(50+1)
        
        namesCol = ['Date', 'Name', 'qB', 'pB', 'pA', 'qA', 'pT', 'qT', 'pc', 'pc10', 'pc50', 'pc10MaShort', 'pc50MaShort', 'pc50MaLong', 'macd', 'macdSignal']
        self._dfData = {product: pd.DataFrame(columns=namesCol) for product in self._products}
    
        #'Date,Name,qB,pB,pA,qA,pT,qT,pc,pc50,pc50MaShort,pc50MaLong,macd,macdSignal'
        self._formatString = '{:%Y-%m-%d %H:%M:%S.%f}|{}|{}|{}|{}|{}|{}|{}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}'               
        
        self._logger = self._get_logger(fileName) 
        if writeHeader: 
            self._logger.info(self.niceOutputHeader())
            print('{} Start StrategyBase - Log every {} seconds to console'.format(dt.datetime.now(), self._dTimeToConsoleInSeconds))
        
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
            
            nowTime = dt.datetime.now()
            
            if (nowTime-self._timeLastUpdate[product]).total_seconds() > self._dTimeToDF:
                self._timeLastUpdate[product] = nowTime
                df = self._dfData[product]
                szDf = len(df)
                
                (bS, bP, aP, aS, tradePrice, tradeSize, exchDly,
                 bS_5, bP_5, aP_5, aS_5,
                 bS_10, bP_10, aP_10, aS_10,
                 bS_50, bP_50, aP_50, aS_50,
                 volume, tradeSide,
                 aBP, aAP, aIP, aIQ, aRst,aTyp) = self._orderBook.getMarketData(product)
                
                pc = float((bS*bP + aS*aP) / (bS+aS))
                pc10 = float((bS_10*bP_10 + aS_10*aP_10) / (bS_10+aS_10))
                pc50 = float((bS_50*bP_50 + aS_50*aP_50) / (bS_50+aS_50))
                
                pc10MaShort = self._maShortEMA*pc10 + (1-self._maShortEMA)*float(df['pc10MaShort'][-1:]) if szDf > 2 else pc10
                pc50MaShort = self._maShortEMA*pc50 + (1-self._maShortEMA)*float(df['pc50MaShort'][-1:]) if szDf > 2 else pc50
                pc50MaLong = self._maLongEMA*pc50 + (1-self._maLongEMA)*float(df['pc50MaLong'][-1:]) if szDf > 2 else pc50
                macd = pc50MaShort - pc50MaLong
                macdSignal = self._macdSignalEMA*macd + (1-self._macdSignalEMA)*float(df['macdSignal'][-1:]) if szDf > 2 else macd
                
                dataRow = [nowTime, product, float(bS), float(bP), float(aP), float(aS), float(tradePrice), float(tradeSize), pc, pc10, pc50, pc10MaShort, pc50MaShort, pc50MaLong, macd, macdSignal]
                df.loc[len(df)] = dataRow
            
                # only first one for now
                if szDf > 2 and (nowTime-self._timeLastLogToConsole).total_seconds() > self._dTimeToConsoleInSeconds and self._products[0] == product:
                    self._timeLastLogToConsole = nowTime
                    #self._orderBook.printBestBidAsk(product, 'StrategyBase - {}'.format(product))
                    #print('pc50 : {:.2f}  pc50MaShort : {:.2f} pc50MaLong : {:.2f}  macd : {:.3f} macdSignal : {:.3f}\n'.format(pc50, pc50MaShort, pc50MaLong, macd, macdSignal))
                    print('{:%Y-%m-%d %H:%M:%S}: {:.2f}|{:.2f}|{:.2f}|{:.2f} - {:.2f}|{:.2f}|{:.2f}|{:.2f}|{:.2f}'.format(dt.datetime.now(), bS, bP, aP, aS, pc50, pc50MaShort, pc50MaLong, macd, macdSignal))
                    self._logger.info(self.niceOutput(dataRow))  
                
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
        
        print('{} StrategyBase::on_close'.format(dt.datetime.now()))
        handlers = self._logger.handlers[:]
        for handler in handlers:
            handler.close()
            self._logger.removeHandler(handler)
            
    def start(self):
        self._orderBook.start()
        
    def close(self):
        self._orderBook.close()
        
    def getDf(self):
        return self._dfData
    
    def niceOutputHeader(self):
        return 'Date,Name,qB,pB,pA,qA,pT,qT,pc,pc10,pc50,pc10MaShort,pc50MaShort,pc50MaLong,macd,macdSignal'
    
    def niceOutput(self, dataRow):
        return self._formatString.format(dataRow[0], dataRow[1], dataRow[2], dataRow[3], dataRow[4],
                                         dataRow[5], dataRow[6], dataRow[7], dataRow[8], dataRow[9],
                                         dataRow[10], dataRow[11], dataRow[12], dataRow[13], dataRow[14],
                                         dataRow[15])
        

def main():
    import time
    
    import sys
    #if "../Exchanges/gdax" not in sys.path: sys.path.append("../Exchanges/gdax") # Desperation
    #if "../Exchanges/hitbtc" not in sys.path: sys.path.append("../Exchanges/hitbtc") # Desperation
    if "../Exchanges/bitfinex" not in sys.path: sys.path.append("../Exchanges/bitfinex") # Desperation
    from order_book import OrderBook 
    
    #fh = open("tick.log", "w")
    fh = None
    
    fileName = 'Strategy_Base_{}.log'.format(time.strftime('%Y%m%d_%H%M%S'))
    
    timeToRunSec = 60    # 12 minutes
    timeToSleep = 1          #1 second
    
    timeStart = dt.datetime.now()
    dTime = 0
    cntLoop = 0
    dfData = None
    while dTime < timeToRunSec:
        orderBook = OrderBook(url='wss://api2.bitfinex.com:3000/ws', products=['BTCUSD', 'ETHUSD'], oneThreadPerProduct=False, log_to=fh)
        strategy = StrategyBase(fileName, orderBook, writeHeader = True if cntLoop == 0 else False)
        orderBook.setCallbackHandler(strategy)
        strategy.start()
        
        while not orderBook.isClosed() and dTime < timeToRunSec:
            time.sleep(timeToSleep)
            dTime = (dt.datetime.now() - timeStart).total_seconds()
         
        dfData = strategy.getDf();
        strategy.close()
        cntLoop = cntLoop  + 1
    
#    for product in dfData:
#        print('\n\n {} \n {}'.format(product, dfData[product].describe()))
        
    return dfData
        
            
if __name__ == '__main__':
    dfData = main()
