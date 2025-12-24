import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import plotly.graph_objects as go
import pytz

# ================= CONFIG =================
st.set_page_config(page_title="Glucose Tracker", layout="centered")
st.title("🩸 Glucose Tracker")

IST = pytz.timezone("Asia/Kolkata")
UTC = pytz.utc

# ================= DB =================
MONGO_URI = st.secrets["mongo"]
client = MongoClient(MONGO_URI)
db = client["glucose_db"]
col = db.glucose_logs

# ================= HELPERS =================
def classify_glucose(v):
    if v < 70:
        return "Hypoglycemia"
    elif v <= 140:
        return "Normal"
    else:
        return "Hyperglycemia"

# ================= INPUT =================
with st.form("glucose_form"):
    glucose = st.number_input(
        "Glucose (mg/dL)",
        min_value=20,
        max_value=600,
        step=1
    )

    log_date = st.date_input("Date (IST)")
    log_time = st.time_input("Time (IST)")

    submit = st.form_submit_button("➕ Add Reading")

    if submit:
        # USER MUST PROVIDE TIMESTAMP (NO DEFAULTS)
        ist_dt = IST.localize(datetime.combine(log_date, log_time))
        utc_dt = ist_dt.astimezone(UTC)

        col.insert_one({
            "glucose": glucose,
            "status": classify_glucose(glucose),
            "time_utc": utc_dt
        })

        st.success(
            f"Logged {glucose} mg/dL at "
            f"{ist_dt.strftime('%d %b %Y %I:%M %p IST')}"
        )

# ================= FETCH =================
data = list(col.find({}, {"_id": 0}))

if not data:
    st.info("No glucose readings yet.")
    st.stop()

df = pd.DataFrame(data)

# 🔑 CRITICAL LINE (FIXES YOUR ERROR)
df["time"] = pd.to_datetime(df["time_utc"], utc=True)\
                .dt.tz_convert("Asia/Kolkata")

df = df.sort_values("time")

# ================= TABLE =================
st.subheader("📋 Glucose History")
st.dataframe(
    df[["time", "glucose", "status"]],
    use_container_width=True
)

# ================= GRAPH =================
st.subheader("📈 Glucose Trend (IST)")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["time"],
    y=df["glucose"],
    mode="lines+markers",
    hovertemplate="Time: %{x}<br>Glucose: %{y} mg/dL<extra></extra>"
))

# Thresholds
fig.add_hline(y=70, line_dash="dash", annotation_text="Hypo (70)")
fig.add_hline(y=140, line_dash="dash", annotation_text="Hyper (140)")

# Zones
fig.add_hrect(y0=0, y1=70, fillcolor="blue", opacity=0.08)
fig.add_hrect(y0=70, y1=140, fillcolor="green", opacity=0.08)
fig.add_hrect(y0=140, y1=600, fillcolor="red", opacity=0.08)

fig.update_layout(
    xaxis_title="Time (IST)",
    yaxis_title="Glucose (mg/dL)",
    hovermode="x unified",
    height=450
)

st.plotly_chart(fig, use_container_width=True)

# ================= LATEST =================
latest = df.iloc[-1]

st.markdown(f"""
### 🧠 Latest Reading
- 🕒 **Time:** {latest['time'].strftime('%d %b %Y %I:%M %p IST')}
- 🩸 **Glucose:** {latest['glucose']} mg/dL
- 📌 **Status:** **{latest['status']}**
""")
