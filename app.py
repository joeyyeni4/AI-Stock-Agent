if st.sidebar.button("開始診斷"):
    if not api_key:
        st.warning("請在側邊欄輸入 API Key")
    else:
        with st.spinner('Gemini 正在深入分析中...'):
            try:
                genai.configure(api_key=api_key)
                # 自動偵測可用的模型，避免 404 錯誤
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                if not available_models:
                    st.error("找不到可用的 Gemini 模型，請檢查 API Key 權限。")
                else:
                    # 優先使用 gemini-1.5-flash，若無則使用列表第一個
                    model_name = next((m for m in available_models if 'gemini-1.5-flash' in m), available_models[0])
                    model = genai.GenerativeModel(model_name)
                    
                    # 進行分析
                    result = analyze_stock(stock_symbol, api_key) # 呼叫您原本的分析函數
                    st.markdown(result)
            except Exception as e:
                st.error(f"連線或分析發生錯誤: {str(e)}")
