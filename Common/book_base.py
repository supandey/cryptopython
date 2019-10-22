import datetime as dt
from decimal import Decimal

class BookBase():
    '''
    Store orders as a dictionary of prices. 
    Some exchanges are ITCH like, some CME like, some just different. 
    Here we just define a common interface to data and common functions (ie printBestBidAsk).
    Assume all prices and sizes are Decimal to ease key lookup in dictionaries.
    '''
    def __init__(self, product):
        self._product = product
        self.initialize()
        
    def initialize(self):
        self._asks = {}         # nothing facny like RBTree or PriorityQueue for now. Perhaps list to sort in place and then bisect?
        self._bids = {}
        self._bestBidPrice = Decimal(-1e9)
        self._bestAskPrice = Decimal(1e9)
        self._exchDly = 0
        self._tradePrice = Decimal(0)
        self._tradeSize = Decimal(0)
        self._volume = Decimal(0) 
        self._tradeSide = 'U'
        self._aBP = Decimal(0) 
        self._aAP = Decimal(0) 
        self._aIP = Decimal(0) 
        self._aIQ = Decimal(0) 
        self._aRst = 0
        self._aTyp = 'U'
        self._good = False
        
        # time|product|bS|bP|aP|aS|tP|tS|exchDly|bS_5|bP_5|aP_5|aS_5|bS_10|bP_10|aP_10|aS_10|bS_50|bP_50|aP_50|aS_50|vol|trdSd|aBP|aAP|aIP|aIQ|aRst|aTyp
        self._formatString = '{:%Y-%m-%d %H:%M:%S.%f}|{}|{}|{}|{}|{}|{}|{}|{}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{}|{}|{}|{}|{}|{}|{}|{}'                 
        
    def setExchDly(self, val):
        self._exchDly = val
        
    def setTradePriceSizeToZero(self):
        self._tradePrice = Decimal(0)
        self._tradeSize = Decimal(0)
        self._tradeSide ='U'
        self._aBP = Decimal(0) 
        self._aAP = Decimal(0) 
        self._aIP = Decimal(0) 
        self._aIQ = Decimal(0) 
        self._aRst = 0
        self._aTyp = 'U'
        
    def setTradePriceSize(self, price, size, side = 'U'):
        self._tradePrice = price
        self._tradeSize = size
        self._tradeSide = side
        self._volume += Decimal(size)
        
    def setAuction(self, aBP, aAP, aIP, aIQ, aRst, aTyp):
        self._aBP = aBP
        self._aAP = aAP
        self._aIP = aIP
        self._aIQ = aIQ
        self._aRst = aRst
        self._aTyp = aTyp
        
    def setBestBidAsk(self, side, price):
        if side == 'buy':
            if price > self._bestBidPrice:
                self._bestBidPrice = price
        else:
            if price < self._bestAskPrice:
                self._bestAskPrice = price
                
    def findBestBidAsk(self, side):
        # sometimes need to find from scratch
        queue = self._bids if side == 'buy' else self._asks
        if len(queue) > 0:
            if side == 'buy':
                self._bestBidPrice = max(queue.keys())
            else:
                self._bestAskPrice = min(queue.keys())
        else:
            if side == 'buy':
                self._bestBidPrice = Decimal(-1e9)
            else:
                self._bestAskPrice = Decimal(1e9)
    
    def isGood(self):
        if self._bestAskPrice < Decimal(1e8) and self._bestBidPrice > Decimal(-1e8):
            self._good = True
        else:
            self._good = False
            
        return self._good

    def getBestAsk(self):
        if (self._bestAskPrice in self._asks):
            return (self._bestAskPrice,  sum(self._asks[self._bestAskPrice].values()))
        else:
            print('Error: Cant find _bestAskPrice {}'.format(self._bestAskPrice))
            self._bestAskPrice = min(self._asks.keys())
            return (self._bestAskPrice,  sum(self._asks[self._bestAskPrice].values()))

    def getBestBid(self):
        if (self._bestBidPrice in self._bids):
            return (self._bestBidPrice, sum(self._bids[self._bestBidPrice].values()))
        else:
            print('Error: Cant find _bestBidPrice {}'.format(self._bestBidPrice))
            self._bestBidPrice = max(self._bids.keys())
            return (self._bestBidPrice, sum(self._bids[self._bestBidPrice].values()))
        
    def getTopBidAsk(self):
        bP, bS = self.getBestBid()
        aP, aS = self.getBestAsk()
        return (bS, bP, aP, aS)
        
    def getTopNLvls(self, numLvl, sortedBidKeys, sortedAskKeys):
        try:
            nB = len(sortedBidKeys)
            nA = len(sortedAskKeys)
            
            bS = Decimal(0)
            bP = Decimal(0)
            aP = Decimal(0)
            aS = Decimal(0)
            
            # bids
            sz = min(nB, numLvl)
            for i in range(sz):
                price = sortedBidKeys[i]
                qty = sum(self._bids[price].values())
                bP = (bP*bS + price*qty) / (bS + qty)
                bS = bS + qty
                
            # asks
            sz = min(nA, numLvl)
            for i in range(sz):
                price = sortedAskKeys[i]
                qty = sum(self._asks[price].values())
                aP = (aP*aS + price*qty) / (aS + qty)
                aS = aS + qty
                 
            return (bS, bP, aP, aS)
        except KeyError:
            print('KeyError in getTopNLvls')
            return (Decimal(0),Decimal(0),Decimal(0),Decimal(0))
        
    def getAIQ(self):
        return self._aIQ
        
    def printBestBidAsk(self, header):
        try:
            if (self.isGood()):
                bS, bP, aP, aS = self.getTopBidAsk()
                print('{}\t {}: \tbid: {:.3f} @ {:.2f} \t ask: {:.3f} @ {:.2f}'
                      .format(dt.datetime.now(), header, bS, bP, aS, aP))
            else:
                print('{} One side is empty'.format(header))
        except KeyError:
            print('{} KeyError in printBestBidAsk'.format(header))
    
    def niceOutputHeader(self):
        return 'Date,Name,qB,pB,pA,qA,pT,qT,Dly,qB_5,pB_5,pA_5,qA_5,qB_10,pB_10,pA_10,qA_10,qB_50,pB_50,pA_50,qA_50,vol,trdSd,aBP,aAP,aIP,aIQ,aRst,aTyp'
        
    def niceOutput(self):
        (bS, bP, aP, aS, tradePrice, tradeSize, exchDly,
         bS_5, bP_5, aP_5, aS_5,
         bS_10, bP_10, aP_10, aS_10,
         bS_50, bP_50, aP_50, aS_50,
         volume, tradeSide,
         aBP, aAP, aIP, aIQ, aRst,aTyp) = self.getMarketData();
         
        return self._formatString.format(dt.datetime.now(), self._product, bS, bP, aP, aS, 
                                         tradePrice, tradeSize, exchDly,
                                         bS_5, bP_5, aP_5, aS_5,
                                         bS_10, bP_10, aP_10, aS_10,
                                         bS_50, bP_50, aP_50, aS_50,
                                         volume, tradeSide,
                                         aBP, aAP, aIP, aIQ, aRst, aTyp)
        
    def getMarketData(self):
        if (self.isGood()):
            
            sortedBidKeys = sorted(self._bids.keys(), reverse=True)  # TODO HIGH: Use iterkeys()?
            sortedAskKeys = sorted(self._asks.keys())                # TODO HIGH: Use iterkeys()?
            
            numLvl = 5
            (bS_5, bP_5, aP_5, aS_5) = self.getTopNLvls(numLvl, sortedBidKeys, sortedAskKeys)
            
            numLvl = 10
            (bS_10, bP_10, aP_10, aS_10) = self.getTopNLvls(numLvl, sortedBidKeys, sortedAskKeys)
            
            numLvl = 50
            (bS_50, bP_50, aP_50, aS_50) = self.getTopNLvls(numLvl, sortedBidKeys, sortedAskKeys)
            
            bS, bP, aP, aS = self.getTopBidAsk()
            return (bS, bP, aP, aS, 
                   self._tradePrice, self._tradeSize, self._exchDly,
                   bS_5, bP_5, aP_5, aS_5,
                   bS_10, bP_10, aP_10, aS_10,
                   bS_50, bP_50, aP_50, aS_50,
                   self._volume, self._tradeSide,
                   self._aBP, self._aAP, self._aIP, self._aIQ, 
                   self._aRst,self._aTyp)
        else:
            return (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'U',0,0,0,0,0,'U')
        
            
def main():
    book = BookBase('btcusd')
    print(book.niceOutput())

if __name__ == '__main__':
    main()
    