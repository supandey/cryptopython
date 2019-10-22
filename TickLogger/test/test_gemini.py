import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from timeit import default_timer as timer
import utils_crypto as utils

filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20171207_131332.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20171011_183142.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20171009_211635.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20171009_091309.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20171008_115414.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20171007_184840.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20171007_045047.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20170922_080638.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20170921_085907.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20170920_063554.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20170919_142655.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20170918_205107.log'

fh = open(filename,'r')
colNames = list(fh.readline()[:-1].split(','))
fh.close()

t0 = timer()
dateparse = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f')
dfALL = pd.read_csv(filename, delimiter='|', header=None, names=colNames, dtype={'Date': str}, parse_dates=['Date'], date_parser=dateparse, skiprows=1)
dfALL.shape
t1 = timer()
total_n = t1-t0
print (' Read Time: %.2f seconds. size: %d' % (total_n, dfALL.shape[0]))

dTime = (np.diff(dfALL['Date'].values)/1e3).astype(float)  # as micro-sec. Time between events

dfBTC_USD, maskTrdBTC_USD, minYBTC_USD, maxYBTC_USD, minIncr_BTC_USD = utils.getExchange('btcusd', dfALL)
dfETH_USD, maskTrdETH_USD, minYETH_USD, maxYETH_USD, minIncr_ETH_USD = utils.getExchange('ethusd', dfALL)
dfETH_BTC, maskTrdETH_BTC, minYETH_BTC, maxYETH_BTC, minIncr_ETH_BTC = utils.getExchange('ethbtc', dfALL)

plt.figure(2)
utils.plotExchange(111, dfBTC_USD, maskTrdBTC_USD, minYBTC_USD, maxYBTC_USD, 'Gemini BTC', None, True)
plt.show()

plt.figure(3)
utils.plotExchange(111, dfETH_USD, maskTrdETH_USD, minYETH_USD, maxYETH_USD, 'Gemini ETH', None, True)
plt.show()

plt.figure(4)
utils.plotExchange(111, dfETH_BTC, maskTrdETH_BTC, minYETH_BTC, maxYETH_BTC, 'Gemini BTC-ETH', None, True)
plt.show()

fig = plt.figure(5)
ax1 = utils.plotExchange(311, dfBTC_USD, maskTrdBTC_USD, minYBTC_USD, maxYBTC_USD, 'BTC Gemini', None, False, False)
utils.plotExchange(312, dfETH_USD, maskTrdETH_USD, minYETH_USD, maxYETH_USD, 'ETH', ax1, False, False)
utils.plotExchange(313, dfETH_BTC, maskTrdETH_BTC, minYETH_BTC, maxYETH_BTC, 'BTC-ETH', ax1, True, False)
#fig.autofmt_xdate()
plt.show()

def findLocation(df, minIncr, scale):
    mask_Ask = ((df['pc_5_ma'] < df['pB'] - scale*minIncr) &       # pc below bid. hope price goes down. pc above ma means recent move up against expectations.
               (df['pc_10_ma'] < df['pB'] - scale*2*minIncr) & 
               (df['pc_50_ma'] < df['pB'] - scale*10*minIncr) &
               (df['pc'] > df['pc_ma'] + 10*minIncr))
    
    mask_Bid = ((df['pc_5_ma'] > df['pA'] + scale*minIncr) & 
                (df['pc_10_ma'] > df['pA'] + scale*2*minIncr) & 
                (df['pc_50_ma'] > df['pA'] + scale*10*minIncr) &
                (df['pc'] < df['pc_ma'] - 10*minIncr))
    
    return mask_Bid, mask_Ask

def findLocationA(df, minIncr, scale):
    # the long term ma's are moving down for a sell even htough pc is mving up.
    mask_Ask = ((df['pc_5_ma'] < df['pB'] - scale*minIncr) &       # pc below bid. hope price goes down. pc above ma means recent move up against expectations.
               (df['pc_10_ma'] < df['pB'] - scale*2*minIncr) & 
               (df['pc_50_ma'] < df['pB'] - scale*10*minIncr) &
               
               (df['pc_50_ma'] < df['pc_50_ma_ma'] - scale*2*minIncr) &
               (df['pc'] > df['pc_ma'] + 10*minIncr))
    
    mask_Bid = ((df['pc_5_ma'] > df['pA'] + scale*minIncr) & 
                (df['pc_10_ma'] > df['pA'] + scale*2*minIncr) & 
                (df['pc_50_ma'] > df['pA'] + scale*10*minIncr) &
                
                (df['pc_50_ma'] > df['pc_50_ma_ma'] + scale*2*minIncr) &                 
                (df['pc'] < df['pc_ma'] - 10*minIncr))
    
    return mask_Bid, mask_Ask

def findLocationB(df, minIncr, scale):
    # only look at long term ma's
    
    df_100 = df.shift(100)
    df_500 = df.shift(500)
    
    mask_Ask = ((df['pc_50_ma'] < df['pB'] - scale*10*minIncr) &
                (df['pc_50_ma_ma'] < df['pB'] - scale*10*minIncr) &
                (df['spread'] < 3*minIncr) &
                #(df['pc_10_ma'] < df['pB'] - scale*2*minIncr) & 
               (df['pc_50_ma'] < df['pc_50_ma_ma'] - scale*5*minIncr) &
               (df_100['pc_50_ma'] < df_100['pc_50_ma_ma'] - scale*5*minIncr) &
               (df_500['pc_50_ma'] < df_500['pc_50_ma_ma'] - scale*5*minIncr))
    
    mask_Bid = ((df['pc_50_ma'] > df['pA'] + scale*10*minIncr) &
                (df['pc_50_ma_ma'] > df['pA'] + scale*10*minIncr) &
                (df['spread'] < 3*minIncr) &
                #(df['pc_10_ma'] > df['pA'] + scale*2*minIncr) & 
                (df['pc_50_ma'] > df['pc_50_ma_ma'] + scale*5*minIncr) &
                (df_100['pc_50_ma'] > df_100['pc_50_ma_ma'] + scale*5*minIncr) &
                (df_500['pc_50_ma'] > df_500['pc_50_ma_ma'] + scale*5*minIncr))
    
    return mask_Bid, mask_Ask

def findLocationC(df, minIncr, scale):
    # only look at long term ma's and MACD
    
    #too many trades
#    mask_Ask = ((df['pc_macd'] < -10*scale*minIncr) &
#                (df['pc_macd'] < df['pc_macd_signal'] - scale*minIncr) &
#                (df['spread'] < 3*minIncr))
#    
#    mask_Bid = ((df['pc_macd'] > 10*scale*minIncr) &
#                (df['pc_macd'] > df['pc_macd_signal'] + scale*minIncr) &
#                (df['spread'] < 3*minIncr))
    
    mask_Ask = ((df['pc_macd_signal'] < -10*scale*minIncr) &
                (df['pc_macd'] < df['pc_macd_signal'] - scale*minIncr) &
                (df['spread'] < 3*minIncr))
    
    mask_Bid = ((df['pc_macd_signal'] > 10*scale*minIncr) &
                (df['pc_macd'] > df['pc_macd_signal'] + scale*minIncr) &
                (df['spread'] < 3*minIncr))
   
    return mask_Bid, mask_Ask

def callStrategy(df, minIncr, scale, risk, profit, scratch, optimistic):
    #mask_Bid, mask_Ask = findLocationB(df, minIncr, scale)
    mask_Bid, mask_Ask = findLocationC(df, minIncr, scale)
    loc_BID = df.index[mask_Bid]
    loc_ASK = df.index[mask_Ask]
    
    pB = df['pB']
    pA = df['pA']
    times = df['Date']
    
    profitB, profitA, gain = utils.pnl_A(times, pB, pA, loc_BID, loc_ASK, risk, profit, scratch, minIncr, optimistic)
    return profitB, profitA, gain

optimistic= True

scale_BTC = 10
risk_BTC = 600
profit_BTC = 800
scratch_BTC = 200
profitB_BTC, profitA_BTC, gain_BTC = callStrategy(dfBTC_USD, minIncr_BTC_USD, scale_BTC, risk_BTC, profit_BTC, scratch_BTC, optimistic)

scale_ETH = 10
risk_ETH = 20
profit_ETH = 50
scratch_ETH = 2
profitB_ETH, profitA_ETH, gain_ETH = callStrategy(dfETH_USD, minIncr_ETH_USD, scale_ETH, risk_ETH, profit_ETH, scratch_ETH, optimistic)

plt.figure(6)
utils.plotExchangeAndMACD( dfBTC_USD, maskTrdBTC_USD, minYBTC_USD, maxYBTC_USD, 'Gemini BTC')
#plt.subplot(211)
plt.subplot(3,1,(1,2))
#utils.plotExchange(111, dfBTC_USD, maskTrdBTC_USD, minYBTC_USD, maxYBTC_USD, 'Gemini BTC', None, True)
plt.plot([x[5] for x in profitB_BTC], [x[2] for x in profitB_BTC], 'kv', markersize=20)  #enter bid
plt.plot([x[6] for x in profitB_BTC], [x[3] for x in profitB_BTC], 'yv', markersize=20)  #exit bid
plt.plot([x[5] for x in profitA_BTC], [x[3] for x in profitA_BTC], 'ko', markersize=20)  #enter ask
plt.plot([x[6] for x in profitA_BTC], [x[2] for x in profitA_BTC], 'yo', markersize=20)  #exit ask
plt.show()

plt.figure(7)
utils.plotExchange(111, dfETH_USD, maskTrdETH_USD, minYETH_USD, maxYETH_USD, 'Gemini ETH', None, True)
plt.plot([x[5] for x in profitB_ETH], [x[2] for x in profitB_ETH], 'kv', markersize=20)  #enter bid
plt.plot([x[6] for x in profitB_ETH], [x[3] for x in profitB_ETH], 'mv', markersize=20)  #exit bid
plt.plot([x[5] for x in profitA_ETH], [x[3] for x in profitA_ETH], 'ko', markersize=20)  #enter ask
plt.plot([x[6] for x in profitA_ETH], [x[2] for x in profitA_ETH], 'mo', markersize=20)  #exit ask
plt.show()

def printResults(title, profitB, profitA, gain):

    sOut = '\n\n {} \n\n Jump Down \n    date     time             pBuy   pSell    PnL (ticks) \n'.format(title);
    for data in profitB:
        pBuy  = data[2]
        pSell = data[3]
        profit = data[4]
        timeEnter = data[5]
        sOut = '{} {:%Y-%m-%d %H:%M:%S.%f} {:.3f} {:.3f} {:.0f} \n'.format(sOut, timeEnter, pBuy, pSell, profit)
    
    sOut1 = '\n Jump Up \n    date     time             pBuy   pSell    PnL (ticks) \n';
    for data in profitA:
        pBuy  = data[2]
        pSell = data[3]
        profit = data[4]
        timeEnter = data[5]
        sOut1 = '{} {:%Y-%m-%d %H:%M:%S.%f} {:.3f} {:.3f} {:.0f} \n'.format(sOut1, timeEnter, pBuy, pSell, profit)
    
    sFinal = '{} {} pnl(ticks) = {:.3f}   # = {}'.format(sOut,sOut1,gain, len(profitB)+len(profitA))
    print(sFinal)

printResults('BTC', profitB_BTC, profitA_BTC, gain_BTC)
printResults('ETH', profitB_ETH, profitA_ETH, gain_ETH)

    
    
    
    


