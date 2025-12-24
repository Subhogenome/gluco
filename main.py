import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Glucose Logger", layout="centered")
st.title("🩸 Glucose Level Logger")

# -------------------------
# Helper: Classification
# -------------------------
def classify_glucose(value):
    if value < 70:
        return "Hypoglycemia"
    elif value <= 140:
        return "Normal"
    else:
        return "Hyperglycemia"

# -------------------------
# Session State
# -------------------------
if "data" not in st.session_state:
    st.session_state.data = []

# -------------------------
# Input Form
# -------------------------
with st.form("glucose_form"):
    glucose = st.number_input(
        "Glucose Level (mg/dL)",
        min_value=20,
        max_value=600,
        step=1
    )

    log_time = st.time_input("Time (optional)", value=None)
    submit = st.form_submit_button("➕ Log Reading")

    if submit:
        timestamp = (
            datetime.combine(datetime.today(), log_time)
            if log_time else datetime.now()
        )

        st.session_state.data.append({
            "Time": timestamp,
            "Glucose": glucose,
            "Status": classify_glucose(glucose)
        })

        st.success(f"Logged {glucose} mg/dL")

# -------------------------
# Show Data & Graph
# -------------------------
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data).sort_values("Time")

    st.subheader("📋 Logged Readings")
    st.dataframe(df, use_container_width=True)

    # -------------------------
    # Graph
    # -------------------------
    st.subheader("📈 Glucose Trend")

    fig, ax = plt.subplots(figsize=(8, 4))

    ax.plot(
        df["Time"],
        df["Glucose"],
        marker="o",
        linewidth=2
    )

    # Threshold lines
    ax.axhline(70, linestyle="--")
    ax.axhline(140, linestyle="--")

    # Shaded zones
    ax.fill_between(df["Time"], 0, 70, alpha=0.15)
    ax.fill_between(df["Time"], 70, 140, alpha=0.15)
    ax.fill_between(df["Time"], 140, 600, alpha=0.15)

    ax.set_ylabel("Glucose (mg/dL)")
    ax.set_xlabel("Time")
    ax.set_title("Blood Glucose Over Time")

    st.pyplot(fig)

    # -------------------------
    # Latest Status
    # -------------------------
    latest = df.iloc[-1]
    st.markdown(f"""
    **Latest Reading:**  
    🕒 {latest['Time']}  
    🩸 {latest['Glucose']} mg/dL  
    📌 **Status:** {latest['Status']}
    """)

else:
    st.info("No glucose readings yet. Add one above 👆")
