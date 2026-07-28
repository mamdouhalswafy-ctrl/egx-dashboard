import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import ta
import os

st.set_page_config(page_title="EGX30 Dashboard", layout="wide")
st.title("📊 تحليل مؤشر EGX30")
st.warning("⚠ هذا التحليل فني فقط ولا يمثل نصيحة استثمارية")

DATA_FILE = "egx_data.csv"

@st.cache_data(ttl=3600)
def load_data():
    if not os.path.exists(DATA_FILE):
        return None
    df = pd.read_csv(DATA_FILE)
    df['Date'] = pd.to_datetime(df['Date'])
    return df.sort_values('Date')

df = load_data()

if df is None or df.empty:
    st.error("❌ لا توجد بيانات بعد. يرجى الانتظار حتى يتم تشغيل التحديث التلقائي.")
    st.info("🕒 آخر تحديث مجدول: الساعة 3:30 مساءً (بتوقيت القاهرة)")
    st.stop()

if len(df) > 20:
    df['SMA20'] = ta.trend.sma_indicator(df['Close'], 20)
    df['SMA50'] = ta.trend.sma_indicator(df['Close'], 50)
    df['RSI'] = ta.momentum.rsi(df['Close'], 14)
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()

st.subheader("📋 آخر 5 أيام")
st.dataframe(df[['Date', 'Symbol', 'Close', 'Volume']].tail(5), use_container_width=True)

has_ohlc = not (df[['Open', 'High', 'Low']].isna().all().all())
st.subheader("📈 الرسم البياني")

if has_ohlc:
    fig = go.Figure(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))
else:
    fig = go.Figure(go.Scatter(x=df['Date'], y=df['Close'], mode='lines', name='EGX30'))

if 'SMA20' in df.columns:
    fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA20'], name='SMA20', line=dict(color='orange')))
if 'SMA50' in df.columns:
    fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA50'], name='SMA50', line=dict(color='blue')))

fig.update_layout(height=500, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

if len(df) > 20:
    last = df.iloc[-1]
    st.subheader("🔍 قراءة فنية")
    st.metric("آخر إغلاق", f"{last['Close']:.2f}")
    st.metric("RSI", f"{last['RSI']:.2f}")
    if last['RSI'] < 30:
        st.info("📉 RSI أقل من 30 (تشبع بيعي فني)")
    elif last['RSI'] > 70:
        st.info("📈 RSI أكبر من 70 (تشبع شرائي فني)")
    else:
        st.info("➖ RSI في منطقة حيادية")
    if last['Close'] > last['SMA50']:
        st.info(f"📊 السعر فوق المتوسط المتحرك 50 يوم")
    else:
        st.info(f"📊 السعر تحت المتوسط المتحرك 50 يوم")

st.caption("💡 هذه قراءة فنية فقط، وليست نصيحة مالية")
