import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

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
# Session Storage
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
# Display Data & Plot
# -------------------------
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data).sort_values("Time")

    st.subheader("📋 Logged Readings")
    st.dataframe(df, use_container_width=True)

    st.subheader("📈 Glucose Trend (Interactive)")

    fig = go.Figure()

    # Line + markers
    fig.add_trace(go.Scatter(
        x=df["Time"],
        y=df["Glucose"],
        mode="lines+markers",
        name="Glucose",
        hovertemplate="Time: %{x}<br>Glucose: %{y} mg/dL<extra></extra>"
    ))

    # Threshold lines
    fig.add_hline(y=70, line_dash="dash", annotation_text="Hypo Threshold (70)")
    fig.add_hline(y=140, line_dash="dash", annotation_text="Hyper Threshold (140)")

    # Shaded zones
    fig.add_hrect(y0=0, y1=70, fillcolor="blue", opacity=0.08, line_width=0)
    fig.add_hrect(y0=70, y1=140, fillcolor="green", opacity=0.08, line_width=0)
    fig.add_hrect(y0=140, y1=600, fillcolor="red", opacity=0.08, line_width=0)

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Glucose (mg/dL)",
        hovermode="x unified",
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # Latest Reading Summary
    # -------------------------
    latest = df.iloc[-1]

    st.markdown(f"""
    ### 🧠 Latest Reading
    - 🕒 **Time:** {latest['Time']}
    - 🩸 **Glucose:** {latest['Glucose']} mg/dL
    - 📌 **Status:** **{latest['Status']}**
    """)

else:
    st.info("No glucose readings logged yet. Add one above 👆")

