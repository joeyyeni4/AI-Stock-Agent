import streamlit as st
import yfinance as yf
import ta
import google.generativeai as genai

# --- 1. 數據校驗模組 ---
def get_verified_data(symbol):
    """
    雙重驗證機制：
    機制 A：確保數值有效提取並轉化為百分比。
    機制 B：檢查數值是否落在石化/化學產業的合理區間 (1%-50%)。
    """
    ticker = yf.Ticker(symbol)
    info = ticker.info
    
    # 提取與轉換
    raw_margin = info.get('grossMargins', 0)
    raw_growth = info.get('revenueGrowth', 0)
    
    margin = float(raw_margin) * 100 if raw_margin else 0.0
    growth = float(raw_growth) * 100 if raw_growth else 0.0
    
    # 邏輯合理性檢查 (若數據極端異常，判定為驗證失敗)
    # 此處設為 0.5% - 60% 作為石化/特化產業的合理預警線
    is_valid = 0.5 <= margin <= 60.0 
    
    return margin, growth, is_valid

# --- 2. 核心分析邏輯 ---
def analyze_stock(symbol, api_key):
    try:
        genai.configure(api_key=api_key)
        # 動態選取模型
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in models if 'gemini' in m), models[0] if models else None)
        model = genai.GenerativeModel(model_name)
        
        # 進行數據驗證
        margin, growth, is_valid = get_verified_data(symbol)
        
        if not is_valid:
            return f"❌ **數據驗證失敗**：偵測到該個股財報數據異常 (毛利率: {margin:.2f}%)，系統已自動中止分析以避免產生錯誤結論。請確認代號是否正確或該數據是否為臨時性斷層。"

        # 技術指標計算
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        rsi = ta.momentum.rsi(df['Close'], window=14).iloc[-1]
        
        prompt = f"""
        你是一位極度嚴謹的證券分析師。請僅根據以下提供的【數據事實】進行分析，嚴禁自行聯想或引用外部知識庫中可能錯誤的歷史資料。
        
        【數據事實】
        - 標的代號: {symbol}
        - 毛利率: {margin:.2f}%
        - 營收年成長率: {growth:.2f}%
        - 當前 RSI: {rsi:.2f}
        
        【分析框架】
        1. 數據性質客觀陳述：針對提供的毛利率與成長率進行數值意義上的評估。
        2. 技術指標解析：基於 RSI (46-55為盤整區間) 與布林通道中軸邏輯，說明股價運作狀態。
        3. 投資觀察清單：列出投資人應持續追蹤的 3 個關鍵數據轉折點。
        
        請以條列式輸出，保持專業、客觀、冷靜的口吻。
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"分析過程發生系統異常: {str(e)}"

# --- 3. 介面呈現 ---
st.title("◎ 專業級台股分析 Agent (嚴謹驗證版)")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
symbol = st.sidebar.text_input("輸入台股代號 (如 1710.TW)", "1710.TW")

if st.sidebar.button("開始專業診斷"):
    if not api_key:
        st.warning("請在側邊欄輸入 API Key")
    else:
        with st.spinner('進行數據雙重驗證中...'):
            st.markdown(analyze_stock(symbol, api_key))
