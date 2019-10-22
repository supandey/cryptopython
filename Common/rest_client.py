# based on https://github.com/veox/python3-krakenex/blob/master/krakenex/api.py

import requests
import time  # private query nonce
import datetime as dt

# private query signing
import urllib.parse
import hashlib
import hmac
import base64

from threading import Thread

class RestClient:
    
    def __init__(self, url, products, intervalSec=1, key='', secret=''):
        self.url = url
        self.products = products
        self.intervalSec = intervalSec
        self.key = key
        self.secret = secret
        self.apiversion = '0'
        self.session = { product : requests.Session() for product in self.products}
        self.response = None
        self.stop = False
        self.thread = {}
        
    def load_key(self, path):
        """ Load key and secret from file.
        Expected file format is key and secret on separate lines.
        :param path: path to keyfile
        :type path: str
        :returns: None
        """
        with open(path, 'r') as f:
            self.key = f.readline().strip()
            self.secret = f.readline().strip()
        return
    
    def start(self):
        self.stop = False
        
        for threadName in self.products:
            method, data = self.on_open(threadName)
            print('Create thread for {} method={} data={}'.format(threadName, method, data))
            self.thread[threadName] = Thread(target=self._go, args=(threadName, method, data), name=threadName)
            self.thread[threadName].start()
        
    def close(self):
        if not self.stop:
            self.on_close()
            self.stop = True
            time.sleep(0.1)      #give _listen time to exit while loop
            
            for key in self.thread:
                print(' Close Thread: {}'.format(key))
                try:
                    self.thread[key].join()
                    if self.session[key]:
                        self.session[key].close()
                except Exception as e:
                    print('\n {} ERROR WebsocketClient:_listen() {}: {}'.format(dt.datetime.now(), key, e))
            
            print('Exit RestClient Close()')
            
    def _go(self, threadName, method, data):
        while not self.stop:
            try:
                #msg = self.query_public(threadName, 'Depth', {'pair': threadName})
                msg = self.query_public(threadName, method, data)
                if (type(msg) == dict): msg['threadName'] = threadName    # add to make easy to determine source when many threads
                self.on_message(msg)
            except Exception as e:
                print('\n {} ERROR RestClient:_go {} - {}'.format(dt.datetime.now(), threadName, e))
            time.sleep(self.intervalSec)
            
    def _nonce(self):
        ''' Nonce counter. an always-increasing unsigned integer (up to 64 bits wide) '''
        return int(1000*time.time())
    
    def _sign(self, data, urlpath):
        ''' Sign request data according to Kraken's scheme.
        :param data: API request parameters
        :type data: dict
        :param urlpath: API URL path sans host
        :type urlpath: str
        :returns: signature digest
        '''
        postdata = urllib.parse.urlencode(data)

        # Unicode-objects must be encoded before hashing
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        signature = hmac.new(base64.b64decode(self.secret),
                             message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())

        return sigdigest.decode()
            
    def _query(self, threadName, urlpath, data, headers=None):
        ''' Low-level query handling.
        .. note::
           Use :py:meth:`query_private` or :py:meth:`query_public`
           unless you have a good reason not to.
        :param urlpath: API URL path sans host
        :type urlpath: str
        :param data: API request parameters
        :type data: dict
        :param headers: (optional) HTTPS headers
        :type headers: dict
        :returns: :py:meth:`requests.Response.json`-deserialised Python object
        :raises: :py:exc:`requests.HTTPError`: if response status not successful
        '''
        if data is None:
            data = {}
        if headers is None:
            headers = {}

        url = self.url + urlpath

        self.response = self.session[threadName].post(url, data = data, headers = headers)

        if self.response.status_code not in (200, 201, 202):
            self.response.raise_for_status()

        return self.response.json()


    def query_public(self, threadName, method, data=None):
        ''' Performs an API query that does not require a valid key/secret pair.
        :param method: API method name
        :type method: str
        :param data: (optional) API request parameters
        :type data: dict
        :returns: :py:meth:`requests.Response.json`-deserialised Python object
        '''
        if data is None:
            data = {}

        urlpath = '/' + self.apiversion + '/public/' + method

        return self._query(threadName, urlpath, data)

    def query_private(self, threadName, method, data=None):
        ''' Performs an API query that requires a valid key/secret pair.
        :param method: API method name
        :type method: str
        :param data: (optional) API request parameters
        :type data: dict
        :returns: :py:meth:`requests.Response.json`-deserialised Python object
        '''
        if data is None:
            data = {}

        if not self.key or not self.secret:
            raise Exception('Either key or secret is not set! (Use `load_key()`.')

        data['nonce'] = self._nonce()

        urlpath = '/' + self.apiversion + '/private/' + method

        headers = {
            'API-Key': self.key,
            'API-Sign': self._sign(data, urlpath)
        }

        return self._query(threadName, urlpath, data, headers)
        
    def on_open(self, threadName):
        return ('Depth', {'pair': threadName})
    
    def on_close(self):
        pass
    
    def on_message(self, msg):
        print(msg)

    def on_error(self, e):
        print(e)
        
        
def main():
    class MyRestClient(RestClient):
        def __init__(self):
            #products = ['XXRPZUSD', 'XXRPXXBT']  #XBTCXLTC
            products = ['XETHZUSD', 'XXBTZUSD']
            RestClient.__init__(self, 'https://api.kraken.com', products, 1)
            self.message_count = 0
            print("\n Let's count the messages!")
        
        def on_open(self, threadName):
            return ('Depth', {'pair': threadName})

        def on_message(self, msg):
            print('{} : {}'.format(dt.datetime.now(), msg))
            self.message_count += 1

        def on_close(self):
            print("-- Goodbye! --")

    rsClient = MyRestClient()
    rsClient.start()
    print(rsClient.url, rsClient.products)
    # Do some logic with the data
    while rsClient.message_count < 3:
        print("\nMessageCount =", "%i \n" % rsClient.message_count)
        time.sleep(1)

    rsClient.close()
    
if __name__ == "__main__":
    main()
    