import streamlit as st
import pandas as pd
import networkx as nx
import altair as alt
from pyvis.network import Network
import streamlit.components.v1 as components
import plotly.express as px
import pycountry

def show_collaboration_network():
    edges_df = pd.read_csv("data/institution_collaboration_edges.csv")
    collab_df = pd.read_csv("data/collaboration_data.csv")

    st.title("🤝 Collaboration Network Dashboard")

    theme = st.sidebar.selectbox("🎨 Theme", ["Light", "Dark"])
    if theme == "Dark":
        st.markdown("<style>body { background-color: #1E1E1E; color: white; }</style>", unsafe_allow_html=True)

    include_unknowns = st.sidebar.checkbox("Include Unknown Institutions", value=True)
    role_filter = st.sidebar.radio("🔄 Role", ["All", "Initiated"])
    top_n = st.sidebar.slider("Top N Links", 10, 50, 30)
    min_collab = st.sidebar.slider("Min Collab Count", 1, int(edges_df["collaboration_count"].max()), 5)

    if not include_unknowns:
        edges_df = edges_df[~edges_df['Institute_x'].astype(str).str.contains("unknown", case=False, na=False)]
        if "Institute" in collab_df.columns:
            collab_df = collab_df[~collab_df["Institute"].astype(str).str.contains("unknown", case=False, na=False)]

    all_insts = pd.unique(edges_df['Institute_x']).tolist()
    inst_search = st.sidebar.selectbox("Highlight Institution", [""] + sorted(all_insts))
    selected_insts = st.sidebar.multiselect("Focus Institutions", sorted(all_insts))

    filtered_edges = edges_df[edges_df["collaboration_count"] >= min_collab]
    if selected_insts:
        filtered_edges = filtered_edges[filtered_edges["Institute_x"].isin(selected_insts)]
    if role_filter == "Initiated":
        filtered_edges = filtered_edges[filtered_edges["Institute_x"].str.contains(inst_search, na=False, case=False)]
    elif inst_search:
        filtered_edges = filtered_edges[filtered_edges["Institute_x"].str.contains(inst_search, na=False, case=False)]

    top_edges = filtered_edges.sort_values(by="collaboration_count", ascending=False).head(top_n)

    G = nx.Graph()
    unique_nodes = top_edges['Institute_x'].unique()
    for i in range(len(unique_nodes) - 1):
        G.add_edge(unique_nodes[i], unique_nodes[i + 1], weight=1)

    node_list = pd.Series(unique_nodes)
    freq = node_list.value_counts()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Visuals", "🔸 Network", "🏫 Clustering", "📆 Trends"])

    with tab1:
        st.markdown("#### 🔍 Top Institutions & Roles")
        top_insts = freq.head(10).reset_index()
        top_insts.columns = ['Institution', 'Collaborations']
        chart1 = alt.Chart(top_insts).mark_bar(size=10).encode(x="Institution", y="Collaborations")

        out = top_edges['Institute_x'].value_counts().head(5).reset_index()
        out.columns = ['Institution', 'Count']
        out['Role'] = 'Initiated'
        chart2 = alt.Chart(out).mark_bar(size=10).encode(x="Institution", y="Count", color="Role")

        share_df = freq.head(10).reset_index()
        share_df.columns = ['Institution', 'Count']
        share_df['Share (%)'] = round((share_df['Count'] / share_df['Count'].sum()) * 100, 1)
        chart3 = alt.Chart(share_df).mark_bar(size=10).encode(y=alt.Y("Institution", sort='-x'), x="Share (%)")

        high = (freq > 10).sum()
        low = (freq <= 10).sum()
        donut_df = pd.DataFrame({'Type': ['High Collaborators', 'Others'], 'Count': [high, low]})
        chart4 = alt.Chart(donut_df).mark_arc(innerRadius=30, outerRadius=70).encode(theta="Count", color="Type")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.altair_chart(chart1, use_container_width=True)
        with col2:
            st.altair_chart(chart2, use_container_width=True)
        with col3:
            st.altair_chart(chart3, use_container_width=True)
        with col4:
            st.altair_chart(chart4, use_container_width=True)

        st.markdown("#### ⬇️ Download Data")
        csv = top_edges.to_csv(index=False).encode('utf-8')
        st.download_button("📄 Download Filtered", csv, "filtered_collaborations.csv", "text/csv")

    with tab2:
        st.markdown("#### 🔸 Interactive Network")
        st.write(f"🧠 Nodes: {len(G.nodes)} | Edges: {len(G.edges)}")
        net = Network(height="600px", width="100%", bgcolor="#FFFFFF", font_color="black")
        net.from_nx(G)
        for node in G.nodes:
            size = freq.get(node, 5)
            net_node = net.get_node(node)
            if net_node:
                net_node["size"] = int(size)
                net_node["label"] = node
                net_node["title"] = f"{node} – {int(size)} links"
                if inst_search and inst_search.lower() in node.lower():
                    net_node["color"] = "#FF5733"
        net.force_atlas_2based(gravity=-50)
        net.save_graph("network.html")
        components.html(open("network.html", "r", encoding="utf-8").read(), height=600)

        st.markdown("#### 🌍 Geographic Distribution Map")

        def get_country_code(institute):
            if "switzerland" in institute.lower():
                return "CHE"
            if "lausanne" in institute.lower():
                return "CHE"
            if "zurich" in institute.lower():
                return "CHE"
            return None

        map_df = pd.DataFrame(top_edges['Institute_x'])
        map_df['Country'] = map_df['Institute_x'].apply(get_country_code)
        country_counts = map_df['Country'].value_counts().reset_index()
        country_counts.columns = ['ISO', 'Collaborations']

        if not country_counts.empty:
            fig = px.choropleth(
                country_counts,
                locations='ISO',
                color='Collaborations',
                color_continuous_scale='Blues',
                title="Collaborations by Country",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📜 No geographic data found for plotting.")

    with tab3:
        st.markdown("#### 🏫 Institutional Clustering")
        node_counts = node_list.value_counts().reset_index()
        node_counts.columns = ['Institution', 'Links']
        high_density = node_counts[node_counts['Links'] > 10]
        low_density = node_counts[node_counts['Links'] <= 10]
        donut_data = pd.DataFrame({
            'Type': ['Dense (>10)', 'Low (≤10)'],
            'Count': [len(high_density), len(low_density)]
        })
        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(
                alt.Chart(donut_data).mark_arc(innerRadius=50).encode(theta="Count", color="Type"),
                use_container_width=True
            )
        with col2:
            st.altair_chart(
                alt.Chart(high_density.head(10)).mark_bar().encode(y=alt.Y("Institution", sort='-x'), x="Links"),
                use_container_width=True
            )

    with tab4:
        st.markdown("#### 📆 Collaboration Timeline & Funding Trends")

        if 'start_year' not in collab_df.columns or collab_df['start_year'].isnull().all():
            year_cols = [col for col in collab_df.columns if "year" in col.lower()]
            if year_cols:
                collab_df['start_year'] = pd.to_numeric(collab_df[year_cols[0]], errors='coerce')
            else:
                possible_date_cols = [col for col in collab_df.columns if 'date' in col.lower() or 'start' in col.lower()]
                for col in possible_date_cols:
                    try:
                        collab_df[col] = pd.to_datetime(collab_df[col], errors='coerce')
                        collab_df['start_year'] = collab_df[col].dt.year
                        break
                    except:
                        continue

        if 'start_year' not in collab_df.columns:
            collab_df['start_year'] = None
        if 'AmountGranted' not in collab_df.columns:
            collab_df['AmountGranted'] = 0

        has_year = 'start_year' in collab_df.columns and collab_df['start_year'].notnull().any()
        has_funding = 'AmountGranted' in collab_df.columns and collab_df['AmountGranted'].notnull().any()

        col1, col2 = st.columns(2)
        try:
            if has_year:
                timeline = collab_df.groupby('start_year').size().reset_index(name='Collaborations')
                col1.altair_chart(
                    alt.Chart(timeline).mark_line(point=True).encode(x="start_year", y="Collaborations"),
                    use_container_width=True
                )
            else:
                col1.empty()

            if has_year and has_funding:
                funding = collab_df.groupby('start_year')['AmountGranted'].sum().reset_index()
                col2.altair_chart(
                    alt.Chart(funding).mark_area().encode(x="start_year", y="AmountGranted"),
                    use_container_width=True
                )
            else:
                col2.empty()
        except Exception as e:
            st.error(f"❌ Chart rendering failed: {e}")

        st.markdown("#### 📋 Collaboration Data Table")
        st.dataframe(collab_df.head(300), height=300)
