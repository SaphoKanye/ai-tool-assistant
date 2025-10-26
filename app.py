
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="AI Tool Selection Assistant", layout="wide")

# =============================
# App Title & Help
# =============================
st.title("🧭 AI Tool Selection Assistant")
st.caption("Upload an Excel matrix or use the bundled one. Pick Function → Activity → Type, then score and get a recommendation.")

with st.expander("ℹ️ How this works", expanded=False):
    st.markdown(
        "1. **Upload** your Excel (or the app will try to use `AI Tool Matrix.xlsx` in the repo).<br>"
        "2. **Select** a Business Function and Activity.<br>"
        "3. **Choose** an AI Tool Type (impact hint included).<br>"
        "4. **Score** suggested tools (1–5) and get a **recommended pick**.<br>"
        "<br>This app auto-detects common header variations and avoids KeyErrors.",
        unsafe_allow_html=True
    )

# =============================
# Helpers
# =============================
@st.cache_data(show_spinner=False)
def load_excel(path_or_buffer, sheet_index=0):
    """Load an Excel sheet as DataFrame using openpyxl and return a copy."""
    df = pd.read_excel(path_or_buffer, sheet_name=sheet_index, engine="openpyxl")
    return df.copy()

def normalize_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize/rename headers to expected names; keep data intact."""
    df = df.copy()
    # Remove unnamed-placeholder columns, strip spaces
    df = df.loc[:, ~df.columns.astype(str).str.contains(r"^Unnamed", case=False, regex=True)]
    df.columns = df.columns.astype(str).str.strip()

    rename_map = {
        # Business Function
        'business function': 'Business Functions',
        'business functions': 'Business Functions',
        'function': 'Business Functions',
        'dept': 'Business Functions',
        'department': 'Business Functions',
        'function area': 'Business Functions',
        'biz function': 'Business Functions',
        # Activity
        'business function activities': 'Business Function Activities',
        'business activities': 'Business Function Activities',
        'activity': 'Business Function Activities',
        'activities': 'Business Function Activities',
        'process step': 'Business Function Activities',
        'task': 'Business Function Activities',
        # Type
        'ai tool type': 'AI Tool Type',
        'ai tool types': 'AI Tool Type',
        'ai type': 'AI Tool Type',
        'tool type': 'AI Tool Type',
        'ai category': 'AI Tool Type',
        'ai tool category': 'AI Tool Type',
    }
    df.rename(columns={c: rename_map.get(c.lower(), c) for c in df.columns}, inplace=True)

    # Ensure required columns exist (blank if absent)
    for col in ['Business Functions', 'Business Function Activities', 'AI Tool Type']:
        if col not in df.columns:
            df[col] = ""

    return df

def impact_for_type(tool_type: str) -> str:
    mapping = {
        'LLM Assistant': 'High',
        'Image Generation AI': 'High',
        'RPA': 'Medium',
        'Creative/Design AI': 'High'
    }
    return mapping.get(tool_type, 'Unknown')

# Demo catalogue (extend or replace with your own list or a second sheet)
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

# =============================
# Data Source: Upload or bundled file
# =============================
left, right = st.columns([2, 1])
with left:
    uploaded = st.file_uploader("Upload Excel matrix (.xlsx)", type=["xlsx"])

with right:
    use_bundled = st.toggle("Use bundled file", value=not bool(uploaded), help="If ON, the app looks for 'AI Tool Matrix.xlsx' next to app.py.")

df = None
source_label = ""

if uploaded is not None:
    try:
        df = load_excel(uploaded, sheet_index=0)
        source_label = "Uploaded file"
    except Exception as e:
        st.error(f"Failed to read uploaded file: {e}")
elif use_bundled:
    default_path = Path("AI Tool Matrix.xlsx")
    if default_path.exists():
        try:
            df = load_excel(default_path, sheet_index=0)
            source_label = "Bundled file (AI Tool Matrix.xlsx)"
        except Exception as e:
            st.error(f"Failed to read bundled file: {e}")
    else:
        st.info("No file uploaded and bundled file not found. Please upload your Excel.")

if df is not None:
    df = normalize_and_rename_columns(df)

    with st.expander("🔍 Data check (click to open)"):
        st.write(f"Source: **{source_label}**")
        st.write("Detected columns (first 10):", list(df.columns[:10]))
        st.dataframe(df.head(10), use_container_width=True)

# Stop here if we still don't have data
if df is None or df.empty:
    st.stop()

# =============================
# UI Step 1: Select Function & Activity
# =============================
st.header("Step 1 · Select Business Function & Activity")
functions = sorted(pd.Series(df['Business Functions'].dropna().astype(str).unique()))
selected_function = st.selectbox("Business Function", options=functions)

activities = sorted(pd.Series(
    df.loc[df['Business Functions'] == selected_function, 'Business Function Activities']
    .dropna()
    .astype(str)
    .unique()
))
selected_activity = st.selectbox("Activity", options=activities)

# =============================
# UI Step 2: Filter AI Tool Types
# =============================
st.header("Step 2 · Filter AI Tool Types")
mask = (df['Business Functions'] == selected_function) & (df['Business Function Activities'] == selected_activity)
tool_types = pd.Series(df.loc[mask, 'AI Tool Type'].dropna().astype(str).unique()).tolist()

if len(tool_types) == 0:
    st.warning("No AI Tool Types found for that Function/Activity. Please adjust your selections or update your Excel.")
    st.stop()

type_with_impact = [f"{t} (Impact: {impact_for_type(t)})" for t in tool_types]
selected_type_label = st.selectbox("AI Tool Type", options=type_with_impact)
selected_type = selected_type_label.split(" (")[0]

# =============================
# UI Step 3: Preferences
# =============================
st.header("Step 3 · Set Preferences")
pref1, pref2, pref3 = st.columns(3)
with pref1:
    complexity = st.select_slider("Complexity", options=['Low', 'Medium', 'High'], value='Medium')
with pref2:
    scalability = st.select_slider("Scalability", options=['Low', 'Medium', 'High'], value='Medium')
with pref3:
    cost = st.selectbox("Cost Structure", options=['Free', 'Freemium', 'Subscription', 'Enterprise'], index=1)

# =============================
# Step 4: Matching tools (Demo catalogue)
# =============================
st.header("Step 4 · Matching AI Tools")
matches = DEMO_CATALOGUE[(DEMO_CATALOGUE['Type'] == selected_type) &
                         (DEMO_CATALOGUE['Pricing'].str.contains(cost, case=False, na=False))]

if matches.empty:
    st.info("No exact matches on cost filter; showing all tools for the selected type.")
    matches = DEMO_CATALOGUE[DEMO_CATALOGUE['Type'] == selected_type]

st.dataframe(matches[['Tool', 'Features', 'Strengths', 'Limitations', 'Pricing', 'Link']],
             use_container_width=True)

# =============================
# Step 5: Score & Recommendation
# =============================
st.header("Step 5 · Score & Recommend")
if not matches.empty:
    scores = {}
    for _, row in matches.iterrows():
        scores[row['Tool']] = st.slider(f"Score {row['Tool']} (1-5)", 1, 5, 3)
    best_tool = max(scores, key=scores.get) if scores else None

    if best_tool:
        st.success(f"✅ Recommended Tool: **{best_tool}**")
        st.markdown(
            "- Check integration options\n"
            "- Start with a pilot/test\n"
            "- Monitor performance and ROI\n"
            "- Ensure data privacy and compliance\n"
            "- Review vendor support and documentation\n"
        )

# Footer
st.caption("Tip: Keep Excel headers close to 'Business Functions', 'Business Function Activities', 'AI Tool Type' for best results.")
