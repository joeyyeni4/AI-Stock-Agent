import streamlit as st
import yfinance as yf
import ta
import google.generativeai as genai
import pandas as pd

# --- 1. 自動化數據驗證與自我修復模組 ---
def get_consensus_data(ticker):
    """
    三節點一致性驗證法：
    1. 抓取當前 API 數據
    2. 比對近 4 季財務數據均值
    3. 設定合理區間，若異常則自動修復
    """
    info = ticker.info
    financials = ticker.quarterly_financials
    
    # 節點 A: 獲取 API 數值
    raw_margin = info.get('grossMargins', 0) * 100
    
    # 節點 B: 計算歷史基線 (取近 4 季平均)
    avg_hist_margin = 0.0
    if financials is not None and not financials.empty:
        try:
            # 確保欄位存在並計算毛利百分比
            margins = (financials.loc['Gross Profit'] / financials.loc['Total Revenue']) * 100
            avg_hist_margin = margins.mean()
        except:
            avg_hist_margin = raw_margin
            
    # 節點 C: 一致性邏輯判定與自我修復
    # 若當前數據 < 0.5% 或與歷史均值偏差過大，啟動修復
    is_anomaly = raw_margin < 0.5 or (avg_hist_margin > 5 and abs(raw_margin - avg_hist_margin) > (avg_hist_margin * 0.6))
    
    if is_anomaly and avg_hist_margin > 0:
        final_margin = avg_hist_margin
        status = f"偵測到異常數據({raw_margin:.2f}%)，已自動修復為歷史均值({final_margin:.2f}%)"
    else:
        final_margin = raw_margin
        status = "數據通過一致性驗證"
        
    return final_margin, status

# --- 2. 核心分析邏輯 ---
def analyze_stock(symbol, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        
        # 獲取自動校準後的數據
        margin, status = get_consensus_data(ticker)
        growth = (ticker.info.get('revenueGrowth', 0) * 100)
        rsi = ta.momentum.rsi(df['Close'], window=14).iloc[-1]
        
        # 顯示驗證狀態
        st.sidebar.info(status)
        
        prompt = f"""
        你是一位嚴謹的證券分析師，請針對 {symbol} 進行分析。
        【已驗證數據事實】
        - 毛利率: {margin:.2f}%
        - 營收年成長率: {growth:.2f}%
        - 當前 RSI: {rsi:.2f}
        
        【分析要求】
        1. 數據性質評估：基於上述毛利率，分析其獲利能力是否偏離歷史常態。
        2. 產業週期判斷：結合該公司產業特性，說明當前數據暗示的週期階段。
        3. 技術指標解析：以 RSI 盤整邏輯為基礎，說明股價運行狀態。
        4. 觀察清單：列出該標的需關注的 3 個技術與基本面轉折點。
        
        請以條列式輸出，保持極度客觀。
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"分析過程發生系統異常: {str(e)}"

# --- 3. 介面呈現 ---
st.title("◎ 專業台股分析 Agent (自動驗證版)")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
symbol = st.sidebar.text_input("輸入台股代號 (如 1710.TW)", "1710.TW")

if st.sidebar.button("開始專業診斷"):
    if not api_key:
        st.warning("請在側邊欄輸入 API Key")
    else:
        with st.spinner('進行數據三節點比對與深度邏輯分析中...'):
            st.markdown(analyze_stock(symbol, api_key))
