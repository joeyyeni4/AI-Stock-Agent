import streamlit as st
import yfinance as yf
import ta
import google.generativeai as genai

# 設定頁面標題
st.title("◎ Gemini 專屬台股智慧分析 Agent")
st.sidebar.header("系統參數設定")

# 側邊欄輸入
api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")
stock_symbol = st.sidebar.text_input("輸入台股代號 (如 1597.TW)", "1597.TW")

# 分析函數
def analyze_stock(symbol, api_key):
    try:
        genai.configure(api_key=api_key)
        # 嘗試使用通用名稱，若失敗再改
        model = genai.GenerativeModel('gemini-pro')
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        info = ticker.info
        
        if df.empty:
            return "錯誤：找不到資料，請確認代號格式正確。"
        
        df['rsi'] = ta.momentum.rsi(df['Close'], window=14)
        
        prompt = f"請分析股票 {symbol}。基本面：毛利率 {info.get('grossMargins', 'N/A')}。技術面：當前RSI {df['rsi'].iloc[-1]:.2f}。請給予分析與建議。"
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"分析過程發生錯誤: {str(e)}"

# 按鈕動作
if st.sidebar.button("開始診斷"):
    if not api_key:
        st.warning("請在側邊欄輸入 API Key")
    else:
        with st.spinner('Gemini 正在分析...'):
            result = analyze_stock(stock_symbol, api_key)
            st.markdown(result)
