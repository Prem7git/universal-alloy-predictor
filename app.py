import streamlit as st
import pandas as pd
import math

# -------------------------
# Base data
# -------------------------
BASE_HV = {
    "Fe": 120, "Al": 70, "Cu": 80, "Ti": 100, "Ni": 100, "Co": 110, "Mg": 60, "Zn": 70
}

ELEMENT_FACTOR = {
    "C": 180.0, "Cr": 6.0, "Ni": 5.0, "Mo": 9.0, "Mn": 3.0, "Si": 2.0,
    "V": 12.0, "Ti": 8.0, "Al": 3.0, "Cu": 3.0, "Nb": 14.0, "W": 10.0,
    "Co": 6.0, "Zn": 1.0, "Sn": 1.0, "Pb": -5.0, "S": -10.0, "P": -8.0,
    "B": 60.0, "N": 40.0, "O": -20.0, "SiO2": -5.0
}
DEFAULT_ELEM_FACTOR = 2.0

HT_HV_MULT = {
    "Annealing": 0.8, "Normalizing": 1.0, "Hardening": 1.2,
    "Tempering": 1.05, "Age hardening": 1.25, "Carburizing": 1.2,
    "Nitriding": 1.3, "Cyaniding": 1.25, "Stress relieving": 0.98,
    "Quenching": 1.35
}

HT_YS_FRAC = {
    "Annealing": 0.55, "Normalizing": 0.65, "Hardening": 0.78,
    "Tempering": 0.72, "Age hardening": 0.85, "Carburizing": 0.80,
    "Nitriding": 0.90, "Cyaniding": 0.85, "Stress relieving": 0.75,
    "Quenching": 0.82
}

HV_TO_UTS = 3.45

# -------------------------
# Core logic
# -------------------------
def estimate_hv(matrix, composition, heat_treatment):
    base = BASE_HV.get(matrix, 100)
    ht = HT_HV_MULT.get(heat_treatment, 1.0)
    C = composition.get("C", 0.0)
    if matrix == "Fe":
        if C <= 0.2:
            c_contrib = 120.0 * (C / 0.2)
        else:
            c_contrib = 120.0 + 400.0 * (C - 0.2)
    else:
        c_contrib = 40.0 * C
    contrib = sum(ELEMENT_FACTOR.get(el, DEFAULT_ELEM_FACTOR) * pct
                  for el, pct in composition.items() if el != "C")
    hv = (base + c_contrib + contrib) * ht
    return max(20.0, min(round(hv, 1), 1200.0))

def hv_to_uts(hv): return hv * HV_TO_UTS
def uts_to_ys(uts, ht): return uts * HT_YS_FRAC.get(ht, 0.8)

# -------------------------
# Streamlit app
# -------------------------
st.set_page_config(page_title="Universal Alloy Strength Predictor", layout="centered")

st.title("🧪 Universal Alloy Strength Predictor")
st.write("Estimate hardness (HV), UTS, and YS for arbitrary alloy systems using heuristic models.")

tab1, tab2 = st.tabs(["🔹 Single Alloy", "📂 Batch CSV Upload"])

# --- Single alloy input ---
with tab1:
    matrix = st.selectbox("Matrix (base metal)", list(BASE_HV.keys()))
    heat = st.selectbox("Heat Treatment", list(HT_HV_MULT.keys()))
    st.write("### Alloying Elements (%)")
    n = st.number_input("Number of alloying elements", 0, 10, 3)
    comp = {}
    for i in range(int(n)):
        col1, col2 = st.columns(2)
        with col1:
            el = st.text_input(f"Element #{i+1}", key=f"el{i}")
        with col2:
            pct = st.number_input(f"{el} wt%", 0.0, 100.0, 0.0, key=f"pct{i}")
        if el:
            comp[el] = pct

    if st.button("Predict"):
        hv = estimate_hv(matrix, comp, heat)
        uts = hv_to_uts(hv)
        ys = uts_to_ys(uts, heat)
        st.success(f"**Estimated Hardness (HV):** {hv}")
        st.info(f"**Ultimate Tensile Strength (MPa):** {uts:.1f}")
        st.info(f"**Yield Strength (MPa):** {ys:.1f}")

# --- Batch mode ---
with tab2:
    uploaded = st.file_uploader("Upload CSV (columns: matrix, heat, C, Cr, Ni, etc.)", type="csv")
    if uploaded:
        df = pd.read_csv(uploaded)
        st.write("Input Data:", df.head())
        results = []
        for _, row in df.iterrows():
            matrix = row.get("matrix", "Fe")
            heat = row.get("heat", "Normalizing")
            comp = {k: float(v) for k, v in row.items() if k not in ["matrix", "heat"] and not pd.isna(v)}
            hv = estimate_hv(matrix, comp, heat)
            uts = hv_to_uts(hv)
            ys = uts_to_ys(uts, heat)
            results.append({"Estimated_HV": hv, "UTS_MPa": uts, "YS_MPa": ys})
        out = pd.concat([df, pd.DataFrame(results)], axis=1)
        st.write("Predictions:", out)
        csv = out.to_csv(index=False).encode('utf-8')
        st.download_button("Download Results CSV", csv, "predictions.csv", "text/csv")

st.caption("⚠️ Heuristic estimates only — use for screening or baseline comparison.")
