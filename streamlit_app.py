streamlit
yfinance
pandas
plotly

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="عين V12 - تحليل كامل", layout="wide", page_icon="👁️")
st.title("👁️ عين على البورصة V12 - التحليل الكامل بدون هلوسة")

def calculate_rsi_wilder(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 0.0001)
    return 100 - (100 / (1 + rs))

def calculate_ain_score_full(hist):
    try:
        if len(hist) < 60: return 0, ["بيانات غير كافية"]
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
        
        # 1. RSI (25 نقطة)
        if rsi < 30: score+=15; reasons.append(f"RSI {rsi:.1f} تشبع بيع قوي (+15)")
        elif rsi < 40: score+=8; reasons.append(f"RSI {rsi:.1f} ميل للشراء (+8)")
        elif rsi > 70: score-=15; reasons.append(f"RSI {rsi:.1f} تشبع شراء (-15)")
        elif rsi > 60: score-=8; reasons.append(f"RSI {rsi:.1f} ميل للبيع (-8)")
        else: reasons.append(f"RSI {rsi:.1f} متوازن")
        
        # 2. المتوسطات (25 نقطة)
        if last > sma20 > sma50: score+=10; reasons.append(f"فوق SMA20/50 صاعد (+10)")
        elif last < sma20 < sma50: score-=10; reasons.append(f"تحت SMA20/50 هابط (-10)")
        if last > sma200: score+=5; reasons.append(f"فوق SMA200 اتجاه طويل صاعد (+5)")
        else: score-=5; reasons.append(f"تحت SMA200 اتجاه طويل هابط (-5)")
        
        # 3. الفوليوم (20 نقطة)
        if vol_last > vol_avg*1.5: score+=8; reasons.append(f"فوليوم عالي {vol_last/vol_avg:.1f}x (+8)")
        elif vol_last < vol_avg*0.5: score-=5; reasons.append(f"فوليوم ضعيف (-5)")
        
        # 4. القرب من القمم والقيعان (15 نقطة)
        high_52 = float(high.rolling(60).max().iloc[-1])
        low_52 = float(low.rolling(60).min().iloc[-1])
        dist_high = (high_52 - last)/high_52*100 if high_52>0 else 0
        if dist_high < 5: score-=7; reasons.append(f"قريب من قمة 60 يوم (-7)")
        if last < low_52*1.05: score+=7; reasons.append(f"قريب من قاع 60 يوم (+7)")
        
        # 5. التغير اليومي (15 نقطة)
        prev = float(close.iloc[-2])
        chg = (last-prev)/prev*100
        if chg > 3: score+=7; reasons.append(f"صعود يومي قوي {chg:.1f}% (+7)")
        elif chg < -3: score-=7; reasons.append(f"هبوط يومي قوي {chg:.1f}% (-7)")
        
        score = max(0, min(100, round(score,1)))
        return score, reasons, rsi, sma20, sma50, chg
    except Exception as e:
        return 0, [f"خطأ حسابي: {e}"], 50, 0, 0, 0

@st.cache_data(ttl=600, show_spinner=False)
def get_hist_stable(symbol_raw):
    try:
        sym = symbol_raw.strip().upper()
        if not sym: return None, "اكتب رمز", ""
        if not sym.endswith(".CA"): sym = sym + ".CA"
        ticker = yf.Ticker(sym)
        hist = ticker.history(period="1y", auto_adjust=True)
        if hist is None or hist.empty or len(hist) < 50:
            return None, f"الرمز {sym} غير موجود", sym
        return hist.dropna(), "نجاح", sym
    except Exception as e:
        return None, f"خطأ: {str(e)[:200]}", symbol_raw

query = st.text_input("🔍 ابحث عن أي سهم EGX (COMI, FWRY, ABUK...)", placeholder="COMI")

if query:
    with st.spinner(f"تحليل {query} تحليل كامل..."):
        hist, msg, sym_final = get_hist_stable(query)
    
    if hist is None:
        st.error(msg)
    else:
        try:
            score, reasons, rsi, sma20, sma50, chg = calculate_ain_score_full(hist)
            last = float(hist['Close'].iloc[-1])
            
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("السهم", sym_final.replace('.CA',''))
            c2.metric("السعر", f"{last:.2f}")
            c3.metric("عين سكور V12", f"{score}/100")
            c4.metric("RSI Wilder", f"{rsi:.1f}")
            
            st.divider()
            
            # تفصيل التحليل
            st.subheader("📊 تفصيل عين سكور V12 (بدون هلوسة - كله من الشارت الحقيقي)")
            for r in reasons:
                if "+" in r: st.success(r)
                elif "-" in r: st.error(r)
                else: st.info(r)
            
            st.divider()
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="السعر"))
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'].rolling(20).mean(), name="SMA20", line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'].rolling(50).mean(), name="SMA50", line=dict(color='blue')))
            fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, title=f"{sym_final} + SMA20/50 - بيانات حية")
            st.plotly_chart(fig, use_container_width=True)
            
            st.bar_chart(hist['Volume'].tail(60))
            st.caption("الفوليوم 60 يوم - حقيقي من Yahoo")
            
        except Exception as e:
            st.error(f"خطأ: {e}")
else:
    st.info("اكتب أي رمز فوق - سيتم تحليله بـ 5 عوامل حقيقية من الشارت")

