
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="AI Tool Selection Assistant", layout="wide")
st.title("AI Tool Selection Assistant (Improved & Robust)")

# -------- Helpers
def norm(s: str) -> str:
    return "".join(ch for ch in s.lower().strip() if ch.isalnum())

def find_col(df: pd.DataFrame, aliases):
    target = {norm(a): a for a in aliases}
    for col in df.columns:
        if norm(col) in target:
            return col
    return None

# Aliases we will accept from the Excel
FN_ALIASES = [
    "Business Functions", "Business Function", "Function", "Dept", "Department",
    "Function Area", "Biz Function"
]
ACT_ALIASES = [
    "Business Function Activities", "Business Activities", "Activity", "Activities",
    "Process Step", "Task"
]
TYPE_ALIASES = [
    "AI Tool Type", "AI Tool Types", "AI Type", "Tool Type", "AI Category", "AI Tool Category"
]

# -------- Load data
DATA_FILE = "AI Tool Matrix.xlsx"

if not Path(DATA_FILE).exists():
    st.error(f"Couldn't find `{DATA_FILE}` in the app folder. "
             "Please upload it to your GitHub repo alongside `app.py`.")
    st.stop()

# We assume first sheet has the taxonomy table
try:
    sheet1 = pd.read_excel(DATA_FILE, sheet_name=0, engine="openpyxl")
except Exception as e:
    st.exception(e)
    st.stop()

# -------- Map columns safely
fn_col = find_col(sheet1, FN_ALIASES)
act_col = find_col(sheet1, ACT_ALIASES)
type_col = find_col(sheet1, TYPE_ALIASES)

with st.expander("Data check (click to open)"):
    st.write("Detected columns:")
    st.write({ "Function": fn_col, "Activity": act_col, "AI Tool Type": type_col })
    st.write("All columns found in your sheet:", list(sheet1.columns))

missing = [label for label, c in [("Business Function", fn_col),
                                  ("Activity", act_col),
                                  ("AI Tool Type", type_col)] if c is None]
if missing:
    st.warning(
        "Your Excel doesn't have the expected column names: " + ", ".join(missing) +
        ".\n\nPlease either rename the columns to standard names or add them. "
        "Accepted names include:\n"
        f"- Function: {FN_ALIASES}\n"
        f"- Activity: {ACT_ALIASES}\n"
        f"- AI Tool Type: {TYPE_ALIASES}\n"
        "The app will continue using any columns it found."
    )

# Guard against total failure
if fn_col is None or act_col is None or type_col is None:
    st.stop()

# -------- UI Step 1: Needs
st.header("Step 1: Select Business Function & Activity")
functions = sorted(pd.Series(sheet1[fn_col].dropna().unique()).astype(str))
selected_function = st.selectbox("Business Function", functions)

activities = sorted(pd.Series(
    sheet1.loc[sheet1[fn_col] == selected_function, act_col].dropna().unique()
).astype(str))
selected_activity = st.selectbox("Activity", activities)

# -------- UI Step 2: Filter types
st.header("Step 2: Filter AI Tool Types")
mask = (sheet1[fn_col] == selected_function) & (sheet1[act_col] == selected_activity)
types_series = sheet1.loc[mask, type_col].dropna().astype(str).unique()

if len(types_series) == 0:
    st.warning("No AI Tool Types found for that function/activity. "
               "Please check your Excel or pick a different combination.")
    st.stop()

impact_map = {"LLM Assistant": "High", "Image Generation AI": "High",
              "RPA": "Medium", "Creative/Design AI": "High"}
type_options = [f"{t} (Impact: {impact_map.get(t, 'Unknown')})" for t in types_series]
selected_type = st.selectbox("AI Tool Type", type_options)
selected_type_clean = selected_type.split(' (')[0]

# -------- Tool details (simple demo table)
tool_details = pd.DataFrame({
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

# -------- Step 3: Preferences
st.header("Step 3: Set Preferences")
col1, col2, col3 = st.columns(3)
with col1:
    complexity = st.selectbox("Complexity", ['Low', 'Medium', 'High'])
with col2:
    scalability = st.selectbox("Scalability", ['Low', 'Medium', 'High'])
with col3:
    cost = st.selectbox("Cost Structure", ['Free', 'Freemium', 'Subscription', 'Enterprise'])

# -------- Step 4: Matching tools
st.header("Step 4: Matching AI Tools")
matching = tool_details[(tool_details['Type'] == selected_type_clean) &
                        (tool_details['Pricing'].str.contains(cost, case=False, na=False))]

if matching.empty:
    st.info("No matching tools found. Broadening to all tools for this type.")
    matching = tool_details[tool_details['Type'] == selected_type_clean]

st.dataframe(matching[['Tool','Features','Strengths','Limitations','Pricing','Link']], use_container_width=True)

# -------- Step 5: Score & recommend
st.header("Step 5: Score Tools")
if not matching.empty:
    scores = {}
    for _, row in matching.iterrows():
        scores[row['Tool']] = st.slider(f"Score {row['Tool']} (1-5)", 1, 5, 3)
    best = max(scores, key=scores.get) if scores else None
    if best:
        st.success(f"Recommended Tool: {best}")
        st.write("- Check integration options")
        st.write("- Start with a pilot/test")
        st.write("- Monitor performance and ROI")
        st.write("- Ensure data privacy and compliance")
        st.write("- Review vendor support and documentation")

st.caption("Tip: To avoid column errors, keep your Excel headers close to: "
           "'Business Functions', 'Business Function Activities', 'AI Tool Type'.")
