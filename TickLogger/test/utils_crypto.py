import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

hours = mdates.HourLocator()   # every year
minutes = mdates.MinuteLocator()   # every year
dateFmt = mdates.DateFormatter('%H:%M:%S.%f')

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
    df['pc_ma'] = df['pc'].ewm(span=100).mean()
    df['pc_5_ma'] = df['pc_5'].ewm(span=100).mean()
    df['pc_10_ma'] = df['pc_10'].ewm(span=100).mean()
    df['pc_50_ma'] = df['pc_50'].ewm(span=100).mean()
    
    df['pc_5_ma_ma'] = df['pc_5_ma'].ewm(span=100).mean()
    df['pc_10_ma_ma'] = df['pc_10_ma'].ewm(span=100).mean()
    df['pc_50_ma_ma'] = df['pc_50'].ewm(span=200).mean()
    df['pc_macd'] = df['pc_50_ma'] - df['pc_50_ma_ma'];
    df['pc_macd_signal'] = df['pc_macd'].ewm(span=50).mean()
    
    df = df.reset_index()
    del df['index']
    
    maskTrd = df['pT'] > 1.e-8
    
    return df, maskTrd, minY, maxY, minIncr

def plotExchange(figPos, df, maskTrd, minY, maxY, title, ax=None, last=False, plotAll = True):

    if ax == None:
        ax1 = plt.subplot(figPos)
    else:
        ax1 = plt.subplot(figPos, sharex=ax)
        
    plt.plot(df['Date'], df['pB'], label='pB', drawstyle='steps-post')
    plt.plot(df['Date'], df['pA'], label='pA', drawstyle='steps-post')
    plt.plot(df['Date'][maskTrd].values, df['pT'][maskTrd].values, 'ys', label='Trd')
    if plotAll:
        plt.plot(df['Date'], df['pc'], label='pc', drawstyle='steps-post', linewidth=0.5, linestyle='--')
        plt.plot(df['Date'], df['pc_5_ma'], label='pc_5_ma', drawstyle='steps-post', linewidth=0.4, linestyle='--')
        plt.plot(df['Date'], df['pc_10_ma'], label='pc_10_ma', drawstyle='steps-post', linewidth=0.4, linestyle='--')
        plt.plot(df['Date'], df['pc_50_ma'], label='pc_50_ma', drawstyle='steps-post', linewidth=0.6, linestyle='--')
        plt.plot(df['Date'], df['pc_50_ma_ma'], label='pc_50_ma_ma', drawstyle='steps-post', linewidth=0.6, linestyle='--')
        plt.plot(df['Date'], df['pc_ma'], label='pc_ma', drawstyle='steps-post', linewidth=0.6, linestyle='-')
    
    plt.ylim((minY, maxY))
    plt.title('%s: %s' % (title, df.iloc[0]['Date'].strftime('%Y-%m-%d')), fontsize=18)    
    plt.ylabel('Prices', fontsize=18)
    plt.tick_params(axis='y', which='major', labelsize=14)
    plt.legend(loc='upper left')
    
    if last == True:
        plt.xlabel('Time', fontsize=18)
        plt.tick_params(axis='x', which='major', labelsize=14)
        
        #ax1.xaxis.set_major_locator(hours)
        #ax1.xaxis.set_minor_locator(minutes)
        #ax1.format_xdata = mdates.DateFormatter('%H:%M:%S.%f')
        #ax1.xaxis.set_major_formatter(dateFmt)
    else:
        plt.tick_params(axis='x', which='major', labelsize=2)
    
    plt.gcf().set_size_inches(15,8)
    ax1 = plt.gca()
    #ax1.get_yaxis().get_major_formatter().set_scientific(False)
    ax1.get_yaxis().get_major_formatter().set_useOffset(False)
    
    
    plt.grid()
    return ax1

def plotExchangeAndMACD(df, maskTrd, minY, maxY, title):

    #ax = plt.subplot(211)
    ax = plt.subplot(3,1,(1,2))
    
    plt.plot(df['Date'], df['pB'], label='pB', drawstyle='steps-post')
    plt.plot(df['Date'], df['pA'], label='pA', drawstyle='steps-post')
    plt.plot(df['Date'][maskTrd].values, df['pT'][maskTrd].values, 'ys', label='Trd')
    plt.plot(df['Date'], df['pc_50_ma'], label='pc_50_ma', drawstyle='steps-post', linewidth=0.6, linestyle='--')
    plt.plot(df['Date'], df['pc_50_ma_ma'], label='pc_50_ma_ma', drawstyle='steps-post', linewidth=0.6, linestyle='--')
    
    plt.ylim((minY, maxY))
    plt.title('%s: %s' % (title, df.iloc[0]['Date'].strftime('%Y-%m-%d')), fontsize=18)    
    plt.ylabel('Prices', fontsize=18)
    plt.tick_params(axis='y', which='major', labelsize=14)
    plt.legend(loc='upper left')
    plt.tick_params(axis='x', which='major', labelsize=2)
    plt.grid()
    ax.get_yaxis().get_major_formatter().set_useOffset(False)
    
    #plt.subplot(212, sharex=ax) 
    plt.subplot(3,1,3, sharex=ax)
    
    plt.plot(df['Date'], df['pc_macd'], label='pc_macd', drawstyle='steps-post')
    plt.plot(df['Date'], df['pc_macd_signal'], label='pc_macd_signal', drawstyle='steps-post')
    plt.ylabel('MACD', fontsize=18)
    plt.xlabel('Time', fontsize=18)
    plt.tick_params(axis='x', which='major', labelsize=14)
    plt.legend(loc='upper left')
    plt.grid()
       
    
    plt.gcf().set_size_inches(15,8)
#    ax2 = plt.gca()
#    #ax1.get_yaxis().get_major_formatter().set_scientific(False)
#    ax2.get_yaxis().get_major_formatter().set_useOffset(False)
    

def pnl(times, pB, pA, trdLongPos, trdShortPos, risk, profit, scratch, minIncr, optimistic):
    '''risk, profit, and scratch are in units of minIncr'''
    
    profitB = []
    profitA = []
    gain = 0
    
    profitLvl = profit*minIncr
    scratchLvl = scratch*minIncr
    riskLvl = risk*minIncr
    
    sz = trdLongPos.shape[0]
    szTot = pB.shape[0]
    
    # Bids
    
    i = 0
    while i < sz:
        cnt = 0
        pos = trdLongPos[i]
        pBuy = pB[pos] if optimistic else pA[pos]               # buy on ask to enter (if not optimistic)

        while pos+cnt < szTot:
            
            pExit = pA[pos+cnt] if optimistic else pB[pos+cnt]  # sell on bid to exit (if not optimistic)
            
            if pExit > pBuy + profitLvl - 1.e-8:
           
                good = 1
                profit = (pExit - pBuy)/minIncr
                profitB.append([pos, good, pBuy, pExit, profit, times[pos], times[pos+cnt]])
                gain = gain + profit
                break
                
            elif pExit< pBuy - riskLvl + 1.e-8:
               
                good = 0
                profit = (pExit - pBuy)/minIncr
                profitB.append([pos, good, pBuy, pExit, profit, times[pos], times[pos+cnt]])               
                gain = gain + profit
                break
            
            cnt = cnt + 1
            
        # see how far forward to go for next try
        nextI = 1
        while i + nextI < sz and trdLongPos[i+nextI] < pos+cnt:
            nextI = nextI + 1
        
        i = i + nextI
      
    # Asks
    
    sz = trdShortPos.shape[0]
    szTot = pA.shape[0]
        
    i = 0
    while i < sz:
        cnt = 0
        pos = trdShortPos[i]
        pSell = pA[pos] if optimistic else pB[pos]              # sell on bid to enter (if not optimistic)

        while pos+cnt < szTot:
       
            pExit = pB[pos+cnt] if optimistic else pA[pos+cnt]  # buy on offer to exit (if not optimistic)
            
            if pExit < pSell - profitLvl + 1.e-8:
           
                good = 1
                profit = (pSell - pExit)/minIncr
                profitA.append([pos, good, pExit, pSell, profit, times[pos], times[pos+cnt]])
                gain = gain + profit
                break
                
            elif pExit > pSell + riskLvl - 1.e-8:
               
                good = 0
                profit = (pSell - pExit)/minIncr
                profitA.append([pos, good, pExit, pSell, profit, times[pos], times[pos+cnt]])
                gain = gain + profit
                break
            
            cnt = cnt + 1
            
        # see how far forward to go for next try
        nextI = 1
        while i + nextI < sz and trdShortPos[i+nextI] < pos+cnt:
            nextI = nextI + 1
        
        i = i + nextI
        
    
    return profitB, profitA, gain

def pnl_A(times, pB, pA, trdLongPos, trdShortPos, risk, profit, scratch, minIncr, optimistic):
    '''risk, profit, and scratch are in units of minIncr
       if we lose more than risk exit
       if we make more than profit than keep going until reversal of more than scratch
       
       TODO MEDIUM change scratch to look at mid to avoid wide market exit?
    '''
    
    profitB = []
    profitA = []
    gain = 0
    
    profitLvl = profit*minIncr
    scratchLvl = scratch*minIncr
    riskLvl = risk*minIncr
    
    sz = trdLongPos.shape[0]
    szTot = pB.shape[0]
    
    # Bids
    
    i = 0
    while i < sz:
        cnt = 0
        typeOfTrade = -1
        sawProfit = 0
        bestPrice = -9999
        pos = trdLongPos[i]
        pBuy = pB[pos] if optimistic else pA[pos]               # buy on ask to enter (if not optimistic)
        pExit = -9999

        while pos+cnt < szTot:
            
            pExit = pA[pos+cnt] if optimistic else pB[pos+cnt]  # sell on bid to exit (if not optimistic)
            
            if pExit < pBuy - riskLvl + 1.e-8:
                typeOfTrade = 0         # ie bad
                break
            elif pExit > pBuy + profitLvl - 1.e-8:
                sawProfit = 1
                if pExit > bestPrice: bestPrice = pExit
            
            if sawProfit == 1 and pExit < bestPrice - scratchLvl:
                typeOfTrade = 1         # ie good
                break
            
            cnt = cnt + 1
            
        if typeOfTrade > -1:
            profit = (pExit - pBuy)/minIncr
            profitB.append([pos, typeOfTrade, pBuy, pExit, profit, times[pos], times[pos+cnt]])
            gain = gain + profit
            
        # see how far forward to go for next try
        nextI = 1
        while i + nextI < sz and trdLongPos[i+nextI] < pos+cnt:
            nextI = nextI + 1
        
        i = i + nextI
      
    # Asks
    
    sz = trdShortPos.shape[0]
    szTot = pA.shape[0]
        
    i = 0
    while i < sz:
        cnt = 0
        typeOfTrade = -1
        sawProfit = 0
        bestPrice = 9999
        pos = trdShortPos[i]
        pSell = pA[pos] if optimistic else pB[pos]                     # sell on bid to enter (if not optimistic)
        pExit = 9999

        while pos+cnt < szTot:
            
            pExit = pB[pos+cnt] if optimistic else pA[pos+cnt]  # buy on offer to exit (if not optimistic)
            
            if pExit > pSell + riskLvl - 1.e-8:
                typeOfTrade = 0         # ie bad
                break    
            elif pExit < pSell - profitLvl + 1.e-8:
                sawProfit = 1
                if pExit < bestPrice: bestPrice = pExit
            
            if sawProfit == 1 and pExit > bestPrice + scratchLvl:
                typeOfTrade = 1         # ie good
                break
            
            cnt = cnt + 1
            
        if typeOfTrade > -1:
            profit = (pSell - pExit)/minIncr
            profitA.append([pos, typeOfTrade, pExit, pSell, profit, times[pos], times[pos+cnt]])
            gain = gain + profit
            
        # see how far forward to go for next try
        nextI = 1
        while i + nextI < sz and trdShortPos[i+nextI] < pos+cnt:
            nextI = nextI + 1
        
        i = i + nextI
        
    
    return profitB, profitA, gain

