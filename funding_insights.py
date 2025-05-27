import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_funding_data():
    df = pd.read_csv("data/grant_final.csv")
    df = df[df['AmountGrantedAllSets'].notna()]
    df['AmountGrantedAllSets'] = pd.to_numeric(df['AmountGrantedAllSets'], errors='coerce')
    df['CallDecisionYear'] = pd.to_numeric(df['CallDecisionYear'], errors='coerce')
    return df

def styled_plot(fig):
    fig.update_layout(
        margin=dict(t=25, b=20, l=10, r=10),
        plot_bgcolor="#E4E1DC",
        paper_bgcolor="#E4E1DC",
        font=dict(color="#2B2B2B", size=11),
        xaxis=dict(color="#2B2B2B"),
        yaxis=dict(color="#2B2B2B"),
        legend=dict(font=dict(color="#2B2B2B"))
    )
    return fig

def show_funding_insights():
    st.markdown("<h5 style='color:#3B4C59; margin-bottom:0.3rem;'>Funding Insights Dashboard</h5>", unsafe_allow_html=True)
    df = load_funding_data()

    with st.sidebar:
        min_year, max_year = int(df['CallDecisionYear'].min()), int(df['CallDecisionYear'].max())
        year_range = st.slider("Call Decision Year", min_year, max_year, (min_year, max_year))
        df = df[(df['CallDecisionYear'] >= year_range[0]) & (df['CallDecisionYear'] <= year_range[1])]
        top_n = st.selectbox("Show Top N Items", options=[5, 10, 15, 20, 30, 40, 50], index=0)

    tabs = st.tabs(["Overview", "By Discipline", "By Institution", "By Funding Type", "By Duration"])

    # === OVERVIEW ===
    with tabs[0]:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Grants", f"{df.shape[0]:,}")
        col2.metric("Total Funding (CHF)", f"CHF {df['AmountGrantedAllSets'].sum():,.0f}")
        col3.metric("Avg Grant Size", f"CHF {df['AmountGrantedAllSets'].mean():,.0f}")
        col4, col5, col6, col7 = st.columns(4)

        yearly_total = df.groupby("CallDecisionYear")["AmountGrantedAllSets"].sum().reset_index()
        fig1 = px.area(yearly_total, x="CallDecisionYear", y="AmountGrantedAllSets", title="Total Funding",
                       color_discrete_sequence=["#3B4C59"])
        fig1.update_layout(height=230)
        col4.plotly_chart(styled_plot(fig1), use_container_width=True)

        yearly_count = df.groupby("CallDecisionYear").size().reset_index(name="GrantCount")
        fig2 = px.bar(yearly_count, x="CallDecisionYear", y="GrantCount", title="Grant Count",
                      color_discrete_sequence=["#9A5A41"])
        fig2.update_layout(height=230)
        col5.plotly_chart(styled_plot(fig2), use_container_width=True)

        yearly_avg = df.groupby("CallDecisionYear")["AmountGrantedAllSets"].mean().reset_index()
        fig3 = px.line(yearly_avg, x="CallDecisionYear", y="AmountGrantedAllSets", title="Avg Grant Size",
                       color_discrete_sequence=["#7A5B9D"])
        fig3.update_layout(height=230)
        col6.plotly_chart(styled_plot(fig3), use_container_width=True)

        yearly_total["YoY_Growth"] = yearly_total["AmountGrantedAllSets"].pct_change() * 100
        fig4 = px.bar(yearly_total, x="CallDecisionYear", y="YoY_Growth", title="YoY Growth (%)",
                      color_discrete_sequence=["#3B4C59"])
        fig4.update_layout(height=230)
        col7.plotly_chart(styled_plot(fig4), use_container_width=True)
    # === BY DISCIPLINE ===
    with tabs[1]:
        st.markdown("<h6 style='margin-bottom: 0.2rem;'>Top Disciplines by Funding, Count, Avg & Trend</h6>", unsafe_allow_html=True)

        # Prepare data
        top_funding = df.groupby("MainDiscipline")["AmountGrantedAllSets"].sum().reset_index()
        top_funding = top_funding.sort_values("AmountGrantedAllSets", ascending=False).head(top_n)

        top_counts = df["MainDiscipline"].value_counts().head(top_n).reset_index()
        top_counts.columns = ["MainDiscipline", "GrantCount"]

        avg_grant = df.groupby("MainDiscipline")["AmountGrantedAllSets"].mean().reset_index()
        avg_grant = avg_grant.sort_values("AmountGrantedAllSets", ascending=False).head(top_n)

        # Row 1: 3 side-by-side charts
        col1, col2, col3 = st.columns(3)

        fig1 = px.bar(top_funding, x="AmountGrantedAllSets", y="MainDiscipline",
                      orientation="h", title="Total Funding", color_discrete_sequence=["#3B4C59"])
        fig1.update_layout(height=190)
        col1.plotly_chart(styled_plot(fig1), use_container_width=True)

        fig2 = px.bar(top_counts, x="GrantCount", y="MainDiscipline",
                      orientation="h", title="Grant Count", color_discrete_sequence=["#9A5A41"])
        fig2.update_layout(height=190)
        col2.plotly_chart(styled_plot(fig2), use_container_width=True)

        fig3 = px.bar(avg_grant, x="AmountGrantedAllSets", y="MainDiscipline",
                      orientation="h", title="Avg Grant Size", color_discrete_sequence=["#7A5B9D"])
        fig3.update_layout(height=190)
        col3.plotly_chart(styled_plot(fig3), use_container_width=True)

        # Row 2: Dropdown (right) + Trend (left)
        col_left, col_right = st.columns([8, 2])

        with col_right:
            st.markdown("""
                <div style='background-color:#E4E1DC; padding:8px 10px; border-radius:8px;'>
                    <label style='font-size:13px; color:#2B2B2B; font-weight:500;'>Select a discipline:</label>
                </div>
            """, unsafe_allow_html=True)
            selected_discipline = st.selectbox(
                "", sorted(df["MainDiscipline"].dropna().unique()),
                label_visibility="collapsed",
                key="discipline_selectbox"
            )

        trend_df = df[df["MainDiscipline"] == selected_discipline]
        trend_grouped = trend_df.groupby("CallDecisionYear")["AmountGrantedAllSets"].sum().reset_index()

        if not trend_grouped.empty:
            fig4 = px.line(trend_grouped, x="CallDecisionYear", y="AmountGrantedAllSets",
                           title=f"Funding Trend – {selected_discipline}",
                           color_discrete_sequence=["#3B4C59"])
            fig4.update_layout(height=140)
            col_left.plotly_chart(styled_plot(fig4), use_container_width=True)
        else:
            col_left.info("No funding data available for this discipline.")
    # === BY INSTITUTION ===
    with tabs[2]:
        st.markdown("<h6 style='margin-bottom: 0.2rem;'>Top Institutions by Funding, Count, Avg & Trend</h6>", unsafe_allow_html=True)

        # Prepare data
        top_funding = df.groupby("ResearchInstitution")["AmountGrantedAllSets"].sum().reset_index()
        top_funding = top_funding.sort_values("AmountGrantedAllSets", ascending=False).head(top_n)

        top_counts = df["ResearchInstitution"].value_counts().head(top_n).reset_index()
        top_counts.columns = ["ResearchInstitution", "GrantCount"]

        avg_grant = df.groupby("ResearchInstitution")["AmountGrantedAllSets"].mean().reset_index()
        avg_grant = avg_grant.sort_values("AmountGrantedAllSets", ascending=False).head(top_n)

        # Row 1: 3 compact bar charts
        col1, col2, col3 = st.columns(3)

        fig1 = px.bar(top_funding, x="AmountGrantedAllSets", y="ResearchInstitution",
                      orientation="h", title="Total Funding", color_discrete_sequence=["#3B4C59"])
        fig1.update_layout(height=190)
        col1.plotly_chart(styled_plot(fig1), use_container_width=True)

        fig2 = px.bar(top_counts, x="GrantCount", y="ResearchInstitution",
                      orientation="h", title="Grant Count", color_discrete_sequence=["#9A5A41"])
        fig2.update_layout(height=190)
        col2.plotly_chart(styled_plot(fig2), use_container_width=True)

        fig3 = px.bar(avg_grant, x="AmountGrantedAllSets", y="ResearchInstitution",
                      orientation="h", title="Avg Grant Size", color_discrete_sequence=["#7A5B9D"])
        fig3.update_layout(height=190)
        col3.plotly_chart(styled_plot(fig3), use_container_width=True)

        # Row 2: Dropdown (right) + Trend chart (left)
        col_left, col_right = st.columns([8, 2])

        with col_right:
            st.markdown("""
                <div style='background-color:#E4E1DC; padding:8px 10px; border-radius:8px;'>
                    <label style='font-size:13px; color:#2B2B2B; font-weight:500;'>Select institution:</label>
                </div>
            """, unsafe_allow_html=True)
            selected_inst = st.selectbox(
                "", sorted(df["ResearchInstitution"].dropna().unique()),
                label_visibility="collapsed",
                key="institution_selectbox"
            )

        trend_df = df[df["ResearchInstitution"] == selected_inst]
        trend_grouped = trend_df.groupby("CallDecisionYear")["AmountGrantedAllSets"].sum().reset_index()

        if not trend_grouped.empty:
            fig4 = px.line(trend_grouped, x="CallDecisionYear", y="AmountGrantedAllSets",
                           title=f"Funding Trend – {selected_inst}",
                           color_discrete_sequence=["#3B4C59"])
            fig4.update_layout(height=160)
            col_left.plotly_chart(styled_plot(fig4), use_container_width=True)
        else:
            col_left.info("No funding data available for this institution.")
    # === BY FUNDING TYPE ===
    with tabs[3]:
        st.markdown("<h6 style='margin-bottom: 0.2rem;'>Funding Insights by Instrument Type</h6>", unsafe_allow_html=True)

        if "FundingInstrumentLevel1" in df.columns:

            top_funding = df.groupby("FundingInstrumentLevel1")["AmountGrantedAllSets"].sum().reset_index()
            top_funding = top_funding.sort_values("AmountGrantedAllSets", ascending=False).head(top_n)

            top_counts = df["FundingInstrumentLevel1"].value_counts().head(top_n).reset_index()
            top_counts.columns = ["FundingInstrumentLevel1", "GrantCount"]

            avg_grant = df.groupby("FundingInstrumentLevel1")["AmountGrantedAllSets"].mean().reset_index()
            avg_grant = avg_grant.sort_values("AmountGrantedAllSets", ascending=False).head(top_n)

            col1, col2, col3 = st.columns(3)

            fig1 = px.bar(top_funding, x="AmountGrantedAllSets", y="FundingInstrumentLevel1",
                          orientation="h", title="Total Funding", color_discrete_sequence=["#3B4C59"])
            fig1.update_layout(height=190)
            col1.plotly_chart(styled_plot(fig1), use_container_width=True)

            fig2 = px.bar(top_counts, x="GrantCount", y="FundingInstrumentLevel1",
                          orientation="h", title="Grant Count", color_discrete_sequence=["#9A5A41"])
            fig2.update_layout(height=190)
            col2.plotly_chart(styled_plot(fig2), use_container_width=True)

            fig3 = px.bar(avg_grant, x="AmountGrantedAllSets", y="FundingInstrumentLevel1",
                          orientation="h", title="Avg Grant Size", color_discrete_sequence=["#7A5B9D"])
            fig3.update_layout(height=190)
            col3.plotly_chart(styled_plot(fig3), use_container_width=True)

            grouped = df.groupby(["CallDecisionYear", "FundingInstrumentLevel1"])["AmountGrantedAllSets"].sum().reset_index()

            fig4 = px.area(grouped, x="CallDecisionYear", y="AmountGrantedAllSets",
                           color="FundingInstrumentLevel1", title="Funding Over Time by Instrument",
                           color_discrete_sequence=px.colors.sequential.Purples_r)
            fig4.update_layout(height=190)

            total_by_year = df.groupby("CallDecisionYear")["AmountGrantedAllSets"].sum().reset_index(name="TotalFunding")
            share_df = pd.merge(grouped, total_by_year, on="CallDecisionYear")
            share_df["Share"] = (share_df["AmountGrantedAllSets"] / share_df["TotalFunding"]) * 100

            fig5 = px.line(share_df, x="CallDecisionYear", y="Share", color="FundingInstrumentLevel1",
                           title="% Share of Funding by Instrument", markers=True,
                           color_discrete_sequence=px.colors.qualitative.Set2)
            fig5.update_layout(height=190)

            col4, col5 = st.columns(2)
            col4.plotly_chart(styled_plot(fig4), use_container_width=True)
            col5.plotly_chart(styled_plot(fig5), use_container_width=True)

        else:
            st.warning("Column 'FundingInstrumentLevel1' not found in the dataset.")

    # === BY DURATION ===
    with tabs[4]:
        st.markdown("<h6 style='margin-bottom: 0.2rem;'>Funding Duration Insights</h6>", unsafe_allow_html=True)

        if "StartDate" in df.columns and "EndDate" in df.columns:
            df["StartDate"] = pd.to_datetime(df["StartDate"], errors="coerce")
            df["EndDate"] = pd.to_datetime(df["EndDate"], errors="coerce")
            df["DurationMonths"] = (df["EndDate"] - df["StartDate"]).dt.days // 30
            filtered_df = df[df["DurationMonths"].notna() & (df["DurationMonths"] > 0) & (df["DurationMonths"] < 100)]

            col1, col2, col3 = st.columns(3)

            avg_discipline = filtered_df.groupby("MainDiscipline")["DurationMonths"].mean().reset_index().sort_values("DurationMonths", ascending=False).head(top_n)
            fig1 = px.bar(avg_discipline, x="DurationMonths", y="MainDiscipline",
                          orientation="h", title="Avg Duration by Discipline",
                          color_discrete_sequence=["#3B4C59"])
            fig1.update_layout(height=180)
            col1.plotly_chart(styled_plot(fig1), use_container_width=True)

            fig2 = px.histogram(filtered_df, x="DurationMonths", nbins=25,
                                title="Duration Distribution", color_discrete_sequence=["#9A5A41"])
            fig2.update_layout(height=180)
            col2.plotly_chart(styled_plot(fig2), use_container_width=True)

            avg_inst = filtered_df.groupby("ResearchInstitution")["DurationMonths"].mean().reset_index().sort_values("DurationMonths", ascending=False).head(top_n)
            fig3 = px.bar(avg_inst, x="DurationMonths", y="ResearchInstitution",
                          orientation="h", title="Avg Duration by Institution",
                          color_discrete_sequence=["#7A5B9D"])
            fig3.update_layout(height=180)
            col3.plotly_chart(styled_plot(fig3), use_container_width=True)

            col_left, col_right = st.columns([8, 2])

            with col_right:
                st.markdown("""
                    <div style='background-color:#E4E1DC; padding:8px 10px; border-radius:8px;'>
                        <label style='font-size:13px; color:#2B2B2B; font-weight:500;'>Select Discipline:</label>
                    </div>
                """, unsafe_allow_html=True)
                selected_discipline = st.selectbox(
                    "", sorted(filtered_df["MainDiscipline"].dropna().unique()),
                    label_visibility="collapsed",
                    key="duration_discipline_selectbox"
                )

            trend_df = filtered_df[filtered_df["MainDiscipline"] == selected_discipline]
            trend_grouped = trend_df.groupby("CallDecisionYear")["DurationMonths"].mean().reset_index()

            if not trend_grouped.empty:
                fig4 = px.line(trend_grouped, x="CallDecisionYear", y="DurationMonths",
                               title=f"Avg Duration Over Time – {selected_discipline}",
                               color_discrete_sequence=["#3B4C59"])
                fig4.update_layout(height=160)
                col_left.plotly_chart(styled_plot(fig4), use_container_width=True)
            else:
                col_left.info("No duration data available for this discipline.")
        else:
            st.warning("StartDate or EndDate columns not found in the dataset.")
