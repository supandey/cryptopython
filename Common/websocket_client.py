#
# Based on https://github.com/danpaquin/gdax-python and https://github.com/Seratna/GDAX-python
#

import json
import time
import datetime as dt
from threading import Thread
from websocket import create_connection, WebSocketConnectionClosedException

class WebsocketClient:
    ''' Open market data connection to Exchange'''
    
    def __init__(self, url, products, oneThreadPerProduct):
        self.url = url
        self.products = products
        self.oneThreadPerProduct = oneThreadPerProduct;
        self.stop = False
        self.ws = {}
        self.thread = {}

    def start(self):
        self.stop = False
        self.on_open()
        if self.oneThreadPerProduct:
            for threadName in self.products:
                print('Create thread for {}'.format(threadName))
                self.thread[threadName] = Thread(target=self._go, args=(threadName,), name=threadName)
                self.thread[threadName].start()
        else:
            threadName = 'MY_THREAD'
            self.thread[threadName] = Thread(target=self._go, args=(threadName,), name=threadName)
            self.thread[threadName].start()
        
    def subscribe(self, threadName, msg):
        self.ws[threadName].send(json.dumps(msg))

    def _go(self, threadName):
        self._connect(threadName)
        self._listen(threadName)
        self._disconnect(threadName)

    def _connect(self, threadName):
        if self.oneThreadPerProduct:
            self.ws[threadName] = create_connection(self.url+threadName)   # Note threadName = product
            self.on_subscribe(threadName)
        else:
            self.ws[threadName] = create_connection(self.url)
            self.on_subscribe(threadName)              # This calls subscribe(). Each exchange has unique msg syntax
            #self.ws.send(json.dumps({"type": "heartbeat", "on": True}))  # heartbeat
            
    def _disconnect(self, threadName):
        #if self.type == "heartbeat": self.ws.send(json.dumps({"type": "heartbeat", "on": False}))
        try:
            if self.ws[threadName]:
                self.ws[threadName].close()
        except WebSocketConnectionClosedException as e:
            pass
        except Exception as e:
            print('\n {} ERROR WebsocketClient:_disconnect() {}: {}'.format(dt.datetime.now(), threadName, e))
          
    def _listen(self, threadName):
        while not self.stop:
            try:
                if int(time.time() % 30) == 0: self.ws[threadName].ping("keepalive")  # Set a 30 second ping to keep connection alive
                msg = json.loads(self.ws[threadName].recv())
                if (type(msg) == dict): msg['threadName'] = threadName    # add to make easy to determine source when many threads
                self.on_message(msg)
            except Exception as e:
                self.stop = True
                errMsg = '\n WebsocketClient:_listen() {}: {}-{}'.format(threadName, type(e), e)
                self.on_error(errMsg)
 
    def close(self):
        #self.ws.send(json.dumps({"type": "heartbeat", "on": False}))
        self.on_close()
        self.stop = True
        
        for key in self.thread:
            print(' Close Thread: {}'.format(key))
            self.thread[key].join()

    def on_open(self):
        pass
    
    def on_subscribe(self, threadName):
        pass

    def on_close(self):
        pass

    def on_message(self, msg):
        print(msg)

    def on_error(self, errMsg):
        print('\n {} ERROR {}: {}'.format(dt.datetime.now(), errMsg))
        
def main():
    class MyWebsocketClient(WebsocketClient):
        
        def __init__(self):
            WebsocketClient.__init__(self, 'wss://ws-feed.gdax.com', ['BTC-USD', 'ETH-USD'], oneThreadPerProduct=False)
            self.message_count = 0
            print("\n Let's count the messages!")
        
        def on_open(self):
            pass
            #self._fh = open("rawTick.log", "w")
            
        def on_subscribe(self, threadName):
            msg = {'type': 'subscribe', 'product_ids': self.products}
            self.subscribe(threadName, msg)
            
        def on_message(self, msg):
            #self._fh.write('{} : {}\n'.format(dt.datetime.now(), msg))
            #print('{} : {}'.format(dt.datetime.now(), msg))
            self.message_count += 1

        def on_close(self):
            #self._fh.close()
            print('-- Goodbye! - MessageCount = {}'.format(self.message_count))


    for cnt in range(3):                #handle disconencts this way. Cleans up resources (Websocket) better
        wsClient = MyWebsocketClient()
        wsClient.start()
        print('Loop: {} (url: {} products: {})'.format(cnt, wsClient.url, wsClient.products))
        # Do some logic with the data
        while wsClient.message_count < 100 and wsClient.stop == False:
            print('MessageCount = {} \n'.format(wsClient.message_count))
            time.sleep(1)
    
        wsClient.close()
        if wsClient.message_count >= 100: break
    
    
if __name__ == "__main__":
    main()
    