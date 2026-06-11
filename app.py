import streamlit as st
import yfinance as yf
import ta
import google.generativeai as genai

# --- 1. 數據守門員：格式化與單位校準 ---
def clean_financial_data(info):
    """ 強制將財報數據清洗為標準百分比格式 """
    raw_margin = info.get('grossMargins')
    raw_growth = info.get('revenueGrowth')
    
    # 邏輯：若值小於 1，通常是小數格式 (0.03 -> 3%)；若大於 1，則視為原始百分比
    margin = (raw_margin * 100) if raw_margin and raw_margin < 1 else (raw_margin or 0)
    growth = (raw_growth * 100) if raw_growth and raw_growth < 1 else (raw_growth or 0)
    
    return round(float(margin), 2), round(float(growth), 2)

# --- 2. 核心分析邏輯 ---
def analyze_stock(symbol, api_key, m_margin, m_growth):
    try:
        genai.configure(api_key=api_key)
        # 動態抓取模型
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in models if 'gemini' in m), models[0] if models else None)
        model = genai.GenerativeModel(model_name)
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        info = ticker.info
        
        # 進行數據清洗
        auto_margin, auto_growth = clean_financial_data(info)
        
        # 軌道決策：若手動輸入不為 0，則強制覆蓋 API 數據
        margin = m_margin if m_margin != 0 else auto_margin
        growth = m_growth if m_growth != 0 else auto_growth
        
        # 顯示當前使用的數據供用戶核對
        st.sidebar.info(f"當前分析使用數據\n毛利率: {margin}%\n營收成長: {growth}%")
        
        df['rsi'] = ta.momentum.rsi(df['Close'], window=14)
        
        prompt = f"""
        你是一位專業的證券分析師，請針對 {symbol} 進行診斷。
        數據事實 (已校準)：毛利率 {margin}%，營收成長 {growth}%，當前 RSI {df['rsi'].iloc[-1]:.2f}。
        
        分析要求：
        1. 獲利能力解讀：基於上述毛利率，評價其獲利穩定性，勿使用簡單主觀形容詞。
        2. 產業背景：請結合石化業循環特性分析目前的營運逆風。
        3. 技術面：以布林通道中軸為分界，結合 RSI 盤整區間 (40-60) 進行分析。
        4. 結論：列出該個股未來觀察的「關鍵轉折轉折指標」。
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"分析發生錯誤: {str(e)}"

# --- 3. 介面呈現 ---
st.title("◎ 專業級台股分析 Agent (雙軌數據)")
st.sidebar.header("系統參數")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
symbol = st.sidebar.text_input("輸入股號 (如 1710.TW)", "1710.TW")

st.sidebar.subheader("手動校準 (修正異常數據)")
m_margin = st.sidebar.number_input("強制修正毛利率 (%)", value=0.0)
m_growth = st.sidebar.number_input("強制修正營收年增率 (%)", value=0.0)

if st.sidebar.button("開始專業診斷"):
    if not api_key:
        st.warning("請先輸入 API Key")
    else:
        with st.spinner('進行邏輯校驗與深度分析中...'):
            st.markdown(analyze_stock(symbol, api_key, m_margin, m_growth))
