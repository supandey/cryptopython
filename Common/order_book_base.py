import tzlocal
import datetime as dt

from websocket_client import WebsocketClient

class OrderBookBase(WebsocketClient):
    '''Live order book updated from the Websocket Feed'''
    
    def __init__(self, url, products, oneThreadPerProduct, log_to=None):
        WebsocketClient.__init__(self, url, products, oneThreadPerProduct)
        self._book = {}     # derived class has to populate this.
        self._client = {}   # derived class has to populate this.
        self._sequence = {product : -1 for product in self.products}
        self._workingProduct = None
        self._callbackHandler = None  # hook for other classes to get messages
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
     
    def on_error(self, errMsg):
        #WebsocketClient.on_error(self, errMsg)  NoO DO NOT call as I dont want to stop. Call stop explicitley.
        print('\n {} ERROR {}'.format(dt.datetime.now(), errMsg))
        
        self._sequence = {product : -1 for product in self.products}
        for product in  self.products:
            self._book[product].initialize()
    
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
    
    def getMarketData(self, product):
        return self._book[product].getMarketData()
    
    def niceOutputHeader(self, product):
        return self._book[product].niceOutputHeader()
    
    def products(self):
        return self.products
    
    def isClosed(self):
        return self.stop
    
    def setCallbackHandler(self, callbackHandler):
        self._callbackHandler = callbackHandler
    
def main():
    pass
    
if __name__ == '__main__':
    main()
