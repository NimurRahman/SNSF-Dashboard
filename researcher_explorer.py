import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Optional styled_plot import
try:
    from utils import styled_plot
    USE_STYLE = True
except ImportError:
    def styled_plot(fig, **kwargs):
        return fig
    USE_STYLE = False

@pd.api.extensions.register_dataframe_accessor("snsf")
class ResearcherHelper:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def filter_and_group(self):
        df = self._obj.dropna(subset=['start_year', 'AmountGrantedAllSets'])
        df = df[df['start_year'] > 1900]
        return df.groupby('start_year')['AmountGrantedAllSets'].sum().reset_index()

@st.cache_data
def load_data():
    person_df = pd.read_csv("data/person_final.csv")
    grant_df = pd.read_csv("data/grant_final.csv")
    g2p_df = pd.read_csv("data/GrantToPerson.csv")

    merged = pd.merge(g2p_df, person_df, on="PersonNumber", how="left")
    merged = pd.merge(
        merged,
        grant_df[['GrantNumber', 'AmountGrantedAllSets', 'start_year', 'MainDiscipline', 'InstituteCountry', 'Institute', 'Title']],
        on="GrantNumber",
        how="left"
    )
    merged['AmountGrantedAllSets'] = pd.to_numeric(merged['AmountGrantedAllSets'], errors='coerce')
    merged['start_year'] = pd.to_numeric(merged['start_year'], errors='coerce')
    merged['FullName'] = merged['FirstName'].fillna('') + ' ' + merged['Surname'].fillna('')
    merged['Title'] = merged['Title'].fillna('')

    if 'OutputType' not in merged.columns:
        merged['OutputType'] = np.random.choice([
            'Academic Event', 'Public Communication', 'Award', 'Dataset', 'Knowledge Transfer'
        ], len(merged))
    return merged

def show_researcher_explorer():
    st.title("Researcher Explorer")

    df = load_data()

    with st.sidebar:
        st.image("data/swinburne_logo.png", width=200)
        st.subheader("Filter Researchers")

        disciplines = sorted(df['MainDiscipline'].dropna().unique())
        selected_discipline = st.selectbox("Discipline", ["All"] + disciplines)
        if selected_discipline != "All":
            df = df[df['MainDiscipline'] == selected_discipline]

        if df['start_year'].notnull().any():
            min_year = int(df['start_year'].min())
            max_year = int(df['start_year'].max())
            start_year, end_year = st.slider("Grant Year Range", min_year, max_year, (min_year, max_year))
            df = df[(df['start_year'] >= start_year) & (df['start_year'] <= end_year)]

        institutes = sorted(df['Institute'].dropna().unique())
        selected_institute = st.selectbox("Institute", ["All"] + institutes)
        if selected_institute != "All":
            df = df[df['Institute'] == selected_institute]

        researcher_names = sorted([
            name for name in df['FullName'].dropna().unique()
            if name and not name.startswith('?') and '?' not in name
        ])
        selected = st.selectbox("Select Researcher", ["Select a researcher"] + researcher_names)

    if selected != "Select a researcher":
        researcher_df = df[df['FullName'] == selected]

        if not researcher_df.empty:
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Overview",
                "Visual Insights",
                "Research Impacts",
                "Compare Researchers",
                "Keywords"
            ])

            with tab1:
                st.header(f"Profile: {selected}")
                st.write(f"Institute: {researcher_df['Institute'].iloc[0]}")

                col1, col2 = st.columns(2)
                col1.metric("Grants", researcher_df['GrantNumber'].nunique())
                col2.metric("Total Funding (CHF)", f"{researcher_df['AmountGrantedAllSets'].sum():,.2f}")

                st.subheader("Grant Records")
                st.dataframe(researcher_df[['GrantNumber', 'AmountGrantedAllSets', 'start_year']])

                st.download_button(
                    "Download Grant Data",
                    researcher_df.to_csv(index=False),
                    f"{selected.replace(' ', '_')}_grants.csv"
                )

                st.subheader("Similar Researchers in the Same Discipline")

            main_discipline = researcher_df['MainDiscipline'].iloc[0]
            similar_df = df[(df['MainDiscipline'] == main_discipline) & (df['FullName'] != selected)]
            similar_names = similar_df[['FullName', 'Institute']].drop_duplicates().sort_values(by='FullName').head(10)

            if similar_names.empty:
                st.info("No similar researchers found in this discipline.")
            else:
                st.write(f"These researchers also work in {main_discipline}:")
                st.table(similar_names.rename(columns={
                    'FullName': 'Researcher',
                    'Institute': 'Affiliated Institute'
                }))

            with tab2:
                st.header("Funding Trend")
                yearly_funding = researcher_df.snsf.filter_and_group().sort_values(by='start_year')
                fig = px.line(yearly_funding, x='start_year', y='AmountGrantedAllSets', markers=True)
                st.plotly_chart(styled_plot(fig), use_container_width=True)

                st.header("Grant Output Types")
                output_data = researcher_df['OutputType'].value_counts().reset_index()
                output_data.columns = ['Output Type', 'Count']
                fig_pie = px.pie(output_data, names='Output Type', values='Count', hole=0.4)
                st.plotly_chart(styled_plot(fig_pie), use_container_width=True)

            with tab3:
                st.header("Researcher Locations")
                map_df = df.groupby('InstituteCountry')['FullName'].nunique().reset_index()
                map_df.columns = ['Country', 'Number of Researchers']
                fig_map = px.scatter_geo(
                    map_df,
                    locations="Country",
                    locationmode="country names",
                    size="Number of Researchers",
                    projection="natural earth",
                    title="Researchers by Country"
                )
                st.plotly_chart(styled_plot(fig_map), use_container_width=True)

                st.header("Swiss Universities – Grants & Funding")
                try:
                    df_map = pd.read_csv("data/all_swiss_universities_stats.csv")
                    fig_mapbox = px.scatter_mapbox(
                        df_map,
                        lat="Latitude",
                        lon="Longitude",
                        size="GrantCount",
                        hover_name="ResearchInstitution",
                        hover_data={"City": True, "GrantCount": True, "TotalFunding": True},
                        zoom=6,
                        mapbox_style="carto-positron",
                        title="Swiss Universities by Research Grant Count"
                    )
                    st.plotly_chart(styled_plot(fig_mapbox), use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading Swiss university map: {e}")

                st.header("Total Funding by Discipline")
                bar_df = df.groupby("MainDiscipline")["AmountGrantedAllSets"].sum().sort_values(ascending=False).reset_index()
                fig_bar = px.bar(
                    bar_df,
                    x="AmountGrantedAllSets",
                    y="MainDiscipline",
                    orientation='h',
                    title="Funding by Discipline",
                    labels={"AmountGrantedAllSets": "Total Funding (CHF)", "MainDiscipline": "Discipline"},
                    color="AmountGrantedAllSets",
                    color_continuous_scale="Blues"
                )
                st.plotly_chart(styled_plot(fig_bar), use_container_width=True)

                st.header("Predicted Research Trend (Next 10 Years)")
                discipline_years = df.dropna(subset=['MainDiscipline', 'start_year'])
                trend_data = discipline_years.groupby(['start_year', 'MainDiscipline']).size().reset_index(name='Counts')

                future_years = np.arange(df['start_year'].max() + 1, df['start_year'].max() + 11)
                prediction_rows = []

                for discipline, group in trend_data.groupby('MainDiscipline'):
                    if len(group) >= 2:
                        model = np.poly1d(np.polyfit(group['start_year'], group['Counts'], 1))
                        predicted_counts = model(future_years)
                        for year, count in zip(future_years, predicted_counts):
                            prediction_rows.append({
                                'MainDiscipline': discipline,
                                'Year': year,
                                'Predicted': max(0, count)
                            })

                prediction_df = pd.DataFrame(prediction_rows)
                fig_pred = px.line(
                    prediction_df,
                    x='Year',
                    y='Predicted',
                    color='MainDiscipline',
                    title="Projected Research Activity by Discipline (Next 10 Years)",
                    labels={"Predicted": "Projected Grant Count"}
                )
                st.plotly_chart(styled_plot(fig_pred), use_container_width=True)

            with tab4:
                st.header("Compare Researchers")
                r_list = sorted([
                    name for name in df['FullName'].dropna().unique()
                    if name and not name.startswith('?') and '?' not in name
                ])
                col1, col2 = st.columns(2)
                r1 = col1.selectbox("Researcher A", r_list, key="r1")
                r2 = col2.selectbox("Researcher B", r_list, key="r2")
                d1 = df[df['FullName'] == r1]
                d2 = df[df['FullName'] == r2]
                trend1 = d1.groupby('start_year')['AmountGrantedAllSets'].sum().reset_index()
                trend2 = d2.groupby('start_year')['AmountGrantedAllSets'].sum().reset_index()
                fig = px.line()
                fig.add_scatter(x=trend1['start_year'], y=trend1['AmountGrantedAllSets'], name=r1)
                fig.add_scatter(x=trend2['start_year'], y=trend2['AmountGrantedAllSets'], name=r2)
                st.plotly_chart(fig, use_container_width=True)

            with tab5:
                st.header("Keyword Cloud from Grant Titles")
                txt = " ".join(researcher_df['Title'].tolist())
                if txt.strip():
                    vec = CountVectorizer(stop_words='english', max_features=50)
                    X = vec.fit_transform([txt])
                    freqs = dict(zip(vec.get_feature_names_out(), X.toarray()[0]))
                    wc = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(freqs)
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                else:
                    st.warning("No keywords available from grant titles.")
    else:
        st.info("Please select a researcher from the dropdown.")
