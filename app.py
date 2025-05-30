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
    # Swinburne Logo
    st.image("data/swinburne_logo.png", width=200)
    st.markdown("## Navigation")
    selection = st.radio("Go to section:", [
        "Funding Insights",
        "Collaboration Network",
        "Gender Diversity",
        "Keyword Analysis",
        "Researcher Explorer",
        "Credits"
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

elif selection == "Credits":
    # Credits Page
    st.markdown(
        """
        <div style='text-align: center;'>
            <img src='data/swinburne_logo.png' width='200' style='margin-bottom: 20px;'/>
            <h1 style='color: #d90429;'> Project Credits</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("""
    ### Group Members:
    - **Nimur Rahman** — 105092109
    - **Md Minhaj Rahman** — 105300501
    - **Nishandeep Singh** — 105315259
    - **Rahul Kumar** — 105234040

    ### Faculty Supervisor:
    - **Dr. Dinh Ngọc Tân**

    ### Acknowledgements:
    - Swinburne University of Technology
    - Swiss National Science Foundation

    ---
    #### This dashboard is built as part of our COS60011-Technology Design Project (Data Analytics) course project, showcasing collaboration, funding insights, gender diversity, keyword analysis, and researcher exploration using real-world data.
    """)
