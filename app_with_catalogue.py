
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="AI Tool Selection Assistant", layout="wide")
st.title("🧭 AI Tool Selection Assistant (Matrix + Catalogue)")
st.caption("Reads 'Matrix' for Function/Activity/Type and 'Catalogue' for tools. Upload an Excel or use bundled one.")

REQ_MATRIX = ['Business Functions', 'Business Function Activities', 'AI Tool Type']
REQ_CATALOGUE_MIN = ['Tool', 'Type']  # other columns are optional

def norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.loc[:, ~df.columns.astype(str).str.contains(r"^Unnamed", case=False, regex=True)]
    df.columns = df.columns.astype(str).str.strip()
    return df

def load_workbook(path_or_file):
    try:
        return pd.read_excel(path_or_file, sheet_name=None, engine="openpyxl")
    except Exception as e:
        st.error(f"Failed to read Excel: {e}")
        return None

def find_matrix_sheet(sheets: dict):
    # Prefer explicit 'Matrix' sheet; otherwise auto-detect
    if 'Matrix' in sheets:
        df = norm_cols(sheets['Matrix'])
        if all(c in df.columns for c in REQ_MATRIX):
            return df, 'Matrix', 'ok'
    # auto-detect across all sheets
    for name, raw in sheets.items():
        df = norm_cols(raw)
        # try light aliasing
        aliases = {
            'business function': 'Business Functions',
            'business functions': 'Business Functions',
            'business function activities': 'Business Function Activities',
            'business activities': 'Business Function Activities',
            'activity': 'Business Function Activities',
            'ai tool type': 'AI Tool Type',
            'ai tool types': 'AI Tool Type',
            'tool type': 'AI Tool Type'
        }
        df = df.rename(columns={c: aliases.get(c.strip().lower(), c) for c in df.columns})
        if all(c in df.columns for c in REQ_MATRIX):
            return df[REQ_MATRIX].copy(), name, 'ok'
    return None, None, 'missing_required_columns'

def find_catalogue_sheet(sheets: dict):
    # Prefer explicit 'Catalogue' sheet; otherwise look for minimal columns
    preferred_names = ['Catalogue', 'Catalog', 'Tools', 'Tool Catalogue']
    for n in preferred_names:
        if n in sheets:
            df = norm_cols(sheets[n])
            return df, n
    # scan any sheet that has Tool + Type
    for name, raw in sheets.items():
        df = norm_cols(raw)
        if 'Tool' in df.columns and 'Type' in df.columns:
            return df, name
    return None, None

# --------- Inputs
left, right = st.columns([2,1])
with left:
    uploaded = st.file_uploader("Upload Excel (.xlsx) containing 'Matrix' and optionally 'Catalogue'", type=['xlsx'])
with right:
    use_bundled = st.toggle("Use bundled file", value=not bool(uploaded))

sheets = None; source = ""
if uploaded is not None:
    sheets = load_workbook(uploaded); source = "Uploaded file"
elif use_bundled:
    p = Path("AI Tool Matrix.xlsx")
    if p.exists():
        sheets = load_workbook(p); source = "Bundled file (AI Tool Matrix.xlsx)"
    else:
        st.info("No file uploaded and bundled file not found. Please upload your Excel.")
        st.stop()

if sheets is None:
    st.stop()

# --------- Load Matrix
matrix_df, matrix_sheet, matrix_status = find_matrix_sheet(sheets)

with st.expander("🔎 Data check: Matrix"):
    st.write(f"Source: **{source}**")
    st.write(f"Matrix sheet used: **{matrix_sheet}** | Status: **{matrix_status}**")
    if matrix_df is not None:
        st.write("Matrix columns:", list(matrix_df.columns))
        st.dataframe(matrix_df.head(10), use_container_width=True)

if matrix_df is None or matrix_status != 'ok':
    st.error(f"Couldn't find a valid Matrix sheet with columns {REQ_MATRIX}. Please upload the cleaned file.")
    st.stop()

# --------- Load Catalogue
catalogue_df, catalogue_sheet = find_catalogue_sheet(sheets)
if catalogue_df is not None:
    catalogue_df = norm_cols(catalogue_df)
    # keep only known columns; create missing optional ones
    desired_cols = ['Tool','Type','Features','Strengths','Limitations','Pricing','Link']
    for c in desired_cols:
        if c not in catalogue_df.columns:
            catalogue_df[c] = ""
    catalogue_df = catalogue_df[desired_cols]
    with st.expander("📚 Data check: Catalogue"):
        st.write(f"Catalogue sheet used: **{catalogue_sheet}**")
        st.dataframe(catalogue_df.head(10), use_container_width=True)
else:
    st.warning("No Catalogue sheet found. Using a built-in demo list.")
    catalogue_df = pd.DataFrame({
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

def impact_for_type(t):
    return {'LLM Assistant':'High','Image Generation AI':'High','RPA':'Medium','Creative/Design AI':'High'}.get(str(t),'Unknown')

# --------- UI Step 1
st.header("Step 1 · Select Business Function & Activity")
functions = sorted(pd.Series(matrix_df['Business Functions'].dropna().astype(str).unique()))
selected_function = st.selectbox("Business Function", options=functions)

activities = sorted(pd.Series(
    matrix_df.loc[matrix_df['Business Functions'] == selected_function, 'Business Function Activities']
    .dropna().astype(str).unique()
))
selected_activity = st.selectbox("Activity", options=activities)

# --------- UI Step 2
st.header("Step 2 · Filter AI Tool Types")
mask = (matrix_df['Business Functions'] == selected_function) & (matrix_df['Business Function Activities'] == selected_activity)
tool_types = pd.Series(matrix_df.loc[mask, 'AI Tool Type'].dropna().astype(str).unique()).tolist()
if not tool_types:
    st.warning("No AI Tool Types for that selection. Please adjust your Excel or pick another Activity.")
    st.stop()
labels = [f"{t} (Impact: {impact_for_type(t)})" for t in tool_types]
selected_type_label = st.selectbox("AI Tool Type", options=labels)
selected_type = selected_type_label.split(" (")[0]

# --------- Step 3
st.header("Step 3 · Set Preferences")
c1,c2,c3 = st.columns(3)
with c1: complexity = st.select_slider("Complexity", ['Low','Medium','High'], value='Medium')
with c2: scalability = st.select_slider("Scalability", ['Low','Medium','High'], value='Medium')
with c3: cost = st.selectbox("Cost Structure", ['Free','Freemium','Subscription','Enterprise'], index=1)

# --------- Step 4 (use Catalogue)
st.header("Step 4 · Matching AI Tools (from Catalogue)")
matches = catalogue_df[(catalogue_df['Type'].astype(str) == selected_type) &
                       (catalogue_df['Pricing'].astype(str).str.contains(cost, case=False, na=False))]
if matches.empty:
    st.info("No exact matches on cost; showing all tools for the selected type.")
    matches = catalogue_df[catalogue_df['Type'].astype(str) == selected_type]

st.dataframe(matches[['Tool','Features','Strengths','Limitations','Pricing','Link']], use_container_width=True)

# --------- Step 5
st.header("Step 5 · Score & Recommend")
if not matches.empty:
    scores = {}
    for _, row in matches.iterrows():
        scores[row['Tool']] = st.slider(f"Score {row['Tool']} (1-5)", 1, 5, 3)
    if scores:
        best = max(scores, key=scores.get)
        st.success(f"✅ Recommended Tool: **{best}**")
        st.markdown("- Check integration options\n- Start with a pilot/test\n- Monitor performance and ROI\n- Ensure data privacy and compliance\n- Review vendor support and documentation")

st.caption("Template requires sheets: 'Matrix' (Business Functions | Business Function Activities | AI Tool Type) and optional 'Catalogue' (Tool | Type | Features | Strengths | Limitations | Pricing | Link).")
