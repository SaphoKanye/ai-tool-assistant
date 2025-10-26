
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="AI Tool Selection Assistant", layout="wide")
st.title("🧭 AI Tool Selection Assistant (Auto‑detect sheets)")
st.caption("Uploads or bundled Excel are scanned across ALL sheets; the first sheet with the required headers is used.")

REQUIRED = ['Business Functions', 'Business Function Activities', 'AI Tool Type']

def normalize_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.loc[:, ~df.columns.astype(str).str.contains(r"^Unnamed", case=False, regex=True)]
    df.columns = df.columns.astype(str).str.strip()

    rename_map = {
        'business function': 'Business Functions',
        'business functions': 'Business Functions',
        'function': 'Business Functions',
        'dept': 'Business Functions',
        'department': 'Business Functions',
        'function area': 'Business Functions',
        'biz function': 'Business Functions',
        'business function activities': 'Business Function Activities',
        'business activities': 'Business Function Activities',
        'activity': 'Business Function Activities',
        'activities': 'Business Function Activities',
        'process step': 'Business Function Activities',
        'task': 'Business Function Activities',
        'ai tool type': 'AI Tool Type',
        'ai tool types': 'AI Tool Type',
        'ai type': 'AI Tool Type',
        'tool type': 'AI Tool Type',
        'ai category': 'AI Tool Type',
        'ai tool category': 'AI Tool Type',
    }
    df.rename(columns={c: rename_map.get(c.lower(), c) for c in df.columns}, inplace=True)
    return df

@st.cache_data(show_spinner=False)
def load_matching_sheet(path_or_buffer):
    """Return (df, sheet_name, reason) for the first sheet that contains required columns after normalization."""
    try:
        all_sheets = pd.read_excel(path_or_buffer, sheet_name=None, engine="openpyxl")
    except Exception as e:
        return None, None, f"Failed to read Excel: {e}"
    for name, raw in all_sheets.items():
        df = normalize_and_rename_columns(raw)
        cols = set(df.columns)
        if all(col in cols for col in REQUIRED):
            # Ensure required columns exist as strings
            for c in REQUIRED:
                df[c] = df[c].astype(str)
            return df, name, "ok"
    # none matched, return first sheet (normalized) with reason
    first_name, first_df = next(iter(all_sheets.items()))
    return normalize_and_rename_columns(first_df), first_name, "missing_required_columns"

def impact_for_type(t):
    return {'LLM Assistant':'High','Image Generation AI':'High','RPA':'Medium','Creative/Design AI':'High'}.get(t,'Unknown')

# --- Inputs
left, right = st.columns([2,1])
with left:
    uploaded = st.file_uploader("Upload Excel matrix (.xlsx)", type=["xlsx"])
with right:
    use_bundled = st.toggle("Use bundled file", value=not bool(uploaded), help="If ON, reads 'AI Tool Matrix.xlsx' from repo.")

df = None; src = ""; sheet_used = ""; status = ""

if uploaded is not None:
    df, sheet_used, status = load_matching_sheet(uploaded)
    src = "Uploaded file"
elif use_bundled:
    p = Path("AI Tool Matrix.xlsx")
    if p.exists():
        df, sheet_used, status = load_matching_sheet(p)
        src = "Bundled file (AI Tool Matrix.xlsx)"
    else:
        st.info("No file uploaded and bundled file not found. Please upload your Excel.")
        st.stop()

with st.expander("🔍 Data check (click to open)"):
    st.write(f"Source: **{src}** | Sheet: **{sheet_used}** | Status: **{status}**")
    if df is not None:
        st.write("Detected columns:", list(df.columns))
        st.dataframe(df.head(10), use_container_width=True)

if df is None or df.empty:
    st.stop()

if status == "missing_required_columns":
    st.error(f"Couldn't find all required columns {REQUIRED} in any sheet. "
             "Please rename your headers or upload the fixed template.")
    st.stop()

# --- UI
st.header("Step 1 · Select Business Function & Activity")
functions = sorted(pd.Series(df['Business Functions'].dropna().astype(str).unique()))
selected_function = st.selectbox("Business Function", options=functions)

activities = sorted(pd.Series(
    df.loc[df['Business Functions'] == selected_function, 'Business Function Activities']
    .dropna().astype(str).unique()
))
selected_activity = st.selectbox("Activity", options=activities)

st.header("Step 2 · Filter AI Tool Types")
mask = (df['Business Functions'] == selected_function) & (df['Business Function Activities'] == selected_activity)
tool_types = pd.Series(df.loc[mask, 'AI Tool Type'].dropna().astype(str).unique()).tolist()
if not tool_types:
    st.warning("No AI Tool Types for that selection. Try another Activity or update Excel.")
    st.stop()
label_types = [f"{t} (Impact: {impact_for_type(t)})" for t in tool_types]
selected_type_label = st.selectbox("AI Tool Type", options=label_types)
selected_type = selected_type_label.split(" (")[0]

# Demo catalogue (kept inline; replace with your sheet if you have one)
DEMO_CATALOGUE = pd.DataFrame({
    'Tool': ['ChatGPT', 'MidJourney', 'UiPath', 'Figma AI', 'Canva AI'],
    'Type': ['LLM Assistant', 'Image Generation AI', 'RPA', 'Creative/Design AI', 'Creative/Design AI'],
    'Features': ['Chatbot, content gen', 'Image gen', 'Automation', 'Design, prototyping', 'Graphic design'],
    'Strengths': ['Versatile', 'High quality', 'Scalable', 'User-friendly', 'Easy to use'],
    'Limitations': ['No real-time data', 'Subscription', 'Complex setup', 'Limited advanced features', 'Less technical'],
    'Pricing': ['Freemium', 'Subscription', 'Enterprise', 'Freemium', 'Freemium'],
    'Link': [
        'https://chatgpt.com/', 'https://www.midjourney.com/', 'https://www.uipath.com/',
        'https://www.figma.com/ai/', 'https://www.canva.com/ai/'
    ]
})

st.header("Step 3 · Set Preferences")
c1,c2,c3 = st.columns(3)
with c1: complexity = st.select_slider("Complexity", ['Low','Medium','High'], value='Medium')
with c2: scalability = st.select_slider("Scalability", ['Low','Medium','High'], value='Medium')
with c3: cost = st.selectbox("Cost Structure", ['Free','Freemium','Subscription','Enterprise'], index=1)

st.header("Step 4 · Matching AI Tools")
matches = DEMO_CATALOGUE[(DEMO_CATALOGUE['Type'] == selected_type) &
                         (DEMO_CATALOGUE['Pricing'].str.contains(cost, case=False, na=False))]
if matches.empty:
    st.info("No exact matches on cost; showing all tools for this type.")
    matches = DEMO_CATALOGUE[DEMO_CATALOGUE['Type'] == selected_type]
st.dataframe(matches[['Tool','Features','Strengths','Limitations','Pricing','Link']], use_container_width=True)

st.header("Step 5 · Score & Recommend")
if not matches.empty:
    scores = {}
    for _, row in matches.iterrows():
        scores[row['Tool']] = st.slider(f"Score {row['Tool']} (1-5)", 1, 5, 3)
    if scores:
        best = max(scores, key=scores.get)
        st.success(f"✅ Recommended Tool: **{best}**")
        st.markdown("- Check integration options\n- Start with a pilot/test\n- Monitor performance and ROI\n- Ensure data privacy and compliance\n- Review vendor support and documentation")

st.caption("Auto-detects sheets and normalizes headers. Required columns: 'Business Functions', 'Business Function Activities', 'AI Tool Type'.")
