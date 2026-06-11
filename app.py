import streamlit as st
import yfinance as yf
import ta
import google.generativeai as genai

# 1. 介面與基本設定
st.title("◎ Gemini 專屬台股智慧分析 Agent")
st.sidebar.header("系統參數設定")
api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")
stock_symbol = st.sidebar.text_input("輸入台股代號 (如 1597.TW)", "1597.TW")

# 2. 核心分析函數
def analyze_stock(symbol, api_key):
    try:
        genai.configure(api_key=api_key)
        
        # 動態抓取可用模型，避免 404 錯誤
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 自動選擇一個支援的模型名稱
        model_name = next((m for m in models if 'gemini' in m), models[0] if models else None)
        
        if not model_name:
            return f"錯誤：找不到可用的 Gemini 模型。偵測到的模型列表: {models}"
            
        model = genai.GenerativeModel(model_name)
        
        # 資料抓取
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        info = ticker.info
        
        if df.empty:
            return "錯誤：找不到該股票資料，請檢查代號是否正確 (例如需加 .TW)。"
            
        # 技術指標計算
        df['rsi'] = ta.momentum.rsi(df['Close'], window=14)
        bb = ta.volatility.BollingerBands(close=df['Close'], window=20)
        
        # 準備分析提示詞
        prompt = f"""
        你是一位專業的台股分析師，請針對 {symbol} 進行診斷：
        1. 基本面：毛利率 {info.get('grossMargins', 'N/A')}, 營收成長 {info.get('revenueGrowth', 'N/A')}。
        2. 技術面：當前 RSI 為 {df['rsi'].iloc[-1]:.2f}，價格是否在布林通道下軌邊緣: {df['Close'].iloc[-1] <= bb.bollinger_lband().iloc[-1]}。
        
        請提供一份精簡且專業的診斷報告，包含：
        - 公司體質評估
        - 短線進場技術訊號
        - 綜合操作建議（積極進場/觀察/避開）
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"分析過程中發生錯誤 (可能是模型名稱或權限問題): {str(e)}"

# 3. 按鈕動作邏輯
if st.sidebar.button("開始診斷"):
    if not api_key:
        st.warning("請在側邊欄輸入 API Key")
    else:
        with st.spinner('Gemini 正在深入分析中...'):
            result = analyze_stock(stock_symbol, api_key)
            st.markdown(result)
