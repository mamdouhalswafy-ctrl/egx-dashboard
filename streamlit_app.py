import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="عين على البورصة - بحث حر", layout="wide", page_icon="🔍")
st.title("🔍 عين على البورصة - بحث حر بدون هلوسة")
st.caption("اكتب أي رمز EGX وهيجيبه لايف من Yahoo - ممنوع نألف بيانات")

def calculate_rsi_wilder(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 0.0001)
    return 100 - (100 / (1 + rs))

def analyze_any_symbol(raw_symbol):
    # تنظيف الرمز
    sym = raw_symbol.strip().upper()
    if not sym: return None, "اكتب رمز"
    if not sym.endswith(".CA"): sym = sym + ".CA"
    
    try:
        hist = yf.download(sym, period="1y", interval="1d", threads=False, progress=False, auto_adjust=True)
        if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
        hist = hist.dropna()
        if len(hist) < 40:
            return None, f"الرمز {sym} غير موجود أو بياناته قليلة على Yahoo"
        return hist, sym
    except Exception as e:
        return None, f"فشل جلب {sym} - {str(e)[:100]}"

# --- خانة البحث الحر ---
st.subheader("ابحث عن أي سهم EGX")
query = st.text_input("اكتب رمز السهم (مثال: COMI أو COMI.CA أو FWRY)", placeholder="COMI").strip()

if query:
    with st.spinner(f"جاري جلب {query} لايف..."):
        hist, msg = analyze_any_symbol(query)
    
    if hist is None:
        st.error(msg)
        st.warning("تحقق يدوياً بدون هلوسة:")
        st.markdown(f"- [مباشر مصر - {query}](https://www.mubasher.info/markets/EGX/stocks/{query.replace('.CA','')})")
        st.markdown(f"- [TradingView - {query}](https://www.tradingview.com/symbols/EGX-{query.replace('.CA','')}/)")
        st.markdown(f"- [EGX الرسمي](https://www.egx.com.eg)")
    else:
        sym_clean = msg
        last = float(hist['Close'].iloc[-1])
        prev = float(hist['Close'].iloc[-2])
        chg = ((last-prev)/prev*100) if prev!=0 else 0
        rsi = float(calculate_rsi_wilder(hist['Close']).iloc[-1])
        
        score = 50
        if rsi > 70: score -= 15
        elif rsi < 30: score += 15
        
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("السهم", sym_clean.replace('.CA',''))
        c2.metric("السعر", f"{last:.2f}")
        c3.metric("التغير %", f"{chg:.2f}%")
        c4.metric("عين سكور", f"{score}")
        
        st.info(f"RSI Wilder (14): {rsi:.1f} | المصدر: Yahoo Finance لايف - بدون بيانات وهمية")
        
        # شارت
        fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name=sym_clean)])
        fig.update_layout(template="plotly_dark", height=500, title=f"شارت {sym_clean} - سنة كاملة لايف")
        st.plotly_chart(fig, use_container_width=True)
        
        # جدول آخر 10 أيام
        st.subheader("آخر 10 أيام تداول حقيقية")
        st.dataframe(hist.tail(10)[['Open','High','Low','Close','Volume']].sort_index(ascending=False), use_container_width=True)
        
        st.success(f"تم تحليل {sym_clean} بنجاح - كل البيانات حقيقية من Yahoo بدون تأليف")
else:
    st.info("👆 اكتب أي رمز فوق - مثال: ABUK, ESRS, TMGH, FWRY, COMI, ETEL")
    st.markdown("سيتم جلبه وتحليله فوراً بدون قائمة ثابتة وبدون هلوسة")

# --- قائمة سريعة للتجربة ---
st.markdown("---")
st.caption("جرب هذه الرموز الحقيقية:")
st.code("COMI.CA  ABUK.CA  FWRY.CA  TMGH.CA  ESRS.CA  ETEL.CA  HRHO.CA  EFGH.CA  JUFO.CA  SWDY.CA")
