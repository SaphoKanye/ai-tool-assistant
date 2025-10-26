import streamlit as st
import pandas as pd

# --- Load Data ---
# Replace with st.file_uploader for production, here we use static file names
sheet1 = pd.read_excel('AI Tool Matrix.xlsx', sheet_name=0)
sheet2 = pd.read_excel('AI Tool Matrix.xlsx', sheet_name=1)

# Simulate improved tool details from Word doc (expand as needed)
tool_details = pd.DataFrame({
    'Tool': ['ChatGPT', 'MidJourney', 'UiPath', 'Figma AI', 'Canva AI'],
    'Type': ['LLM Assistant', 'Image Generation AI', 'RPA', 'Creative/Design AI', 'Creative/Design AI'],
    'Features': ['Chatbot, content gen', 'Image gen', 'Automation', 'Design, prototyping', 'Graphic design'],
    'Strengths': ['Versatile', 'High quality', 'Scalable', 'User-friendly', 'Easy to use'],
    'Limitations': ['No real-time data', 'Subscription', 'Complex setup', 'Limited advanced features', 'Less technical'],
    'Pricing': ['Freemium', 'Subscription', 'Enterprise', 'Freemium', 'Freemium'],
    'Link': [
        'https://chatgpt.com/',
        'https://www.midjourney.com/',
        'https://www.uipath.com/',
        'https://www.figma.com/ai/',
        'https://www.canva.com/ai/'
    ]
})

st.title("AI Tool Selection Assistant (Improved)")

# --- Step 1: Needs Assessment ---
st.header("Step 1: Select Business Function & Activity")
business_functions = sheet1['Business Functions'].dropna().unique()
selected_function = st.selectbox("Business Function", business_functions)

activities = sheet1[sheet1['Business Functions'] == selected_function]['Business Function Activities'].dropna().unique()
selected_activity = st.selectbox("Activity", activities)

# --- Step 2: Filter AI Tool Types ---
st.header("Step 2: Filter AI Tool Types")
filtered_types = sheet1[
    (sheet1['Business Functions'] == selected_function) &
    (sheet1['Business Function Activities'] == selected_activity)
]['AI Tool Type'].dropna().unique()

# Improvement: Show impact ratings if available
impact_map = {
    'LLM Assistant': 'High',
    'Image Generation AI': 'High',
    'RPA': 'Medium',
    'Creative/Design AI': 'High'
}
type_options = []
for t in filtered_types:
    impact = impact_map.get(t, 'Unknown')
    type_options.append(f"{t} (Impact: {impact})")
selected_type = st.selectbox("AI Tool Type", type_options)
selected_type_clean = selected_type.split(' (')[0]

# --- Step 3: Set Preferences ---
st.header("Step 3: Set Preferences")
complexity = st.selectbox("Complexity", ['Low', 'Medium', 'High'])
scalability = st.selectbox("Scalability", ['Low', 'Medium', 'High'])
cost = st.selectbox("Cost Structure", ['Free', 'Freemium', 'Subscription', 'Enterprise'])

# --- Step 4: List Matching Tools ---
st.header("Step 4: Matching AI Tools")
matching_tools = tool_details[
    (tool_details['Type'] == selected_type_clean) &
    (tool_details['Pricing'].str.contains(cost))
]

if matching_tools.empty:
    st.warning("No matching tools found for your criteria. Consider broadening your filters or reviewing the taxonomy for gaps.")
else:
    st.dataframe(matching_tools[['Tool', 'Features', 'Strengths', 'Limitations', 'Pricing', 'Link']])

# --- Step 5: Score & Suggest ---
st.header("Step 5: Score Tools")
if not matching_tools.empty:
    scores = {}
    for idx, row in matching_tools.iterrows():
        score = st.slider(f"Score {row['Tool']} (1-5)", 1, 5, 3)
        scores[row['Tool']] = score
    best_tool = max(scores, key=scores.get)
    st.success(f"Recommended Tool: {best_tool}")
    st.write("Implementation Advice:")
    st.write("- Check integration options")
    st.write("- Start with a pilot/test")
    st.write("- Monitor performance and ROI")
    st.write("- Ensure data privacy and compliance")
    st.write("- Review vendor support and documentation")
else:
    st.info("Expand your search or review the taxonomy for more options.")

# --- Improvements & Suggestions ---
st.header("Copilot Suggestions & Improvements")
st.write("""
- **Clarified Impact Ratings:** Tool types now show impact ratings for easier decision-making.
- **Improved Scoring:** User can score tools, and the app recommends the best fit.
- **Actionable Advice:** Implementation steps are clearer and more practical.
- **Error Handling:** If no tools match, the app suggests next steps.
- **Extensible:** Easily add more tool details or refine the taxonomy.
""")

st.write("For further improvements, consider adding conversational AI, dynamic file uploads, and more granular filtering.")