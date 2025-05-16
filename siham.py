import streamlit as st
import pandas as pd
import plotly.express as px

# إعداد الصفحة
st.set_page_config(page_title="📊 تتبع السيولة", layout="wide")

# ضبط اتجاه النصوص
st.markdown("""
    <style>
    * {
        direction: rtl;
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

# ========== تحميل البيانات ==========
st.title("📊 نظام تتبع السيولة في الوقت الحقيقي")

try:
    data = pd.read_csv("liquidite_banque_maroc_2023_2025.csv")
    data["تاريخ"] = pd.to_datetime(data["تاريخ"])
    data = data.sort_values(by=["فرع", "تاريخ"])
except Exception as e:
    st.error(f"فشل في تحميل البيانات: {e}")
    st.stop()

# ========== إدخال المستخدم ==========
st.subheader("⚙️ إعدادات التحليل")

min_date = data["تاريخ"].min().date()
max_date = data["تاريخ"].max().date()

start_date = st.date_input("📌 تاريخ البداية", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.date_input("📌 تاريخ النهاية", value=max_date, min_value=min_date, max_value=max_date)

threshold = st.number_input("🔢 حد السيولة الأدنى للتنبيه", min_value=10000, max_value=200000, value=80000, step=5000)
branches = data["فرع"].unique()
selected_branch = st.selectbox("اختر الفرع", ["الكل"] + list(branches))

# ========== زر التحليل ==========
if st.button("🔍 تحليل البيانات"):

    # التحقق من التواريخ
    if start_date > end_date:
        st.error("❌ تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")
        st.stop()

    # تصفية البيانات
    filtered = data[(data["تاريخ"].dt.date >= start_date) & (data["تاريخ"].dt.date <= end_date)]

    if selected_branch != "الكل":
        filtered = filtered[filtered["فرع"] == selected_branch]

    if filtered.empty:
        st.warning("⚠️ لا توجد بيانات متوفرة ضمن هذا النطاق الزمني.")
        st.stop()

    # تحليل الفرع
    st.markdown("### 🧾 تحليل البيانات:")
    st.write(f"📅 عدد الأيام: {filtered['تاريخ'].nunique()}")
    st.write(f"🏢 عدد الفروع: {filtered['فرع'].nunique()}")
    st.write(f"💰 متوسط الرصيد: {int(filtered['الرصيد'].mean())} درهم")

    if selected_branch != "الكل":
        st.write(f"📉 أدنى رصيد: {filtered['الرصيد'].min()} درهم")
        st.write(f"📈 أعلى رصيد: {filtered['الرصيد'].max()} درهم")
        st.write(f"📊 الانحراف المعياري: {round(filtered['الرصيد'].std(), 2)}")

    # حساب المعدل المتحرك والتغير
    filtered["المعدل_المتحرك"] = filtered.groupby("فرع")["الرصيد"].transform(lambda x: x.rolling(window=3).mean())
    filtered["نسبة_التغير_%"] = filtered.groupby("فرع")["الرصيد"].pct_change() * 100

    # تنبيه السيولة
    low_liquidity = filtered[filtered["الرصيد"] < threshold]
    st.subheader("⚠️ مراقبة السيولة المنخفضة")
    if not low_liquidity.empty:
        st.warning("🚨 يوجد نقص في السيولة!")
        st.write(f"📍 عدد التنبيهات: {len(low_liquidity)}")
        st.dataframe(low_liquidity.sort_values("الرصيد"))
    else:
        st.success("✅ لا توجد مشاكل حالياً في السيولة.")

    # عرض البيانات
    st.subheader("📅 البيانات اليومية")
    st.dataframe(filtered.sort_values("تاريخ", ascending=False))

    # الرسم البياني الرئيسي
    st.subheader("📈 تطور السيولة والمعدل المتحرك")
    fig = px.line(filtered, x="تاريخ", y=["الرصيد", "المعدل_المتحرك"], color="فرع",
                  labels={"value": "القيمة", "variable": "المؤشر"},
                  title="الرصيد مقابل المعدل المتحرك")
    st.plotly_chart(fig, use_container_width=True)

    # تحليل المنحنى
    st.markdown("###  تحليل المنحنى:")
    last_days = filtered.sort_values("تاريخ").tail(5)
    avg_trend = last_days["الرصيد"].diff().mean()
    ma_trend = last_days["المعدل_المتحرك"].diff().mean()

    if avg_trend > 0 and ma_trend > 0:
        st.success("📈 السيولة في اتجاه تصاعدي مستقر.")
    elif avg_trend < 0 and ma_trend < 0:
        st.warning("📉 انخفاض مستمر في السيولة.")
    else:
        st.info("⚖️ السيولة تعرف تقلبات في الأيام الأخيرة.")

    # رسم التغير اليومي
    st.subheader("📉 نسبة التغير اليومية في السيولة (%)")
    fig2 = px.bar(filtered, x="تاريخ", y="نسبة_التغير_%", color="فرع",
                  title="تغير السيولة اليومي")
    st.plotly_chart(fig2, use_container_width=True)

    # تحليل التغير
    st.markdown("###  تحليل التغيرات اليومية:")
    volatility = filtered["نسبة_التغير_%"].std()
    avg_change = filtered["نسبة_التغير_%"].mean()
    st.write(f"📊 متوسط التغير: {round(avg_change, 2)}%")
    st.write(f"📉 التقلب: {round(volatility, 2)}%")

    if volatility > 15:
        st.warning("⚠️ تغيرات كبيرة تشير إلى عدم استقرار.")
    elif volatility > 5:
        st.info("📉 تقلبات متوسطة.")
    else:
        st.success("✅ استقرار جيد في السيولة.")
