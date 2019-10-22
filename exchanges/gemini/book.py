import sys
if "../../Common" not in sys.path: sys.path.append("../../Common") # Desperation

import datetime as dt
from decimal import Decimal
from book_base import BookBase

class Book(BookBase):
    '''
    Store orders as a dictionary of prices. Each price has one size (no orderID's)
    Auction is not yet implemented. 
    '''
    def __init__(self, product):
        BookBase.__init__(self, product)
        
    def doUpdateBook(self, msgBody):
        
        for data in msgBody:
            if (data['type'] == 'change'):          # trade or auction
                side = data['side']                 # bid or ask
                price = Decimal(data['price'])
                size = Decimal(data['remaining'])
                
                queue = self._bids if side == 'bid' else self._asks
                
                if (size == Decimal(0)):
                    if price in queue:
                        del queue[price]
                    else:
                        print('ERROR: Expect price {} in dictionary to delete'.format(price))
                else:
                    queue[price] = {-1 : size}  # no orderID (ITCH). CME like
                
            elif (data['type'] == 'trade'):
                side = 'A' if data['makerSide'] == 'Ask' else 'B'          # bid or ask
                price = Decimal(data['price'])
                size = Decimal(data['amount'])                
                self.setTradePriceSize(price, size, side)
                
            elif (data['type'].find('auction') != -1):
                #print('Auction: {}'.format(data))
                if (data['type'] == 'auction_open'):
                    print('auction open: {}'.format(data))
                elif (data['type'] == 'auction_indicative'):
                    print('auction indicative: {}'.format(data))
                    aBP = Decimal(data['highest_bid_price'])
                    aAP = Decimal(data['lowest_ask_price'])
                    aIP = Decimal(data['indicative_price'])
                    aIQ = Decimal(data['indicative_quantity'])
                    aRst = 1 if data['result'] == 'success' else 0
                    aTyp = 'I' if data['type'] == 'auction_indicative' else 'U'
                    self.setAuction(aBP, aAP, aIP, aIQ, aRst, aTyp)
                elif (data['type'] == 'auction_result'):
                    print('auction result: {}'.format(data))
                    aBP = Decimal(data['highest_bid_price'])
                    aAP = Decimal(data['lowest_ask_price'])
                    aIP = Decimal(data['auction_price'])
                    aIQ = Decimal(data['auction_quantity'])
                    aRst = 1 if data['result'] == 'success' else 0
                    aTyp = 'R' if data['type'] == 'auction_result' else 'U'
                    self.setAuction(aBP, aAP, aIP, aIQ, aRst, aTyp)
                    
        self.findBestBidAsk('buy')
        self.findBestBidAsk('sell')
        self.isGood()
    
def main():
    book = Book('btcusd')
    
    dataBidAsk = [{'price': '98',  'side': 'bid', 'remaining': '30', 'type': 'change'},
                  {'price': '100', 'side': 'bid', 'remaining': '20', 'type': 'change'},
                  {'price': '99',  'side': 'bid', 'remaining': '10', 'type': 'change'},
                  {'price': '102', 'side': 'ask', 'remaining': '20', 'type': 'change'},
                  {'price': '101', 'side': 'ask', 'remaining': '10', 'type': 'change'},
                  {'price': '103', 'side': 'ask', 'remaining': '30', 'type': 'change'}]
    
    
    book.doUpdateBook(dataBidAsk)
    
    print(('Best Bid/Ask Expect (100,101). {} {}'.format(book._bestBidPrice, book._bestAskPrice)))
    book.printBestBidAsk('Expect (20@100 10@101)') 
        
    bid1 = 100.5
    bid2 = 100
    ask1 = 100.6
    ask2 = 101
    
    sz0 = 0
    sz1 = 1
    sz2 = 2
    
    #bids
    book.doUpdateBook([{'price': bid1,  'side': 'bid', 'remaining': sz1, 'type': 'change'}])    #add better bid
    book.doUpdateBook([{'price': bid2,  'side': 'bid', 'remaining': sz2, 'type': 'change'}])
    book.printBestBidAsk('Expect (1@100.5 10@101)') 
    book.doUpdateBook([{'price': bid1,  'side': 'bid', 'remaining': sz0, 'type': 'change'}])    #remove best bid
    book.printBestBidAsk('Expect (2@100 10@101)') 
    
    #asks
    book.doUpdateBook([{'price': ask1,  'side': 'ask', 'remaining': sz1, 'type': 'change'}])    #add better ask
    book.doUpdateBook([{'price': ask2,  'side': 'ask', 'remaining': sz2, 'type': 'change'}])
    book.printBestBidAsk('Expect (2@100 1@100.6)') 
    book.doUpdateBook([{'price': ask1,  'side': 'ask', 'remaining': sz0, 'type': 'change'}])    #remove best ask
    book.printBestBidAsk('Expect (2@100 2@101)  ') 
    
    #remore all bids
    book.doUpdateBook([{'price': bid2,  'side': 'bid', 'remaining': sz0, 'type': 'change'}]) 
    book.doUpdateBook([{'price': Decimal(98),  'side': 'bid', 'remaining': sz0, 'type': 'change'}]) 
    book.doUpdateBook([{'price': Decimal(99),  'side': 'bid', 'remaining': sz0, 'type': 'change'}]) 
    book.printBestBidAsk('Expect (One side is empty)') 

if __name__ == '__main__':
    main()
    
#{'timestampms': 1505743400167, 'timestamp': 1505743400, 'socket_sequence': 16, 'events': [{'price': '4070.58', 'reason': 'cancel', 'side': 'bid', 'delta': '-5', 'remaining': '0', 'type': 'change'}], 'type': 'update', 'eventId': 1729527560}
#{'timestampms': 1505743399720, 'timestamp': 1505743399, 'socket_sequence': 3, 'events': [{'price': '4076.95', 'reason': 'cancel', 'side': 'bid', 'delta': '-11.72604643', 'remaining': '0', 'type': 'change'}], 'type': 'update', 'eventId': 1729527460}
#{'timestampms': 1505743410556, 'timestamp': 1505743410, 'socket_sequence': 170, 'events': [{'tid': 1729528909, 'amount': '0.0264865', 'makerSide': 'bid', 'price': '4086.56', 'type': 'trade'}, {'price': '4086.56', 'reason': 'trade', 'side': 'bid', 'delta': '-0.0264865', 'remaining': '6.46109148', 'type': 'change'}], 'type': 'update', 'eventId': 1729528909}
