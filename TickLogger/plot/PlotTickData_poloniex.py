import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from timeit import default_timer as timer

#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_poloniex_20171010_063247.log'
filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_poloniex_20171009_211641.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_poloniex_20171009_091314.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_poloniex_20171008_115419.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_poloniex_20171007_184938.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_poloniex_20171007_045058.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_poloniex_20170914_224233.log'
#filename = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_poloniex_20170918_205101.log'


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

def getExchange(name, dfALL):
    
    pd.options.mode.chained_assignment = None  # default='warn'
    
    df = dfALL[dfALL['Name'] == name]   
    
    df['spread'] = df['pA'] - df['pB']
    mask = df['spread'] > 0
    minIncr = df.loc[mask,'spread'].min()
    minY = df['pB'].min() - 3*minIncr;
    maxY = df['pA'].max() + 3*minIncr;
    
    df['pc'] = (df['pB']*df['qA'] + df['pA']*df['qB']) / (df['qB'] + df['qA'])
    maskWide = df['spread'] > minIncr + 1.e-8
    df.loc[maskWide,'pc'] = (df['pA'][maskWide] + df['pB'][maskWide]) / 2.
    
    df['pc_5'] = (df['pB_5']*df['qA_5'] + df['pA_5']*df['qB_5']) / (df['qB_5'] + df['qA_5'])
    df['pc_10'] = (df['pB_10']*df['qA_10'] + df['pA_10']*df['qB_10']) / (df['qB_10'] + df['qA_10'])
    df['pc_50'] = (df['pB_50']*df['qA_50'] + df['pA_50']*df['qB_50']) / (df['qB_50'] + df['qA_50'])
    
    maskTrd = df['pT'] > 1.e-8
    
    return df, maskTrd, minY, maxY

dfBTC_USD, maskTrdBTC_USD, minYBTC_USD, maxYBTC_USD = getExchange('USDT_BTC', dfALL)
dfETH_USD, maskTrdETH_USD, minYETH_USD, maxYETH_USD = getExchange('USDT_ETH', dfALL)
dfLTC_USD, maskTrdLTC_USD, minYLTC_USD, maxYLTC_USD = getExchange('USDT_LTC', dfALL)
dfLTC_BTC, maskTrdLTC_BTC, minYLTC_BTC, maxYLTC_BTC = getExchange('BTC_LTC', dfALL)
dfETH_BTC, maskTrdETH_BTC, minYETH_BTC, maxYETH_BTC = getExchange('BTC_ETH', dfALL)

dfBCH_USD, maskTrdBCH_USD, minYBCH_USD, maxYBCH_USD = getExchange('USDT_BCH', dfALL)
dfXRP_USD, maskTrdXRP_USD, minYXRP_USD, maxYXRP_USD = getExchange('USDT_XRP', dfALL)
dfBTC_XRP, maskTrdBTC_XRP, minYBTC_XRP, maxYBTC_XRP = getExchange('BTC_XRP', dfALL)


#%matplotlib inline
#%matplotlib qt

def plotDly(figPos, dfALL, bins_dT, lowX, highX):
    ax1 = plt.subplot(figPos)
    plt.subplot(figPos)
    n1, bins1, patches1 = plt.hist(dfALL.loc[lowX:highX, ('Dly')]*1e3, bins_dT, facecolor='g', alpha=0.75)
    plt.text(0.55, 0.85, 'Time: %s to %s' % (dfALL.iloc[lowX]['Date'].strftime('%H:%M:%S'), dfALL.iloc[highX]['Date'].strftime('%H:%M:%S')), fontsize=8, bbox=dict(facecolor='yellow', alpha=0.5), transform=ax1.transAxes)
    plt.ylabel('Number', fontsize=12)
    plt.tick_params(axis='both', which='major', labelsize=14)
    plt.xlim((0, 200));
    plt.xlabel('dT (milli-sec)', fontsize=12)
    plt.title('%s: %s' % ('dT Machine to Exchange', dfALL.iloc[lowX]['Date'].strftime('%Y-%m-%d')), fontsize=12)
    plt.grid()
    

def plotExchange(figPos, df, maskTrd, minY, maxY, ax=None, last=False):

    if ax == None:
        ax1 = plt.subplot(figPos)
    else:
        ax1 = plt.subplot(figPos, sharex=ax)
        
    plt.plot(df['Date'], df['pB'], label='pB', drawstyle='steps')
    plt.plot(df['Date'], df['pA'], label='pA', drawstyle='steps')
    plt.plot(df['Date'], df['pc'], label='pc', drawstyle='steps')
    plt.plot(df['Date'], df['pc_5'], label='pc_5', drawstyle='steps')
    plt.plot(df['Date'], df['pc_10'], label='pc_10', drawstyle='steps')
    plt.plot(df['Date'], df['pc_50'], label='pc_50', drawstyle='steps')
    plt.plot(df['Date'][maskTrd].values, df['pT'][maskTrd].values, 'ys', label='Trd')
    plt.ylim((minY, maxY))
    plt.title('%s: %s' % (df.iloc[0]['Name'], df.iloc[0]['Date'].strftime('%Y-%m-%d')), fontsize=18)    
    plt.ylabel('Prices', fontsize=18)
    plt.tick_params(axis='y', which='major', labelsize=14)
    plt.legend(loc='upper left')
    
    if last == True:
        plt.xlabel('Time', fontsize=18)
        plt.tick_params(axis='x', which='major', labelsize=14)
    else:
        plt.tick_params(axis='x', which='major', labelsize=2)
    
    plt.gcf().set_size_inches(15,8)
    ax = plt.gca()
    #ax.get_yaxis().get_major_formatter().set_scientific(False)
    ax.get_yaxis().get_major_formatter().set_useOffset(False)
    plt.grid()
    return ax1
    

npts = dfALL.shape[0]
bins_dT = np.arange(0, 400, 1)
plt.figure(1)
plotDly(221, dfALL, bins_dT, 0, int(npts*0.01))
plotDly(222, dfALL, bins_dT, int(npts*0.99), npts-1)
ax1 = plt.subplot(212)
plt.plot(dfALL['Date'], dfALL['Dly'], label='Dly', drawstyle='steps')
plt.xlabel('Time', fontsize=18)
plt.ylabel('Dly', fontsize=18)
plt.tick_params(axis='both', which='major', labelsize=14)
plt.legend(loc='upper left')
plt.gcf().set_size_inches(15,8)
plt.grid()
plt.show()

plt.figure(2)
plotExchange(111, dfBTC_USD, maskTrdBTC_USD, minYBTC_USD, maxYBTC_USD)
plt.show()

plt.figure(3)
plotExchange(111, dfETH_USD, maskTrdETH_USD, minYETH_USD, maxYETH_USD)
plt.show()

plt.figure(4)
plotExchange(111, dfLTC_USD, maskTrdLTC_USD, minYLTC_USD, maxYLTC_USD)
plt.show()

plt.figure(5)
plotExchange(111, dfLTC_BTC, maskTrdLTC_BTC, minYLTC_BTC, maxYLTC_BTC)
plt.show()

plt.figure(6)
plotExchange(111, dfETH_BTC, maskTrdETH_BTC, minYETH_BTC, maxYETH_BTC)
plt.show()

plt.figure(7)
plotExchange(111, dfBCH_USD, maskTrdBCH_USD, minYBCH_USD, maxYBCH_USD)
plt.show()


plt.figure(8)
plotExchange(111, dfXRP_USD, maskTrdXRP_USD, minYXRP_USD, maxYXRP_USD)
plt.show()


plt.figure(9)
plotExchange(111, dfBTC_XRP, maskTrdBTC_XRP, minYBTC_XRP, maxYBTC_XRP)
plt.show()


plt.figure(10)
ax1 = plotExchange(311, dfBTC_USD, maskTrdBTC_USD, minYBTC_USD, maxYBTC_USD)
plotExchange(312, dfETH_USD, maskTrdETH_USD, minYETH_USD, maxYETH_USD, ax1, False)
plotExchange(313, dfLTC_USD, maskTrdLTC_USD, minYLTC_USD, maxYLTC_USD, ax1, True)
plt.show()

 