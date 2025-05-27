import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import pycountry

@st.cache_data
def load_collab_country_data():
    g2p = pd.read_csv("data/GrantToPerson.csv")
    people = pd.read_csv("data/Person.csv")
    inst = pd.read_csv("data/Institute.csv")
    grants = pd.read_csv("data/Grant.csv")

    # Basic merging for country
    merged = g2p.merge(people[['PersonNumber', 'InstituteNumber']], on='PersonNumber', how='left')
    merged = merged.merge(inst[['InstituteNumber', 'InstituteCountry']], on='InstituteNumber', how='left')
    merged = merged.merge(grants[['GrantNumber']], on='GrantNumber', how='left')

    merged = merged.dropna(subset=['InstituteCountry'])

    # Add dummy year so chart works
    merged['Year'] = 2020

    return merged

def get_country_iso(name):
    try:
        return pycountry.countries.lookup(name).alpha_3
    except:
        return None

def show_collaboration_by_country():
    st.title("🌍 Collaboration by Country")

    df = load_collab_country_data()

    with st.sidebar:
        st.markdown("### 🔧 Options")
        top_n = st.slider("Top Countries", 5, 20, 10)

    # === Top Countries Chart ===
    st.markdown("#### 🏆 Top Collaborating Countries")
    top_countries = df['InstituteCountry'].value_counts().head(top_n).reset_index()
    top_countries.columns = ['Country', 'Collaborations']

    bar = alt.Chart(top_countries).mark_bar().encode(
        x='Collaborations:Q',
        y=alt.Y('Country:N', sort='-x')
    )
    st.altair_chart(bar, use_container_width=True)

    # === Choropleth Map ===
    st.markdown("#### 🗺️ Global Collaboration Map")
    df['ISO'] = df['InstituteCountry'].apply(get_country_iso)
    map_data = df.groupby("ISO").size().reset_index(name="Collaborations")

    fig = px.choropleth(
        map_data,
        locations="ISO",
        color="Collaborations",
        color_continuous_scale="Blues",
        title="Collaborations by Country"
    )
    st.plotly_chart(fig, use_container_width=True)

    # === Download CSV ===
    with st.expander("📥 Download Data"):
        st.dataframe(df[["InstituteCountry", "GrantNumber"]].head(300))
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Collaboration Data", csv, "collab_by_country.csv", "text/csv")
