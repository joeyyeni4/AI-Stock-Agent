import streamlit as st
import yfinance as yf
import ta
import google.generativeai as genai

# 1. 介面與基本設定
st.title("◎ Gemini 專屬台股智慧分析 Agent")
st.sidebar.header("系統參數設定")
api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")
stock_symbol = st.sidebar.text_input("輸入台股代號 (如 1597.TW)", "1597.TW")

# 2. 核心分析邏輯
def analyze_stock(symbol, api_key):
    try:
        # 抓取資料
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        info = ticker.info
        
        if df.empty:
            return "錯誤：找不到該股票代號，請檢查是否正確（台股需加 .TW 或 .TWO）。"
            
        # 計算技術指標
        df['rsi'] = ta.momentum.rsi(df['Close'], window=14)
        bb = ta.volatility.BollingerBands(close=df['Close'], window=20)
        
        # 準備 AI 提示詞
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        你是一位專業的台股分析師。請分析 {symbol}。
        基本面資訊：毛利率 {info.get('grossMargins', 'N/A')}, 營收成長 {info.get('revenueGrowth', 'N/A')}。
        技術面資訊：當前 RSI 為 {df['rsi'].iloc[-1]:.2f}, 當前價格 {df['Close'].iloc[-1]}，是否低於布林下軌 {df['Close'].iloc[-1] <= bb.bollinger_lband().iloc[-1]}。
        
        請提供一份精簡診斷：
        1. 基本面是否健康？
        2. 短線進場技術訊號為何？
        3. 綜合操作建議（積極/觀察/避開）。
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"分析過程發生錯誤: {str(e)}"

# 3. 按鈕觸發
if st.sidebar.button("開始診斷"):
    if not api_key:
        st.warning("請在側邊欄輸入 API Key")
    else:
        with st.spinner('Gemini 正在深入分析中...'):
            result = analyze_stock(stock_symbol, api_key)
            st.markdown(result)
