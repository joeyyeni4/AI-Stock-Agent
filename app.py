import streamlit as st
import yfinance as yf
import ta
import google.generativeai as genai

# --- 1. 自動化數據驗證與自我修復模組 ---
def get_consensus_data(ticker):
    info = ticker.info
    financials = ticker.quarterly_financials
    raw_margin = info.get('grossMargins', 0) * 100
    
    avg_hist_margin = 0.0
    if financials is not None and not financials.empty:
        try:
            margins = (financials.loc['Gross Profit'] / financials.loc['Total Revenue']) * 100
            avg_hist_margin = margins.mean()
        except:
            avg_hist_margin = raw_margin
            
    is_anomaly = raw_margin < 0.5 or (avg_hist_margin > 5 and abs(raw_margin - avg_hist_margin) > (avg_hist_margin * 0.6))
    
    if is_anomaly and avg_hist_margin > 0:
        final_margin = avg_hist_margin
        status = f"已自動修復異常數據({raw_margin:.2f}%)至歷史均值({final_margin:.2f}%)"
    else:
        final_margin = raw_margin
        status = "數據通過一致性驗證"
        
    return final_margin, status

# --- 2. 核心分析邏輯 (自動化模型識別) ---
def analyze_stock(symbol, api_key):
    try:
        genai.configure(api_key=api_key)
        
        # 【自動識別機制】直接詢問 API 權限內可用的模型
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not models:
            return "錯誤：找不到任何可用的模型，請檢查 API Key 是否已開通權限。"
        
        # 選取第一個出現的 gemini 模型
        model_name = next((m for m in models if 'gemini' in m), models[0])
        model = genai.GenerativeModel(model_name)
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        margin, status = get_consensus_data(ticker)
        growth = (ticker.info.get('revenueGrowth', 0) * 100)
        rsi = ta.momentum.rsi(df['Close'], window=14).iloc[-1]
        
        st.sidebar.info(f"檢核狀態: {status}")
        
        prompt = f"""
        你是一位證券分析師，請針對 {symbol} 進行嚴謹分析。
        數據事實: 毛利率 {margin:.2f}%, 營收成長 {growth:.2f}%, RSI {rsi:.2f}。
        請以客觀條列式回答：數據評價、產業景氣判斷、關鍵轉折指標。
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"系統異常: {str(e)}"

# --- 3. 介面 ---
st.title("◎ 專業台股分析 Agent")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
symbol = st.sidebar.text_input("代號", "1710.TW")

if st.sidebar.button("開始診斷"):
    if not api_key:
        st.warning("請輸入 Key")
    else:
        st.markdown(analyze_stock(symbol, api_key))
