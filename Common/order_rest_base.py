import tzlocal

from rest_client import RestClient

class OrderBookRestBase(RestClient):
    '''Live order book updated from the Websocket Feed'''
    
    def __init__(self, url, products, intervalSec, log_to=None):
        RestClient.__init__(self, url, products, intervalSec)
        self._book = {}     # derived class has to populate this.
        self._client = {}   # derived class has to populate this.
        self._sequence = {product : -1 for product in self.products}
        self._workingProduct = None
        self._callbackHandler = None  # hook for other classes to get messages
        self._callClose = False;
        self._log_to = log_to
        self._local_timezone = tzlocal.get_localzone() 
        if self._log_to: assert hasattr(self._log_to, 'write')
        
    def on_subscribe(self, threadName):
        pass

    def on_message(self, data):
        pass
        
    def on_close(self):
        if self._log_to: self._log_to.close()
        if self._callbackHandler: self._callbackHandler.on_close()
     
    def on_error(self):
        self._sequence = {product : -1 for product in self.products}
        for product in  self.products:
            self._book[product].initialize()
        
        self.close()
        self._callClose = True
    
    def isGood(self, product):
        return self._book[product].isGood()

    def getTopBidAsk(self, product):
        return self._book[product].getTopBidAsk()
    
    def getAIQ(self, product):
        return self._book[product].getAIQ()
        
    def printBestBidAsk(self, product, header):
        return self._book[product].printBestBidAsk(header)
    
    def niceOutput(self, product):
        return self._book[product].niceOutput()
    
    def niceOutputHeader(self, product):
        return self._book[product].niceOutputHeader()
    
    def products(self):
        return self.products
    
    def isClosed(self):
        return self._callClose
    
    def setCallbackHandler(self, callbackHandler):
        self._callbackHandler = callbackHandler
    
def main():
    pass
    #obrb = OrderBookRestBase('https://api.kraken.com', ['XETHZUSD', 'XXBTZUSD'], 1)
    #obrb.close()
    
if __name__ == '__main__':
    main()
