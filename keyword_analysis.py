import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud
from nltk.corpus import stopwords
import plotly.express as px
from matplotlib_venn import venn3
import nltk

nltk.download("stopwords")

LANGUAGE_MAP = {
    "en": "English", "fr": "French", "de": "German", "it": "Italian",
    "es": "Spanish", "rm": "Romansh", "unknown": "Unknown"
}

@st.cache_data
def load_keywords_data():
    df = pd.read_csv("data/final_keywords_enriched.csv")
    df["StartYear"] = pd.to_datetime(df["StartDate"], errors="coerce").dt.year
    df["LanguageFull"] = df["Language"].map(LANGUAGE_MAP).fillna(df["Language"])
    return df

def generate_wordcloud(text_series, colormap):
    text = " ".join(str(t) for t in text_series if isinstance(t, str) and t.strip())
    if not text:
        st.warning("No valid text available for WordCloud.")
        return
    wordcloud = WordCloud(
        background_color="black",
        colormap=colormap,
        width=1000,
        height=300,
        max_words=100,
        stopwords=set(stopwords.words("english"))
    ).generate(text)
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)

def keyword_tab(df, column_name, color, colormap, selected_lang):
    data = df[df[column_name].notna()].copy()
    generate_wordcloud(data[column_name], colormap=colormap)

    top_disciplines = data["MainDiscipline"].value_counts().head(10).index.tolist()

    col1, col2, col3 = st.columns([2, 5, 3])
    with col1:
        top_n = st.selectbox("Top N Keywords", options=list(range(5, 55, 5)), index=1, key=f"{column_name}_topn")

    with col3:
        enable_disc_filter = st.checkbox("Enable Discipline Filter", value=False, key=f"{column_name}_check")
        if enable_disc_filter:
            selected_disciplines = st.multiselect("Top Disciplines", top_disciplines, default=top_disciplines, key=f"{column_name}_multi")
            data = data[data["MainDiscipline"].isin(selected_disciplines)]

    with col2:
        keywords = []
        for kw_string in data[column_name].dropna():
            parts = [kw.strip().lower() for kw in kw_string.replace(",", ";").split(";") if kw.strip()]
            keywords.extend(parts)

        counter = Counter(keywords)
        top_keywords = counter.most_common(top_n)

        if top_keywords:
            df_bar = pd.DataFrame(top_keywords, columns=["Keyword", "Frequency"])
            fig = px.bar(
                df_bar,
                x="Keyword",
                y="Frequency",
                title=f"Top {top_n} {column_name.replace('_', ' ')}",
                color_discrete_sequence=[color],
                text="Keyword"
            )
            fig.update_traces(textposition="outside", textfont_size=12)
            fig.update_layout(
                height=160,
                margin=dict(t=30, b=0, l=10, r=10),
                xaxis=dict(tickangle=45, tickfont=dict(size=1), showticklabels=False),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True, config={
                "displaylogo": False,
                "modeBarButtonsToRemove": ["zoom", "pan", "select", "lasso2d"],
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": f"{column_name}_top_keywords",
                    "height": 600,
                    "width": 1000,
                    "scale": 2
                }
            })
        else:
            st.warning("No keywords available for selected filters.")

def extract_keywords(series):
    keywords = []
    for s in series.dropna():
        parts = [kw.strip().lower() for kw in s.replace(",", ";").split(";") if kw.strip()]
        keywords.extend(parts)
    return set(keywords)

def show_keyword_insights():
    df_all = load_keywords_data()

    st.markdown("<h6 style='color:#3B4C59; margin-bottom:0.4rem;'>Keyword Analysis Dashboard</h6>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("Global Filters")
        lang_options = ["All Languages"] + sorted(set(LANGUAGE_MAP.get(code, code) for code in df_all["Language"].unique()))
        selected_lang = st.selectbox("Language", lang_options, index=0)
        min_y, max_y = int(df_all["StartYear"].min()), int(df_all["StartYear"].max())
        year_range = st.slider("Start Year", min_y, max_y, (1980, 2024))

    if selected_lang != "All Languages":
        filtered_df = df_all[df_all["LanguageFull"] == selected_lang]
    else:
        filtered_df = df_all.copy()

    filtered_df = filtered_df[filtered_df["StartYear"].between(year_range[0], year_range[1])]

    tabs = st.tabs(["TF-IDF", "RAKE", "YAKE", "Comparison"])

    with tabs[0]:
        keyword_tab(filtered_df, "TFIDF_Keywords", "#3B4C59", "plasma", selected_lang)

    with tabs[1]:
        keyword_tab(filtered_df, "RAKE_Keywords", "#9A5A41", "autumn", selected_lang)

    with tabs[2]:
        keyword_tab(filtered_df, "YAKE_Keywords", "#7A5B9D", "winter", selected_lang)

    with tabs[3]:
        required = ["GrantNumber", "Sentence", "TFIDF_Keywords", "RAKE_Keywords", "YAKE_Keywords"]
        missing = [col for col in required if col not in df_all.columns]
        if missing:
            st.warning(f"Missing columns: {', '.join(missing)}")
        else:
            compare_df = filtered_df[filtered_df[["TFIDF_Keywords", "RAKE_Keywords", "YAKE_Keywords"]].notna().any(axis=1)]
            compare_df = compare_df.drop_duplicates(subset="GrantNumber")

            st.markdown("<div style='margin-bottom:-0.6rem; font-size:14px;'>Top Keyword Rows (Click full screen to view more)</div>", unsafe_allow_html=True)
            st.dataframe(compare_df[required].head(3), use_container_width=True, height=140)

            tfidf_set = extract_keywords(compare_df["TFIDF_Keywords"])
            rake_set = extract_keywords(compare_df["RAKE_Keywords"])
            yake_set = extract_keywords(compare_df["YAKE_Keywords"])

            col_left, col_right = st.columns(2)

            with col_left:
                fig1, ax = plt.subplots(figsize=(5, 0.9))
                venn = venn3([tfidf_set, rake_set, yake_set], set_labels=("TF-IDF", "RAKE", "YAKE"), ax=ax)
                for p in venn.patches:
                    if p:
                        p.set_alpha(0.6)
                        p.set_linewidth(0.3)
                        p.set_edgecolor("black")
                for label in venn.set_labels:
                    if label:
                        label.set_fontsize(3)
                for label in venn.subset_labels:
                    if label:
                        label.set_fontsize(3)

                plt.title("Keyword Overlap", fontsize=10)
                st.pyplot(fig1)

            with col_right:
                overlap_counts = {
                    "Only TF-IDF": len(tfidf_set - rake_set - yake_set),
                    "Only RAKE": len(rake_set - tfidf_set - yake_set),
                    "Only YAKE": len(yake_set - tfidf_set - rake_set),
                    "TFIDF ∩ RAKE": len(tfidf_set & rake_set - yake_set),
                    "TFIDF ∩ YAKE": len(tfidf_set & yake_set - rake_set),
                    "RAKE ∩ YAKE": len(rake_set & yake_set - tfidf_set),
                    "All Three": len(tfidf_set & rake_set & yake_set)
                }

                df_overlap = pd.DataFrame.from_dict(overlap_counts, orient="index", columns=["Count"])
                df_overlap = df_overlap.reset_index().rename(columns={"index": "Category"})

                fig2 = px.bar(df_overlap, x="Category", y="Count", title="Overlap Counts",
                              color="Category", color_discrete_sequence=px.colors.qualitative.Set2)
                fig2.update_layout(
                    height=250,
                    margin=dict(t=30, b=10, l=10, r=10),
                    title_font_size=12,
                    xaxis_tickangle=20,
                    showlegend=False
                )
                st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    show_keyword_insights()
