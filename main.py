import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import plotly.graph_objects as go
import pytz

# ================= TIMEZONE =================
IST = pytz.timezone("Asia/Kolkata")
UTC = pytz.utc

def ist_now():
    return datetime.now(IST)

def ist_datetime_from_time(t):
    today = ist_now().date()
    ist_dt = IST.localize(datetime.combine(today, t))
    return ist_dt

def utc_to_ist(dt):
    return dt.astimezone(IST)

# ================= CONFIG =================
st.set_page_config(page_title="Glucose Tracker", layout="centered")
st.title("🩸 Glucose Tracker")

MONGO_URI = st.secrets["mongo"]["uri"]
client = MongoClient(MONGO_URI)
db = client["health"]
glucose_col = db.glucose_logs

# ================= CLASSIFICATION =================
def classify_glucose(value):
    if value < 70:
        return "Hypoglycemia"
    elif value <= 140:
        return "Normal"
    else:
        return "Hyperglycemia"

# ================= INPUT =================
with st.form("glucose_form"):
    glucose = st.number_input(
        "Glucose Level (mg/dL)",
        min_value=20,
        max_value=600,
        step=1
    )

    log_time = st.time_input(
        "Time (optional – defaults to current IST)",
        value=None
    )

    submit = st.form_submit_button("➕ Add Reading")

    if submit:
        ist_timestamp = (
            ist_datetime_from_time(log_time)
            if log_time else ist_now()
        )

        glucose_col.insert_one({
            "glucose": glucose,
            "status": classify_glucose(glucose),
            "time_utc": ist_timestamp.astimezone(UTC)
        })

        st.success(
            f"Logged {glucose} mg/dL at "
            f"{ist_timestamp.strftime('%d %b %Y %I:%M %p IST')}"
        )

# ================= FETCH DATA =================
data = list(glucose_col.find({}, {"_id": 0}))

if not data:
    st.info("No glucose readings yet. Add one above 👆")
    st.stop()

df = pd.DataFrame(data)
df["time"] = df["time_utc"].apply(utc_to_ist)
df = df.sort_values("time")

# ================= TABLE =================
st.subheader("📋 Glucose History")
st.dataframe(
    df[["time", "glucose", "status"]],
    use_container_width=True
)

# ================= PLOTLY GRAPH =================
st.subheader("📈 Glucose Trend (IST)")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["time"],
    y=df["glucose"],
    mode="lines+markers",
    name="Glucose",
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

# ================= LATEST READING =================
latest = df.iloc[-1]

st.markdown(f"""
### 🧠 Latest Reading
- 🕒 **Time:** {latest['time'].strftime('%d %b %Y %I:%M %p IST')}
- 🩸 **Glucose:** {latest['glucose']} mg/dL
- 📌 **Status:** **{latest['status']}**
""")
