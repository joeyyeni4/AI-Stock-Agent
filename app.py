import streamlit as st
import yfinance as yf
import ta
import google.generativeai as genai

# 1. 財務數據清洗器：解決百分比誤判
def format_pct(value):
    if isinstance(value, float):
        return f"{value * 100:.2f}%"
    return "N/A"

# 2. 核心分析函數：加入產業屬性辨識與邏輯優化
def analyze_stock(symbol, api_key):
    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in models if 'gemini' in m), models[0])
        model = genai.GenerativeModel(model_name)
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        info = ticker.info
        
        # 數據標準化
        gross_margin = format_pct(info.get('grossMargins'))
        revenue_growth = format_pct(info.get('revenueGrowth'))
        
        # 指標計算
        df['rsi'] = ta.momentum.rsi(df['Close'], window=14)
        
        # 提示詞強化：加入產業視角與邏輯限制
        prompt = f"""
        你是一位資深證券分析師，請針對 {symbol} 進行深度診斷。
        數據事實：毛利率 {gross_margin}，營收成長 {revenue_growth}，當前 RSI {df['rsi'].iloc[-1]:.2f}。
        
        分析要求：
        1. 數據解讀：石化業或相關產業毛利率受景氣循環影響，請依據上述數值客觀評價其獲利能力，勿僅以「孱弱」定論，需考慮產業週期。
        2. 技術面：RSI 46.97 屬盤整區間。請以布林通道中軸作為多空分界線，解釋當前股價相對強弱。
        3. 操作建議：保持中立客觀，說明在目前週期震盪下，投資人應關注的關鍵轉折點，而非簡單建議避開。
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"分析異常: {str(e)}"

# 3. 介面呈現
st.title("◎ 專業級台股分析 Agent")
api_key = st.sidebar.text_input("API Key", type="password")
symbol = st.sidebar.text_input("股號", "1710.TW")

if st.sidebar.button("開始診斷"):
    with st.spinner('進行深度邏輯運算中...'):
        st.markdown(analyze_stock(symbol, api_key))
