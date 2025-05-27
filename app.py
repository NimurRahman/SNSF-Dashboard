import streamlit as st
from funding_insights import show_funding_insights
from collaboration_network import show_collaboration_network
from gender_diversity import show_gender_diversity
from keyword_analysis import show_keyword_insights
from researcher_explorer import show_researcher_explorer

# Set layout and page title
st.set_page_config(page_title="SNSF Research Dashboard", layout="wide")

# === Sidebar Navigation ===
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/6/6b/SNF_Logo_En.png", width=200)
    st.markdown("## Navigation")
    selection = st.radio("Go to section:", [
        "Funding Insights",
        "Collaboration Network",
        "Gender Diversity",
        "Keyword Analysis",
        "Researcher Explorer"
    ])

# === Section Routing ===
if selection == "Funding Insights":
    show_funding_insights()

elif selection == "Collaboration Network":
    show_collaboration_network()

elif selection == "Gender Diversity":
    show_gender_diversity()

elif selection == "Keyword Analysis":
    show_keyword_insights()

elif selection == "Researcher Explorer":
    show_researcher_explorer()
