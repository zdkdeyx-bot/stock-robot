import yfinance as yf
import pandas_ta as ta
import pandas as pd
from datetime import datetime

# ====== 1. 设置你的股票池 ======
# 格式：美股直接写代码，A股加后缀 (.SS上海, .SZ深圳)，港股 (.HK)
# 可以在这里随时修改
MY_WATCHLIST = ['NVDA', 'TSLA', 'AAPL', 'MSFT', '600519.SS', '000001.SZ'] 
MY_PORTFOLIO = ['COIN', 'GOOGL']  # 你的持仓，用于检测卖点

def check_stock(ticker):
    try:
        # 下载数据
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty: return None
        
        # 计算指标
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['MA50'] = ta.sma(df['Close'], length=50)
        df['MA200'] = ta.sma(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        df['MACD'] = macd['MACD_12_26_9']
        df['MACD_HIST'] = macd['MACDh_12_26_9']
        
        # 获取最新一天数据
        curr = df.iloc[-1]
        price = curr['Close']
        
        # --- 买入逻辑 ---
        # 1. 价格 > MA20, MA50, MA200 (多头排列)
        # 2. RSI > 50 (强势区)
        # 3. MACD > 0 (零轴之上)
        buy_score = 0
        if price > curr['MA20']: buy_score += 1
        if price > curr['MA50']: buy_score += 1
        if price > curr['MA200']: buy_score += 1
        if curr['RSI'] > 50: buy_score += 1
        if curr['MACD'] > 0: buy_score += 1
        
        # --- 卖出逻辑 (针对持仓) ---
        sell_signal = False
        reasons = []
        if price < curr['MA20']: 
            sell_signal = True; reasons.append("跌破MA20")
        if curr['MACD_HIST'] < 0 and curr['MACD_HIST'] < df.iloc[-2]['MACD_HIST']:
            sell_signal = True; reasons.append("MACD绿柱变长")
            
        return {
            "ticker": ticker,
            "price": price,
            "buy_score": buy_score,
            "sell_signal": sell_signal,
            "sell_reasons": reasons,
            "rsi": curr['RSI']
        }
        
    except Exception as e:
        print(f"Error: {ticker} - {e}")
        return None

if __name__ == "__main__":
    print(f"====== {datetime.now().strftime('%Y-%m-%d')} 市场扫描报告 ======\n")
    
    print("【🚀 潜在买入机会扫描】")
    print("(满分5分：MA20/50/200之上, RSI>50, MACD>0)")
    for stock in MY_WATCHLIST:
        res = check_stock(stock)
        if res and res['buy_score'] >= 4: # 稍微宽松点，4分以上就提醒
            print(f"✅ {stock} (现价:{res['price']:.2f}) 得分: {res['buy_score']}/5 | RSI: {res['rsi']:.1f}")
            
    print("\n" + "-"*30 + "\n")
    
    print("【⚠️ 持仓预警扫描】")
    for stock in MY_PORTFOLIO:
        res = check_stock(stock)
        if res and res['sell_signal']:
            print(f"❌ {stock} (现价:{res['price']:.2f}) 触发预警: {', '.join(res['sell_reasons'])}")
        else:
            print(f"🛡️ {stock} 安全。")
            
    print("\n扫描结束。")
