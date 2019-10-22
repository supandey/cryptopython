import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.dates as mdates
import pandas as pd
import os
import glob
import time

class PlotData:
    
    def __init__(self, fileName, title):
        self._filename = fileName
        self._minIncr = 0.01
        self._rowInFile = 0;
        
        self._figure1 = plt.figure(1)
        plt.ion()
        
        #---------------------------------------------
        self._ax1 = plt.subplot(3,1,(1,2))
        
        self._linePB, = plt.plot([], [], label='pB', drawstyle='steps-post')
        self._linePA, = plt.plot([], [], label='pA', drawstyle='steps-post')
        #self._linePT, = plt.plot([], [], 'ys', label='Trd')
        self._line10MAShort, = plt.plot([], [], label='pc10MaShort', drawstyle='steps-post', linewidth=0.4, linestyle='--')
        self._line50MAShort, = plt.plot([], [], label='pc50MaShort', drawstyle='steps-post', linewidth=0.6, linestyle='--')
        self._line50MALong, = plt.plot([], [], label='pc50MaLong', drawstyle='steps-post', linewidth=0.6, linestyle='--')
        
        plt.title('%s: %s' % (title, dt.datetime.now().strftime('%Y-%m-%d')), fontsize=18)    
        plt.ylabel('Prices', fontsize=18)
        plt.tick_params(axis='y', which='major', labelsize=14)
        plt.legend(loc='upper left')
        plt.tick_params(axis='x', which='major', labelsize=2)
        self._ax1.get_yaxis().get_major_formatter().set_useOffset(False)
    
        #---------------------------------------------
        
        self._ax2 = plt.subplot(3,1,3, sharex=self._ax1)
        
        self._macd, = plt.plot([], [], label='pc_macd', drawstyle='steps-post')
        self._macdSignal, = plt.plot([], [], label='pc_macd_signal', drawstyle='steps-post')
        plt.ylabel('MACD', fontsize=18)
        plt.xlabel('Time', fontsize=18)
        plt.tick_params(axis='x', which='major', labelsize=14)
        plt.legend(loc='upper left')
        
        #---------------------------------------------
        
        self._ax1.set_autoscaley_on(True)
        self._ax2.set_autoscaley_on(True)
        
        myFmt = mdates.DateFormatter('%H:%M:%S')
        self._ax1.xaxis.set_major_formatter(myFmt)
        self._ax2.xaxis.set_major_formatter(myFmt)
        
        self._ax1.grid()
        self._ax2.grid()
        
        plt.gcf().set_size_inches(15,8)

    def plotHelper(self):
        
        df = self._df
#        maskTrd = df['pT'] > 1.e-8
        
        self._linePB.set_xdata(df['Date'].values)
        self._linePB.set_ydata(df['pB'].values)
        
        self._linePA.set_xdata(df['Date'].values)
        self._linePA.set_ydata(df['pA'].values)
        
#        self._linePT.set_xdata(df['Date'][maskTrd].values)
#        self._linePT.set_ydata(df['pT'][maskTrd].values)
        
        self._line10MAShort.set_xdata(df['Date'].values)
        self._line10MAShort.set_ydata(df['pc10MaShort'].values)
        
        self._line50MAShort.set_xdata(df['Date'].values)
        self._line50MAShort.set_ydata(df['pc50MaShort'].values)
        
        self._line50MALong.set_xdata(df['Date'].values)
        self._line50MALong.set_ydata(df['pc50MaLong'].values)
        
        self._macd.set_xdata(df['Date'].values)
        self._macd.set_ydata(df['macd'].values)
        
        self._macdSignal.set_xdata(df['Date'].values)
        self._macdSignal.set_ydata(df['macdSignal'].values)
        
        #minY = df['pB'].min() - 3*minIncr;
        #maxY = df['pA'].max() + 3*minIncr;
        #plt.ylim((minY, maxY))
        
        #Need both of these in order to rescale
        self._ax1.relim()
        self._ax1.autoscale_view()
        
        self._ax2.relim()
        self._ax2.autoscale_view()
        
        self._ax2.axhline(y=0, xmin=0, xmax=1, color='g')
        
        #We need to draw *and* flush
        self._figure1.canvas.draw()
        self._figure1.canvas.flush_events()
        
    def readInitial(self):
        
        #namesCol = ['Date', 'Name', 'qB', 'pB', 'pA', 'qA', 'pT', 'qT', 'pc', 'pc10', 'pc50', 'pc10MaShort', 'pc50MaShort', 'pc50MaLong', 'macd', 'macdSignal']
        
        num_lines = 0
        try:
            fh = open(self._filename,'r')
            self._colNames = list(fh.readline()[:-1].split(','))
            num_lines = sum(1 for line in fh)
            #num_lines = 10
            self._rowInFile = num_lines - 2    # skip last rows in case incomplete write
            fh.close()
        except OSError as exception:
            print('Can not open file {}'.format(self._filename))
            return False
        
        #self._df = pd.DataFrame(columns=self._namesCol)
        dateparse = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f')
        self._df  = pd.read_csv(self._filename, delimiter='|', header=None, names=self._colNames, dtype={'Date': str}, parse_dates=['Date'], date_parser=dateparse, skiprows=1, nrows=self._rowInFile)
        
        print('num_lines: {}'.format(num_lines))
        
        return True
    
    def readIncr(self, dRows):
        
        bRet = True
        dateparse = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f')
        
        try:
            
            rowsPrev = len(self._df)
            print('readIncr before {}'.format(rowsPrev))
            
            df = pd.read_csv(self._filename, delimiter='|', header=None, names=self._colNames, dtype={'Date': str}, parse_dates=['Date'], date_parser=dateparse, skiprows=self._rowInFile+1, nrows=dRows)
            self._df = self._df.append(df)
            self._df = self._df.reset_index()
            del self._df['index']
            
            
            rowsRead = min(self._rowInFile+dRows, len(self._df))
            self._rowInFile = rowsRead
            
            if rowsPrev == len(self._df):         # no new data
                bRet = False     
            
            print('readIncr after {}'.format(len(self._df)))
            
        except Exception as ex:
           bRet = False
        
        return bRet
        

def driver(dPauseSec):
    #fileName = r'C:/hg/QR/Python/Users/Sanjeev/cryptoB/Strategy\data\Strategy_gdax_20180213_081202.log'
    #fileName = r'Strategy_gdax_20180213_081202.log'
    
    cwd = os.getcwd()
    fileFilter = '{}/*.log'.format(cwd)
    list_of_files = glob.glob(fileFilter)
    latest_file = max(list_of_files, key=os.path.getctime)
    print(latest_file)
    
    fileName = latest_file
    
    plotData = PlotData(fileName, 'gdax BTC')
    good = plotData.readInitial()
    
    while good:
    
        try:
            goodIncr = True
            while goodIncr:
                goodIncr = plotData.readIncr(2)
                   
            #plt.figure(1)
            plotData.plotHelper()
            time.sleep(dPauseSec)
            
        except KeyboardInterrupt:
                print('Exit driver loop')
                break
           

if __name__ == '__main__':
    driver(10)