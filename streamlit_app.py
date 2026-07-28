import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Ain EGX V12 Full Analysis", layout="wide", page_icon="👁️")
st.title("👁️ عين على البورصة V12 - تحليل كامل")
st.caption("بحث حر عن اي سهم EGX - بدون هلوسة - بيانات حية من Yahoo")

def calculate_rsi_wilder(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 0.0001)
    return 100 - (100 / (1 + rs))

def calculate_ain_score_full(hist):
    close = hist['Close']
    volume = hist['Volume']
    high = hist['High']
    low = hist['Low']
    rsi = float(calculate_rsi_wilder(close).iloc[-1])
    sma20 = float(close.rolling(20).mean().iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close)>=200 else sma50
    last = float(close.iloc[-1])
    vol_avg = float(volume.rolling(20).mean().iloc[-1])
    vol_last = float(volume.iloc[-1])
    score = 50
    reasons = []
    if rsi < 30: score+=15; reasons.append(f"RSI {rsi:.1f} Oversold Strong (+15)")
    elif rsi < 40: score+=8; reasons.append(f"RSI {rsi:.1f} Buy Bias (+8)")
    elif rsi > 70: score-=15; reasons.append(f"RSI {rsi:.1f} Overbought (-15)")
    elif rsi > 60: score-=8; reasons.append(f"RSI {rsi:.1f} Sell Bias (-8)")
    else: reasons.append(f"RSI {rsi:.1f} Neutral")
    if last > sma20 > sma50: score+=10; reasons.append("Above SMA20/50 Uptrend (+10)")
    elif last < sma20 < sma50: score-=10; reasons.append("Below SMA20/50 Downtrend (-10)")
    if last > sma200: score+=5; reasons.append("Above SMA200 Long Uptrend (+5)")
    else: score-=5; reasons.append("Below SMA200 Long Downtrend (-5)")
    if vol_last > vol_avg*1.5: score+=8; reasons.append(f"High Volume {vol_last/vol_avg:.1f}x (+8)")
    high_60 = float(high.rolling(60).max().iloc[-1])
    low_60 = float(low.rolling(60).min().iloc[-1])
    if last > high_60*0.95: score-=7; reasons.append("Near 60d High (-7)")
    if last < low_60*1.05: score+=7; reasons.append("Near 60d Low (+7)")
    prev = float(close.iloc[-2])
    chg = (last-prev)/prev*100
    if chg > 3: score+=7; reasons.append(f"Strong Daily Up {chg:.1f}% (+7)")
    elif chg < -3: score-=7; reasons.append(f"Strong Daily Down {chg:.1f}% (-7)")
    score = max(0, min(100, round(score,1)))
    return score, reasons, rsi, sma20, sma50, chg

@st.cache_data(ttl=600, show_spinner=False)
def get_hist_stable(symbol_raw):
    sym = symbol_raw.strip().upper()
    if not sym: return None, "Empty", ""
    if not sym.endswith(".CA"): sym = sym + ".CA"
    ticker = yf.Ticker(sym)
    hist = ticker.history(period="1y", auto_adjust=True)
    if hist is None or hist.empty or len(hist) < 50:
        return None, f"Symbol {sym} not found on Yahoo", sym
    return hist.dropna(), "Success", sym

query = st.text_input("🔍 Search Any EGX Symbol (e.g. COMI, FWRY, ABUK)", placeholder="COMI")
if query:
    with st.spinner(f"Analyzing {query}..."):
        hist, msg, sym_final = get_hist_stable(query)
    if hist is None:
        st.error(msg)
    else:
        score, reasons, rsi, sma20, sma50, chg = calculate_ain_score_full(hist)
        last = float(hist['Close'].iloc[-1])
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Symbol", sym_final.replace('.CA',''))
        c2.metric("Price", f"{last:.2f}")
        c3.metric("Ain Score V12", f"{score}/100")
        c4.metric("RSI Wilder", f"{rsi:.1f}")
        st.divider()
        st.subheader("📊 Ain Score V12 Breakdown (Real Data Only)")
        for r in reasons:
            if "+" in r: st.success(r)
            elif "-" in r: st.error(r)
            else: st.info(r)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price"))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'].rolling(20).mean(), name="SMA20", line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'].rolling(50).mean(), name="SMA50", line=dict(color='blue')))
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Type any symbol above to start - e.g. COMI, FWRY, ABUK, TMGH")
