import os
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
API=os.getenv("API_URL","http://localhost:8000")
st.set_page_config(page_title="Quant Market Intelligence",page_icon="📈",layout="wide")
st.title("🇮🇳 Quant Market Intelligence")
st.caption("NSE equities · Mutual funds · ML signal research | Research tool, not investment advice")

with st.sidebar:
    st.header("Provider & controls")
    provider=st.selectbox("Preferred data provider",["YFINANCE","ANGEL_ONE","ZERODHA","DHAN","UPSTOX"])
    st.caption("Broker providers require API credentials, sessions, and adapter implementations; public YFinance works without broker login.")
    st.selectbox("Prediction confidence threshold",[0.55,0.60,0.65,0.70,0.75],index=2)
    st.button("Connect Zerodha",disabled=True,help="OAuth token exchange is not configured yet")
    st.button("Connect Upstox",disabled=True,help="OAuth token exchange is not configured yet")

cols=st.columns(4)
for col,title,value in zip(cols,["Nifty 50","India VIX","Signals Today","Shadow Accuracy"],["—","—","0","N/A"]):
    col.metric(title,value)

st.subheader("Instrument explorer")
query=st.text_input("Find stock by ticker or company name",placeholder="e.g. RELIANCE or Tata")
selected_ticker=None
if query:
    try:
        res=requests.get(f"{API}/api/v1/instruments/search",params={"q":query},timeout=8).json()
        options={f"{x['ticker']} — {x.get('name','')}":x["ticker"] for x in res}
        if options:
            selected=st.selectbox("Matching instruments",list(options.keys()))
            selected_ticker=options[selected]
        else: st.info("No instrument found. Run the instrument sync from the API or DAG first.")
    except Exception as e: st.warning(f"Instrument API unavailable: {e}")
if selected_ticker:
    st.subheader(f"{selected_ticker} historical chart")
    period=st.selectbox("History period",["3mo","6mo","1y","2y","5y"],index=2)
    try:
        data=requests.get(f"{API}/api/v1/market/history/{selected_ticker}",params={"provider":provider,"period":period},timeout=30).json()
        bars=pd.DataFrame(data.get("bars",[]))
        if not bars.empty:
            date_col=next((c for c in bars.columns if c.lower().startswith("date")),bars.columns[0])
            bars[date_col]=pd.to_datetime(bars[date_col])
            # yfinance returns OHLC column casing; API may have adjusted casing later.
            def find_col(label): return next((c for c in bars.columns if c.lower()==label),None)
            o,h,l,c=find_col("open"),find_col("high"),find_col("low"),find_col("close")
            if all([o,h,l,c]):
                fig=go.Figure(data=[go.Candlestick(x=bars[date_col],open=bars[o],high=bars[h],low=bars[l],close=bars[c],name=selected_ticker)])
                fig.update_layout(height=520,xaxis_rangeslider_visible=False)
                st.plotly_chart(fig,use_container_width=True)
            else: st.dataframe(bars,use_container_width=True)
        else: st.warning("No historical candles returned for the selected provider/ticker.")
    except Exception as e: st.error(f"Could not load historical bars: {e}")

st.subheader("Prediction research")
st.info("Model training, calibrated consensus, signal outcome tracking, and broker-authenticated data feeds are scaffolded but not activated until historical data and credentials are verified. No simulated signal is shown as a real prediction.")
st.subheader("Mutual funds")
st.write("MFapi.in NAV ingestion endpoint integration is planned in this scaffold; mutual-fund NAV data and forecasting are not yet active.")
