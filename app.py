import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai
from google.genai import types

# 網頁基本設定
st.set_page_config(page_title="台股 Gemini AI 分析台", layout="wide")
st.title("🤖 Gemini 專屬台股智慧分析 Agent")

# 側邊欄參數設定
with st.sidebar:
    st.header("系統設定")
    gemini_api_key = st.text_input("輸入您的 Gemini API Key", type="password")
    stock_symbol = st.text_input("輸入台股代號 (上市後綴 .TW / 上櫃後綴 .TWO)", value="1597.TW")
    analyze_btn = st.button("啟動 Gemini 全方位分析")

# 核心分析邏輯
if analyze_btn:
    if not gemini_api_key:
        st.warning("請先在左側欄填入您的 Gemini API Key。")
    else:
        with st.spinner("正在下載台股數據並傳送至 Gemini 進行分析..."):
            try:
                # 1. 抓取股票數據
                ticker = yf.Ticker(stock_symbol)
                # 抓取 3 個月的數據以利計算 20 日均線
                df = ticker.history(period="3mo")
                info = ticker.info
                
                if not df.empty:
                    st.success(f"成功取得 {stock_symbol} 歷史數據！")
                    
                    # 2. 計算技術指標
                    df['MA5'] = df['Close'].rolling(window=5).mean()
                    df['MA20'] = df['Close'].rolling(window=20).mean()
                    
                    # 擷取最新一天的數據
                    latest_data = df.iloc[-1]
                    latest_close = latest_data['Close']
                    latest_ma5 = latest_data['MA5']
                    latest_ma20 = latest_data['MA20']
                    latest_volume = latest_data['Volume']
                    
                    # 顯示近期走勢圖
                    st.subheader("📊 近期收盤價與均線走勢")
                    plot_data = df[['Close', 'MA5', 'MA20']].tail(30)
                    st.line_chart(plot_data)
                    
                    # 3. 建立 Gemini 客製化金融提示詞
                    company_name = info.get('longName', stock_symbol)
                    market_cap = info.get('marketCap', '未知')
                    pe_ratio = info.get('trailingPE', '未知')
                    
                    finance_prompt = f"""
                    你是一位精通台股與台灣科技業供應鏈（例如半導體、自動化設備、工業機器人等）的資深投資長。
                    請針對以下數據與背景，為股票代碼 {stock_symbol} ({company_name}) 進行全方位的多視角分析與短期股價預測。

                    【基本面數據】
                    - 市值: {market_cap}
                    - 本益比 (P/E): {pe_ratio}

                    【最新技術面指標】
                    - 當日收盤價: {latest_close:.2f} 元
                    - 5日均線 (MA5): {latest_ma5:.2f} 元
                    - 20日均線 (MA20): {latest_ma20:.2f} 元
                    - 當日成交量: {latest_volume} 股

                    【分析要求】
                    1. 技術面評估：比較當前股價、MA5 與 MA20 的關係，說明目前屬於多頭、空頭還是區間震盪，並指出潛在的支撐或壓力。
                    2. 產業面解讀：結合你對該產業（如自動化族群）近期在市場上的供應鏈動態，推論其基本面利基。
                    3. 綜合預測與策略：給出未來一週的走勢預測，並提供具體的風險控管建議（不要給出模糊的回答，請給出明確的邏輯推論）。
                    """
                    
                    # 4. 呼叫新版 Gemini API
                    client = genai.Client(api_key=gemini_api_key)
                    response = client.models.generate_content(
                        model='gemini-1.5-pro',  # 亦可改用較快較便宜的 'gemini-1.5-flash'
                        contents=finance_prompt
                    )
                    
                    # 5. 渲染 AI 報告
                    st.subheader("🤖 Gemini 投資長綜合評估報告")
                    st.markdown(response.text)
                    
                else:
                    st.error("找不到該股票數據，請確認代號是否正確。")
            except Exception as e:
                st.error(f"系統執行錯誤：{e}")