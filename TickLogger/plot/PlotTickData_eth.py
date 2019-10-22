import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from timeit import default_timer as timer
import matplotlib.dates as mdates

#filenameGDAX = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gdax_20171009_091259.log'
#filenameKRAKEN = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_kraken_20171009_091318.log'
#filenameBITFINEX = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_bitfinex_20171009_091304.log'
#filenamePOLONIEX = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_poloniex_20171009_091314.log'
#filenameGEMINI = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20171009_091309.log'
#
#timeStart = '20171009 092000'
#timeEnd = '20171009 131500'

#filenameGDAX = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gdax_20171011_082847.log'
#filenameKRAKEN = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_kraken_20171010_182504.log'
#filenameBITFINEX = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_bitfinex_20171010_182450.log'
#filenamePOLONIEX = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_poloniex_20171010_184517.log'
#filenameGEMINI = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20171010_182454.log'
#
#timeStart = '20171011 084000'
#timeEnd = '20171011 161500'

filenameGDAX = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gdax_20171011_183134.log'
filenameKRAKEN = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_kraken_20171011_183152.log'
filenameBITFINEX = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_bitfinex_20171011_183138.log'
filenamePOLONIEX = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_poloniex_20171011_183147.log'
filenameGEMINI = r'\\awcnas4\QAR\Research\Data\Sanjeev\crypto\Tick_gemini_20171011_183142.log'

timeStart = '20171011 190000'
timeEnd = '20171012 161500'

def openFile(filename, name, timeStart=None, timeEnd=None):    #timeStart = '20171009 091500', timeEnd = '20171009 211500'
    fh = open(filename,'r')
    colNames = list(fh.readline()[:-1].split(','))
    fh.close()
    
    t0 = timer()
    dateparse = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f')
    dfALL = pd.read_csv(filename, delimiter='|', header=None, names=colNames, dtype={'Date': str}, parse_dates=['Date'], date_parser=dateparse, skiprows=1)
    dfALL.shape
    t1 = timer()
    total_n = t1-t0
    print ('Read {}. Time: {:.2f} seconds. rows: {}'.format(filename, total_n, dfALL.shape[0]))
    
    return getExchange(name, dfALL, timeStart, timeEnd)

def getExchange(name, dfALL, timeStart, timeEnd):
    
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
    
    if timeStart is not None and timeEnd is not None:
        maskTime = ((df['Date'] > timeStart) & (df['Date'] < timeEnd))
        df = df[maskTime]
    
    df = df.reset_index()
    maskTrd = df['pT'] > 1.e-8
    
    return df, maskTrd, minY, maxY

df_gdax, maskTrd_gdax, minY_gdax, maxY_gdax = openFile(filenameGDAX, 'ETH-USD', timeStart, timeEnd)
df_kraken, maskTrd_kraken, minY_kraken, maxY_kraken = openFile(filenameKRAKEN, 'XETHZUSD', timeStart, timeEnd)
df_bitfinex, maskTrd_bitfinex, minY_bitfinex, maxY_bitfinex = openFile(filenameBITFINEX, 'ETHUSD', timeStart, timeEnd)
df_poloniex, maskTrd_poloniex, minY_poloniex, maxY_poloniex = openFile(filenamePOLONIEX, 'USDT_ETH', timeStart, timeEnd)
df_gemini, maskTrd_gemini, minY_gemini, maxY_gemini = openFile(filenameGEMINI, 'ethusd', timeStart, timeEnd)

print('\n gdax: {} kraken: {} bitfinex: {} poloniex: {} gemini: {}'.format(df_gdax.shape[0], df_kraken.shape[0], df_bitfinex.shape[0], df_poloniex.shape[0], df_gemini.shape[0]))

#%matplotlib inline
#%matplotlib qt
    

def plotExchange(figPos, df, maskTrd, minY, maxY, title, ax=None, last=False, plotAll = True):

    if ax == None:
        ax1 = plt.subplot(figPos)
    else:
        ax1 = plt.subplot(figPos, sharex=ax)
        
    plt.plot(df['Date'], df['pB'], label='pB', drawstyle='steps')
    plt.plot(df['Date'], df['pA'], label='pA', drawstyle='steps')
    plt.plot(df['Date'][maskTrd].values, df['pT'][maskTrd].values, 'ys', label='Trd')
    if plotAll:
        plt.plot(df['Date'], df['pc'], label='pc', drawstyle='steps')
        plt.plot(df['Date'], df['pc_5'], label='pc_5', drawstyle='steps')
        plt.plot(df['Date'], df['pc_10'], label='pc_10', drawstyle='steps')
        plt.plot(df['Date'], df['pc_50'], label='pc_50', drawstyle='steps')
    
    plt.ylim((minY, maxY))
    plt.title('%s: %s' % (title, df.iloc[0]['Date'].strftime('%Y-%m-%d')), fontsize=18)    
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

plt.figure(1)
plotExchange(111, df_gdax, maskTrd_gdax, minY_gdax, maxY_gdax, 'gdax', None, True)
plt.show()

plt.figure(2)
plotExchange(111, df_kraken, maskTrd_kraken, minY_kraken, maxY_kraken, 'kraken', None, True)
plt.show()

plt.figure(3)
plotExchange(111, df_bitfinex, maskTrd_bitfinex, minY_bitfinex, maxY_bitfinex, 'bitfinex', None, True)
plt.show()

plt.figure(4)
plotExchange(111, df_poloniex, maskTrd_poloniex, minY_poloniex, maxY_poloniex, 'poloniex', None, True)
plt.show()

plt.figure(5)
plotExchange(111, df_gemini, maskTrd_gemini, minY_gemini, maxY_gemini, 'gemini', None, True)
plt.show()

plt.figure(6)
ax1 = plotExchange(511, df_gdax, maskTrd_gdax, minY_gdax, maxY_gdax, 'gdax ETH', None, False, False)
plotExchange(512, df_kraken, maskTrd_kraken, minY_kraken, maxY_kraken, 'kraken', ax1, False)
plotExchange(513, df_bitfinex, maskTrd_bitfinex, minY_bitfinex, maxY_bitfinex, 'bitfinex', ax1, False)
plotExchange(514, df_poloniex, maskTrd_poloniex, minY_poloniex, maxY_poloniex, 'poloniex', ax1, False)
plotExchange(515, df_gemini, maskTrd_gemini, minY_gemini, maxY_gemini, 'gemini', ax1, True)
plt.show()

# try to see difference between exchanges
df_gdax_unique = df_gdax.groupby(['Date']).first()
df_gdax_unique = df_gdax_unique.loc[:,('pc', 'pB', 'pA')]
df_gdax_1sec = df_gdax_unique.resample(rule='1S').ffill()
df_gdax_1sec = df_gdax_1sec.reset_index()

df_kraken_unique = df_kraken.groupby(['Date']).first()
df_kraken_unique = df_kraken_unique.loc[:,('pc', 'pB', 'pA')]
df_kraken_1sec = df_kraken_unique.resample(rule='1S').ffill()
df_kraken_1sec = df_kraken_1sec.reset_index()

df_bitfinex_unique = df_bitfinex.groupby(['Date']).first()
df_bitfinex_unique = df_bitfinex_unique.loc[:,('pc', 'pB', 'pA')]
df_bitfinex_1sec = df_bitfinex_unique.resample(rule='1S').ffill()
df_bitfinex_1sec = df_bitfinex_1sec.reset_index()

df_poloniex_unique = df_poloniex.groupby(['Date']).first()
df_poloniex_unique = df_poloniex_unique.loc[:,('pc', 'pB', 'pA')]
df_poloniex_1sec = df_poloniex_unique.resample(rule='1S').ffill()
df_poloniex_1sec = df_poloniex_1sec.reset_index()

df_gemini_unique = df_gemini.groupby(['Date']).first()
df_gemini_unique = df_gemini_unique.loc[:,('pc', 'pB', 'pA')]
df_gemini_1sec = df_gemini_unique.resample(rule='1S').ffill()
df_gemini_1sec = df_gemini_1sec.reset_index()

plt.figure(7)
ax1 = plt.subplot(111)
npts = min(df_gdax_1sec.shape[0], df_kraken_1sec.shape[0], df_bitfinex_1sec.shape[0], df_poloniex_1sec.shape[0], df_gemini_1sec.shape[0] ) - 1
plt.plot(df_gdax_1sec['Date'][:npts], df_gdax_1sec['pc'][:npts]-df_kraken_1sec['pc'][:npts], label='gdax-kraken', drawstyle='steps')
#plt.plot(df_gdax_1sec['Date'][:npts], df_gdax_1sec['pc'][:npts]-df_bitfinex_1sec['pc'][:npts], label='gdax-bitfinex', drawstyle='steps')
plt.plot(df_gdax_1sec['Date'][:npts], df_gdax_1sec['pc'][:npts]-df_poloniex_1sec['pc'][:npts], label='gdax-poloniex', drawstyle='steps')
plt.plot(df_gdax_1sec['Date'][:npts], df_gdax_1sec['pc'][:npts]-df_gemini_1sec['pc'][:npts], label='gdax-gemini', drawstyle='steps')
plt.title('Differences in pc ETH', fontsize=18)
plt.xlabel('Time', fontsize=18)
plt.ylabel('delta pc (dollars)', fontsize=18)
plt.legend(loc='best')
plt.grid()
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.gcf().set_size_inches(6,5)