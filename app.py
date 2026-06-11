def get_comprehensive_analysis(ticker, df):
    # 1. 抓取基本面數據
    info = ticker.info
    gross_margin = info.get('grossMargins', 'N/A')
    revenue_growth = info.get('revenueGrowth', 'N/A')
    
    # 2. 進行技術面計算
    import ta
    df['rsi'] = ta.momentum.rsi(df['Close'], window=14)
    indicator_bb = ta.volatility.BollingerBands(close=df['Close'], window=20)
    df['bb_l'] = indicator_bb.bollinger_lband()
    
    # 3. 組合 Prompt 給 Gemini
    prompt = f"""
    你現在是一位結合「價值投資」與「短線技術分析」的 AI 交易顧問。
    請針對股票進行深度診斷：
    - 基本面數據：毛利率 {gross_margin}, 營收成長 {revenue_growth}。
    - 技術面數據：當前 RSI 為 {df['rsi'].iloc[-1]:.2f}, 當前價格與布林下軌關係為 {df['Close'].iloc[-1] <= df['bb_l'].iloc[-1]}。
    
    請執行雙層過濾分析：
    1. [基本面檢查]：若營收成長為負，請發出預警。
    2. [技術面監測]：評估短線進場點與支撐壓力。
    3. [綜合結論]：給出明確的操作建議（積極進場/觀察/避開）。
    """
    return prompt
