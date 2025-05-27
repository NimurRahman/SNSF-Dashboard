import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

@st.cache_data
def load_gender_data():
    person_df = pd.read_csv("data/person_final.csv")
    g2p_df = pd.read_csv("data/GrantToPerson.csv")
    grant_df = pd.read_csv("data/grant_final.csv")

    merged1 = pd.merge(g2p_df, person_df, on="PersonNumber", how="left")
    merged2 = pd.merge(
        merged1,
        grant_df[['GrantNumber', 'start_year', 'CallDecisionYear', 'AmountGrantedAllSets', 'ResearchInstitution', 'MainDiscipline']],
        on="GrantNumber", how="left"
    )

    merged2 = merged2[merged2['Gender'].notna()]
    merged2['Gender'] = merged2['Gender'].str.strip().str.lower()
    return merged2

def show_gender_diversity():
    st.markdown("## 👥 Gender Diversity")

    df = load_gender_data()

    # Universal Top-N selector
    # Filters in sidebar
    with st.sidebar:
        st.subheader("Filters")
        top_n = st.selectbox("Select Top N results to display:", [5, 10, 20, 50], index=0, key="top_n")
        min_year, max_year = int(df['start_year'].min()), int(df['start_year'].max())
        year_range = st.slider("Start Year Range", min_year, max_year, (min_year, max_year))
        df = df[(df['start_year'] >= year_range[0]) & (df['start_year'] <= year_range[1])]

        disciplines = sorted(df['MainDiscipline'].dropna().unique())
        selected_disciplines = st.multiselect("Disciplines", ["(All)"] + disciplines, default=["(All)"])
        if "(All)" in selected_disciplines:
            selected_disciplines = disciplines
        df = df[df['MainDiscipline'].isin(selected_disciplines)]

    female_df = df[df['Gender'] == 'female']
    male_df = df[df['Gender'] == 'male']

    # Tab-based navigation
    tabs = st.tabs(["Overview", "Top Disciplines by Gender", "Gender Trends", "Funding Distribution"])

    with tabs[0]:
        st.subheader("🔍 Gender Overview")

        female_pct = round((female_df.shape[0] / df.shape[0]) * 100, 2) if df.shape[0] else 0
        male_pct = round((male_df.shape[0] / df.shape[0]) * 100, 2) if df.shape[0] else 0

        col1, col2 = st.columns(2)
        with col1:
            st.caption("🚺 Percentage of Female Researchers")
            fig_female = go.Figure(go.Indicator(
                mode="gauge+number",
                value=female_pct,
                title={'text': "% Female"},
                gauge={"axis": {"range": [0, 100]}, "bar": {"color": "pink"}}
            ))
            fig_female.update_layout(height=200, margin=dict(t=20, b=10, l=10, r=10), font=dict(size=10))
            st.plotly_chart(fig_female, use_container_width=True)

        with col2:
            st.caption("🚹 Percentage of Male Researchers")
            fig_male = go.Figure(go.Indicator(
                mode="gauge+number",
                value=male_pct,
                title={'text': "% Male"},
                gauge={"axis": {"range": [0, 100]}, "bar": {"color": "lightblue"}}
            ))
            fig_male.update_layout(height=200, margin=dict(t=20, b=10, l=10, r=10), font=dict(size=10))
            st.plotly_chart(fig_male, use_container_width=True)

        col3, col4, col5 = st.columns(3)
        col3.metric("Female Researchers", female_df.shape[0])
        col4.metric("Male Researchers", male_df.shape[0])
        col5.metric("Total Grants", df.shape[0])

        col6, col7, col8 = st.columns(3)
        with col6:
            st.caption("👥 Researcher Count")
            pie1 = pd.DataFrame({"Gender": ["Female", "Male"], "Count": [female_df.shape[0], male_df.shape[0]]})
            fig1 = px.pie(pie1, names="Gender", values="Count", hole=0.4)
            fig1.update_layout(height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig1, use_container_width=True)

        with col7:
            st.caption("💰 Total Funding")
            pie2 = df.groupby("Gender")["AmountGrantedAllSets"].sum().reset_index()
            fig2 = px.pie(pie2, names="Gender", values="AmountGrantedAllSets", hole=0.4)
            fig2.update_layout(height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig2, use_container_width=True)

        with col8:
            st.caption("📊 Average Funding")
            avg_female = female_df["AmountGrantedAllSets"].mean()
            avg_male = male_df["AmountGrantedAllSets"].mean()
            pie3 = pd.DataFrame({"Gender": ["Female", "Male"], "Average Funding": [avg_female, avg_male]})
            fig3 = px.pie(pie3, names="Gender", values="Average Funding", hole=0.4)
            fig3.update_layout(height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig3, use_container_width=True)

    with tabs[1]:
        st.subheader("🏅 Top Disciplines by Gender")
        col1, col2 = st.columns(2)

        with col1:
            st.caption("🎓 Female Disciplines")
            female_top = female_df['MainDiscipline'].value_counts().head(top_n).reset_index()
            female_top.columns = ['Discipline', 'Grants']
            fig1 = px.bar(female_top, x='Grants', y='Discipline', orientation='h')
            fig1.update_layout(yaxis={'categoryorder': 'total ascending'}, height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.caption("🎓 Male Disciplines")
            male_top = male_df['MainDiscipline'].value_counts().head(top_n).reset_index()
            male_top.columns = ['Discipline', 'Grants']
            fig2 = px.bar(male_top, x='Grants', y='Discipline', orientation='h')
            fig2.update_layout(yaxis={'categoryorder': 'total ascending'}, height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.caption("💵 Female Avg Funding")
            female_fund = female_df.groupby('MainDiscipline')['AmountGrantedAllSets'].mean().sort_values(ascending=False).head(top_n).reset_index()
            female_fund.columns = ['Discipline', 'Avg Funding']
            fig3 = px.bar(female_fund, x='Avg Funding', y='Discipline', orientation='h')
            fig3.update_layout(yaxis={'categoryorder': 'total ascending'}, height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            st.caption("💵 Male Avg Funding")
            male_fund = male_df.groupby('MainDiscipline')['AmountGrantedAllSets'].mean().sort_values(ascending=False).head(top_n).reset_index()
            male_fund.columns = ['Discipline', 'Avg Funding']
            fig4 = px.bar(male_fund, x='Avg Funding', y='Discipline', orientation='h')
            fig4.update_layout(yaxis={'categoryorder': 'total ascending'}, height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig4, use_container_width=True)

    with tabs[2]:
        st.subheader("📈 Gender Participation Over Time")
        col1, col2 = st.columns(2)

        with col1:
            st.caption("📊 Participation Trend")
            trend_data = df.groupby(['start_year', 'Gender']).size().reset_index(name='Count')
            fig1 = px.line(trend_data, x='start_year', y='Count', color='Gender', markers=True)
            fig1.update_layout(height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.caption("💸 Funding Trend")
            funding_trend = df.groupby(['start_year', 'Gender'])['AmountGrantedAllSets'].sum().reset_index()
            fig2 = px.line(funding_trend, x='start_year', y='AmountGrantedAllSets', color='Gender', markers=True)
            fig2.update_layout(height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig2, use_container_width=True)

        st.caption("📈 Avg Funding Over Time")
        avg_funding_trend = df.groupby(['start_year', 'Gender'])['AmountGrantedAllSets'].mean().reset_index()
        fig3 = px.line(avg_funding_trend, x='start_year', y='AmountGrantedAllSets', color='Gender', markers=True)
        fig3.update_layout(height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig3, use_container_width=True)

    with tabs[3]:
        st.subheader("📊 Funding Distribution by Gender and Discipline")
        top_funding = df.groupby(['MainDiscipline', 'Gender'])['AmountGrantedAllSets'].sum().reset_index()
        top10_disciplines = top_funding.groupby('MainDiscipline')['AmountGrantedAllSets'].sum().nlargest(10).index.tolist()
        top_funding = top_funding[top_funding['MainDiscipline'].isin(top10_disciplines)]

        col1, col2 = st.columns(2)
        with col1:
            st.caption("🏆 Top Funded Disciplines")
            fig = px.bar(top_funding, x='AmountGrantedAllSets', y='MainDiscipline', color='Gender', orientation='h', text_auto='.2s')
            fig.update_layout(height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.caption("🔍 Gender Discipline Tree")
            sunburst_fig = px.sunburst(
                top_funding,
                path=['Gender', 'MainDiscipline'],
                values='AmountGrantedAllSets',
                color='Gender'
            )
            sunburst_fig.update_layout(height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(sunburst_fig, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.caption("🏛️ Institution Funding Treemap")
            fig_tree = px.treemap(df, path=['Gender', 'ResearchInstitution'], values='AmountGrantedAllSets')
            fig_tree.update_layout(height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_tree, use_container_width=True)

        with col4:
            st.caption("📅 Grant Count by Year")
            call_year_data = df.groupby(['CallDecisionYear', 'Gender']).size().reset_index(name='Count')
            fig_bar = px.bar(call_year_data, x='Count', y='CallDecisionYear', color='Gender', orientation='h',
                             title='Grant Count by Year and Gender',
                             color_discrete_map={"male": "lightblue", "female": "pink"})
            fig_bar.update_layout(height=250, font=dict(size=10), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_bar, use_container_width=True)

    st.sidebar.download_button("📥 Download Filtered CSV", df.to_csv(index=False), file_name="gender_data_filtered.csv")
