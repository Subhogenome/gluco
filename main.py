import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from pymongo import MongoClient
import os

st.set_page_config(page_title="Glucose Logger", layout="centered")
st.title("🩸 Glucose Level Logger (MongoDB)")

# -------------------------
# MongoDB Connection
# -------------------------
MONGO_URI = st.secrets["MONGO_URI"]

client = MongoClient(MONGO_URI)
db = client["glucose_db"]
collection = db["readings"]

# -------------------------
# Helper
# -------------------------
def classify_glucose(value):
    if value < 70:
        return "Hypoglycemia"
    elif value <= 140:
        return "Normal"
    else:
        return "Hyperglycemia"

# -------------------------
# Input Form
# -------------------------
with st.form("glucose_form"):
    glucose = st.number_input("Glucose Level (mg/dL)", 20, 600)
    log_time = st.time_input("Time (optional)", value=None)
    submit = st.form_submit_button("➕ Log Reading")

    if submit:
        timestamp = (
            datetime.combine(datetime.today(), log_time)
            if log_time else datetime.now()
        )

        collection.insert_one({
            "time": timestamp,
            "glucose": glucose,
            "status": classify_glucose(glucose)
        })

        st.success("Reading saved to database")

# -------------------------
# Fetch & Plot
# -------------------------
data = list(collection.find({}, {"_id": 0}))
if data:
    df = pd.DataFrame(data).sort_values("time")

    st.subheader("📋 Stored Readings")
    st.dataframe(df, use_container_width=True)

    st.subheader("📈 Glucose Trend")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["glucose"],
        mode="lines+markers",
        name="Glucose"
    ))

    fig.add_hline(y=70, line_dash="dash", annotation_text="Hypo (70)")
    fig.add_hline(y=140, line_dash="dash", annotation_text="Hyper (140)")

    fig.add_hrect(y0=0, y1=70, fillcolor="blue", opacity=0.08)
    fig.add_hrect(y0=70, y1=140, fillcolor="green", opacity=0.08)
    fig.add_hrect(y0=140, y1=600, fillcolor="red", opacity=0.08)

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Glucose (mg/dL)",
        hovermode="x unified",
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No readings found in database.")
