#
# Based on https://github.com/danpaquin/gdax-python and https://github.com/Seratna/GDAX-python
#

import sys
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
        self.stop = True
        self.error = None
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
            
    def _disconnect(self, threadName):
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
                data = self.ws[threadName].recv()
                msg = json.loads(data)
                if (type(msg) == dict): msg['threadName'] = threadName    # add to make easy to determine source when many threads
            except ValueError as e:
                self.stop = True
                errMsg = '\n WebsocketClient:_listen() {}: {}-{}'.format(threadName, type(e), e)
                self.on_error(errMsg)
            except Exception as e:
                self.stop = True
                errMsg = '\n WebsocketClient:_listen() {}: {}-{}'.format(threadName, type(e), e)
                self.on_error(errMsg)
            else:
                self.on_message(msg)
 
    def close(self):
        self.on_close()
        self.stop = True      # will only disconnect after next msg recv
        
        for key in self.thread:
            print(' Close Thread: {}'.format(key))
            self._disconnect(key) # force disconnect so threads can join
            print(' _disconnect(): {}'.format(key))
            self.thread[key].join()
            print(' join(): {}'.format(key))
            

    def on_open(self):
        pass
    
    def on_subscribe(self, threadName):
        pass

    def on_close(self):
        pass

    def on_message(self, msg):
        print(msg)

    def on_error(self, errMsg):
        self.error = errMsg
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
            msg = {'type': 'subscribe', 'product_ids': self.products, 'channels':['full']}
            self.subscribe(threadName, msg)
            
        def on_message(self, msg):
            #self._fh.write('{} : {}\n'.format(dt.datetime.now(), msg))
            #print('{} : {}'.format(dt.datetime.now(), msg))
            self.message_count += 1

        def on_close(self):
            #self._fh.close()
            print('-- Goodbye! - MessageCount = {}'.format(self.message_count))


    wsClient = MyWebsocketClient()
    wsClient.start()
    print('(url: {} products: {})'.format(wsClient.url, wsClient.products))
    
    numLoop = 100
    try:
        # Do some logic with the data
        while wsClient.message_count < numLoop and wsClient.stop == False:
            print('\nMessageCount = {} \n'.format(wsClient.message_count))
            if wsClient.message_count >= numLoop: break
            time.sleep(1)
        print('We exit loop and close')
        wsClient.close()
    except KeyboardInterrupt:
        wsClient.close()
        
    print('\nEXIT LOOP\n')

    if wsClient.error:
        print('Call sys.exit(1): {}'.format(wsClient.error))
        sys.exit(1)
    else:
        print('Call sys.exit(0)')
        sys.exit(0)
    
    
if __name__ == "__main__":
    main()
    