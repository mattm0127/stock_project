import yfinance as yf   

amd = yf.Ticker('msft')
df = amd.history('5y', '1d')
#print(df.Open[0])

stock = yf.Ticker('sdfgb')
df2 = stock.history('5y')
print(len(df2))