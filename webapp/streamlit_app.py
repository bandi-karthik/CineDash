import os
import sys
import streamlit as st

# ------------------------------------------------
# Page config
# ------------------------------------------------
st.set_page_config(
    page_title="CineDashboard – MovieLens Explorer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",  # sidebar collapsed by default
)

# ------------------------------------------------
# Make project root importable so "engine" works
# ------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from engine.parser import csvreader
from engine.dataframe import dataframe
from engine.ops import functions


# --- Helper functions (logic unchanged) ---

def dict_len(df):
    return len(df[list(df.keys())[0]]) if df else 0


def to_rows(df, cols=None, limit=None):
    """
    Convert your dict-of-lists dataframe to a list of row dicts
    so Streamlit can show it nicely without pandas.
    """
    if not df or isinstance(df, str):
        return []

    if cols is None:
        cols = list(df.keys())

    l = len(df[cols[0]])
    if limit is not None:
        l = min(l, limit)

    out = []
    for i in range(l):
        row = {}
        for c in cols:
            row[c] = df[c][i]
        out.append(row)
    return out


def get_unique_values(df, col):
    return sorted(list(set(df[col])))


def parse_value(col_name, text):
    """
    Best-effort conversion of user text input into correct type
    based on column name.
    """
    text = text.strip()
    if text == "":
        return text

    # integer-ish columns
    if any(k in col_name.lower() for k in ["id", "year", "count", "sum"]):
        try:
            return int(text)
        except ValueError:
            try:
                return int(float(text))
            except ValueError:
                return text  # fallback as string

    # float-ish columns (ratings, averages)
    if any(k in col_name.lower() for k in ["rating", "avg"]):
        try:
            return float(text)
        except ValueError:
            return text

    # default: string
    return text


def engine_safe(df_or_msg, where):
    """
    If engine returned an error string, show it nicely in the UI and
    return None so caller can bail out.
    """
    if isinstance(df_or_msg, str):
        st.error(df_or_msg)
        st.caption(
            f"Above error was returned by the engine during **{where}**. "
            "Please adjust your selected columns / aggregation type and try again."
        )
        return None
    return df_or_msg


# --- Data loading (logic unchanged) ---
@st.cache_data(show_spinner=True)
def load_data():
    parse = csvreader()
    dfc = dataframe()
    ops = functions()

    data_dir = os.path.join(BASE_DIR, "data")

    movie_columns, movie_rows = parse.read_doc(
        os.path.join(data_dir, "movies.csv"), ","
    )
    rating_columns, rating_rows = parse.read_doc(
        os.path.join(data_dir, "ratings.csv"), ","
    )
    tag_columns, tag_rows = parse.read_doc(
        os.path.join(data_dir, "tags.csv"), ","
    )

    df_movies = dfc.create_frame(movie_columns, movie_rows, extract_year=True)
    df_ratings = dfc.create_frame(rating_columns, rating_rows)
    df_tags = dfc.create_frame(tag_columns, tag_rows)

    # movies per year for overview chart
    movies_per_year = ops.groupby(df_movies, ["year"], ["movieId"], "count")

    # simple inner join for other tabs (no suffixes)
    movies_ratings = ops.join(df_movies, df_ratings, ["movieId"], how="inner")

    return df_movies, df_ratings, df_tags, movies_per_year, movies_ratings


# --- MAIN ---
def main():

    # --- Global CSS: style, no sidebar, fixed tabs & sliders ---
    st.markdown(
        """
        <style>
        :root {
            --primary-color: #007BFF;
            --primary-soft: #e6f2ff;
            --bg-app: #f5f7fb;
            --card-bg: #ffffff;
            --card-border: #dee2e6;
            --text-main: #212529;
            --text-muted: #6c757d;
            --shadow-soft: 0 8px 20px rgba(15, 23, 42, 0.06);
        }

        /* --- Base & Font --- */
        html, body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        /* --- Keep Material icons as icons (fix keyboard_double_arrow_right) --- */
        .material-icons, .material-icons-outlined {
            font-family: "Material Icons Outlined", "Material Icons" !important;
        }

        /* --- Hide sidebar + collapsed control --- */
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* --- Main App Background --- */
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 0% 0%, #ecf3ff 0, #f7f9ff 40%, #fdfdfd 100%);
        }
        
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1.5rem;
            max-width: 1200px;
        }

        /* --- Hero Header --- */
        .hero-header {
            text-align: center;
            margin-bottom: 2.5rem;
            padding: 1.75rem 1rem 2rem 1rem;
            border-radius: 24px;
            background: radial-gradient(circle at 0% 0%, rgba(0, 123, 255, 0.14) 0, rgba(0, 123, 255, 0.04) 45%, rgba(255, 255, 255, 0.9) 100%);
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.12);
            border: 1px solid rgba(0, 123, 255, 0.25);
            backdrop-filter: blur(18px);
            animation: fadeInUp 0.6s ease-out;
        }

        .hero-title {
            font-size: 3.3rem;
            font-weight: 900;
            color: #0b1736;
            letter-spacing: 0.03em;
            margin-bottom: 0.4rem;
        }

        .hero-subtitle {
            font-size: 1.1rem;
            color: #1f2937;
            margin-bottom: 0.2rem;
        }

        .hero-subtitle span {
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            background-color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
            color: #0b4aa6;
            border: 1px solid rgba(148, 163, 184, 0.5);
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(14px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* --- Section Title --- */
        .section-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-main);
            margin-top: 0.75rem;
            margin-bottom: 0.75rem;
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
        }

        .section-title::before {
            content: "";
            width: 8px;
            height: 22px;
            border-radius: 999px;
            background: linear-gradient(180deg, var(--primary-color), #4c6fff);
            display: inline-block;
        }

        /* --- Step Chips (Query Builder) --- */
        .step-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.28rem 0.8rem;
            border-radius: 999px;
            background-color: var(--primary-soft);
            color: #0b4aa6;
            font-size: 0.86rem;
            font-weight: 600;
            margin-top: 1rem;
            margin-bottom: 0.3rem;
        }

        .step-chip span {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.25rem;
            height: 1.25rem;
            border-radius: 999px;
            background-color: #0b4aa6;
            color: #ffffff;
            font-size: 0.8rem;
        }

        /* --- Generic Card Wrapper --- */
        .app-card {
            background-color: var(--card-bg);
            border-radius: 18px;
            padding: 1.2rem 1.35rem;
            border: 1px solid var(--card-border);
            box-shadow: var(--shadow-soft);
            margin-bottom: 1.25rem;
        }

        .app-card--soft {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), #f6f9ff);
        }

        /* --- Tab Styling --- */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            background-color: transparent;
            padding: 0;
            border-radius: 16px;
            margin-bottom: -6px;
        }
        
        [data-testid="stTabs"] [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 999px;
            font-weight: 600;
            color: #4b5563;
            transition: all 0.25s ease;
            padding: 0.3rem 1.3rem;
            margin-right: 0.25rem;
        }
        
        [data-testid="stTabs"] [data-baseweb="tab"]:hover {
            background-color: rgba(0, 123, 255, 0.08);
            color: #0b4aa6;
        }

        [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
            background: radial-gradient(circle at 0% 0%, #2563eb 0, #1d4ed8 45%, #1d4ed8 100%);
            color: #FFFFFF;
            box-shadow: 0 10px 25px rgba(37, 99, 235, 0.3);
        }

        /* remove the tiny red underline / highlight bar under active tab */
        [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            display: none !important;
        }

        [data-testid="stTabContent"] {
            background-color: transparent;
            padding-top: 1rem;
        }
        
        /* --- Metric "Card" Styling --- */
        [data-testid="stMetric"] {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.1rem 1.2rem;
            box-shadow: var(--shadow-soft);
            transition: all 0.25s ease;
        }
        
        [data-testid="stMetric"]:hover {
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.14);
            transform: translateY(-2px);
        }
        
        [data-testid="stMetric"] label {
            font-weight: 600;
            color: #4b5563;
        }
        
        [data-testid="stMetric"] .stMetricValue {
            font-size: 2rem;
            font-weight: 800;
            color: #1d4ed8;
        }
        
        /* --- Slider Styling (labels visible) --- */
        [data-testid="stSlider"] [data-baseweb="slider"] {
            padding-bottom: 18px;
        }

        [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
            background-color: #ffffff;
            border: 2px solid #1d4ed8;
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.18);
        }
        
        [data-testid="stSlider"] [data-baseweb="slider"] > div:first-child {
            background-color: #e5e7eb;
        }
        
        [data-testid="stSlider"] [data-baseweb="slider"] > div:nth-child(2) {
            background: linear-gradient(90deg, #bfdbfe, #c7d2fe);
        }

        [data-testid="stSlider"] label {
            font-weight: 500;
            color: #374151;
        }

        [data-testid="stSlider"] span {
            background-color: rgba(248, 250, 252, 0.85);
            border-radius: 4px;
            padding: 0 3px;
        }
        
        /* --- Selectbox & Multiselect Styling --- */
        [data-testid="stSelectbox"] div[data-baseweb="select"],
        [data-testid="stMultiSelect"] [data-baseweb="control"] {
            background-color: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 12px;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
            transition: all 0.2s ease;
        }
        
        [data-testid="stSelectbox"] div[data-baseweb="select"]:hover,
        [data-testid="stMultiSelect"] [data-baseweb="control"]:hover {
            border-color: #2563eb;
            box-shadow: 0 9px 24px rgba(37, 99, 235, 0.22);
        }

        /* --- Checkboxes & Radio --- */
        [data-testid="stCheckbox"] label,
        [data-testid="stRadio"] label {
            font-weight: 500;
            color: #374151;
        }

        /* --- DataFrame Styling --- */
        [data-testid="stDataFrame"] > div {
            border-radius: 16px !important;
            border: 1px solid var(--card-border);
            box-shadow: var(--shadow-soft);
            overflow: hidden;
            background-color: #ffffff;
        }

        [data-testid="stDataFrame"] table {
            font-size: 0.9rem;
        }

        [data-testid="stDataFrame"] tbody tr:hover {
            background-color: #eef2ff !important;
        }

        [data-testid="stDataFrame"] thead tr {
            background: linear-gradient(90deg, #2563eb, #4f46e5) !important;
        }

        [data-testid="stDataFrame"] thead th {
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        /* --- Spinner Color --- */
        [data-testid="stSpinner"] > div {
            border-top-color: #2563eb;
        }
        
        /* --- Styled Captions --- */
        [data-testid="stCaption"] {
            font-style: italic;
            color: #475569;
            background-color: rgba(226, 232, 240, 0.7);
            border-radius: 8px;
            padding: 0.5rem 0.75rem;
            border-left: 3px solid #2563eb;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- Hero header ---
    st.markdown(
        """
        <div class="hero-header">
            <div class="hero-title">🎥CineDashboard</div>
            <p class="hero-subtitle">
                MovieLens analytics &amp; search powered by your custom SQL-style engine.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Data load ---
    with st.spinner("Loading data with custom CSV parser and dataframe engine..."):
        df_movies, df_ratings, df_tags, movies_per_year, movies_ratings = load_data()

    ops_obj = functions()

    # --- Tabs ---
    tab_overview, tab_movies, tab_ratings, tab_tags, tab_query = st.tabs(
        [
            "📊 Overview",
            "🎬 Movie Explorer",
            "⭐ Ratings & Top Movies",
            "🏷 Tags Explorer",
            "🔎 Query Builder",
        ]
    )

    # --- TAB 1: OVERVIEW ---
    with tab_overview:
        st.markdown(
            '<p class="section-title">Dataset Snapshot</p>',
            unsafe_allow_html=True,
        )

        total_movies = dict_len(df_movies)
        total_ratings = dict_len(df_ratings)
        unique_users = len(set(df_ratings["userId"]))
        valid_years = [y for y in df_movies["year"] if isinstance(y, int) and y > 1800]
        min_year = min(valid_years)
        max_year = max(valid_years)

        st.markdown('<div class="app-card app-card--soft">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Movies", f"{total_movies:,}")
        col2.metric("Ratings", f"{total_ratings:,}")
        col3.metric("Unique Users", f"{unique_users:,}")
        col4.metric("Year Range", f"{min_year} — {max_year}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            '<p class="section-title">Movies Released per Year</p>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        years = []
        counts = []
        for y, c in zip(movies_per_year["year"], movies_per_year["movieId_count"]):
            if isinstance(y, int) and y > 1800:
                years.append(y)
                counts.append(c)

        if years and counts:
            chart_data = {"year": years, "movies": counts}
            st.line_chart(chart_data, x="year", y="movies", color="#2563eb")
        else:
            st.info("No data available to plot after filtering.")

        st.caption(
            "Above: uses your custom groupby( year, movieId, 'count' ) to build this trend."
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 2: MOVIE EXPLORER ---
    with tab_movies:
        st.markdown(
            '<p class="section-title">Interactive Movie Explorer</p>',
            unsafe_allow_html=True,
        )

        years = get_unique_values(df_movies, "year")
        years = [y for y in years if isinstance(y, int) and y > 1800]

        st.markdown('<div class="app-card app-card--soft">', unsafe_allow_html=True)
        left_controls, _ = st.columns([1, 3])

        with left_controls:
            selected_year = st.selectbox(
                "Filter by year", options=["All Years"] + years, index=len(years)
            )

            min_avg_rating = st.slider(
                "Minimum average rating",
                min_value=0.0,
                max_value=5.0,
                value=3.5,
                step=0.5,
            )

            max_rows = st.slider(
                "Max rows to display",
                min_value=10,
                max_value=200,
                value=50,
                step=10,
            )
        st.markdown('</div>', unsafe_allow_html=True)

        id_to_title = {}
        id_to_year = {}
        for i in range(dict_len(df_movies)):
            mid = df_movies["movieId"][i]
            id_to_title[mid] = df_movies["title"][i]
            id_to_year[mid] = df_movies["year"][i]

        gb_avg = ops_obj.groupby(movies_ratings, ["movieId"], ["rating"], "avg")
        gb_cnt = ops_obj.groupby(movies_ratings, ["movieId"], ["rating"], "count")

        combined = {
            "movieId": [],
            "title": [],
            "year": [],
            "rating_avg": [],
            "rating_count": [],
        }

        for i in range(len(gb_avg["movieId"])):
            mid = gb_avg["movieId"][i]
            avg_val = gb_avg["rating_avg"][i]
            idx_cnt = gb_cnt["movieId"].index(mid)
            cnt_val = gb_cnt["rating_count"][idx_cnt]
            title = id_to_title.get(mid, "Unknown")
            year = id_to_year.get(mid, 0)
            combined["movieId"].append(mid)
            combined["title"].append(title)
            combined["year"].append(year)
            combined["rating_avg"].append(avg_val)
            combined["rating_count"].append(cnt_val)

        current_df = combined

        if selected_year != "All Years":
            current_df = ops_obj.filter(current_df, ["year"], ["="], [selected_year])

        current_df = ops_obj.filter(
            current_df, ["rating_avg"], [">="], [min_avg_rating]
        )

        current_df = ops_obj.order_rows(
            current_df, ["rating_avg"], type="dsc", limit=max_rows
        )

        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.markdown("##### Matching movies")
        st.write(f"Showing up to **{max_rows}** movies matching the filters:")

        st.dataframe(
            to_rows(
                current_df,
                cols=["movieId", "title", "year", "rating_avg", "rating_count"],
            )
        )

        st.caption(
            "This view uses your **join**, **filter**, **groupby (avg & count)**, "
            "**projection** and **order_rows** functions together."
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 3: RATINGS ---
    with tab_ratings:
        st.markdown(
            '<p class="section-title">Top Rated Movies</p>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="app-card app-card--soft">', unsafe_allow_html=True)
        min_count = st.slider(
            "Minimum number of ratings",
            min_value=5,
            max_value=500,
            value=100,
            step=5,
        )

        top_n = st.slider(
            "How many top movies to show",
            min_value=10,
            max_value=100,
            value=25,
            step=5,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        gb_avg = ops_obj.groupby(movies_ratings, ["movieId"], ["rating"], "avg")
        gb_cnt = ops_obj.groupby(movies_ratings, ["movieId"], ["rating"], "count")

        id_to_title = {}
        id_to_year = {}
        for i in range(dict_len(df_movies)):
            mid = df_movies["movieId"][i]
            id_to_title[mid] = df_movies["title"][i]
            id_to_year[mid] = df_movies["year"][i]

        top_df = {
            "movieId": [],
            "title": [],
            "year": [],
            "rating_avg": [],
            "rating_count": [],
        }

        for i in range(len(gb_avg["movieId"])):
            mid = gb_avg["movieId"][i]
            avg_val = gb_avg["rating_avg"][i]
            idx_cnt = gb_cnt["movieId"].index(mid)
            cnt_val = gb_cnt["rating_count"][idx_cnt]
            if cnt_val < min_count:
                continue
            title = id_to_title.get(mid, "Unknown")
            year = id_to_year.get(mid, 0)
            top_df["movieId"].append(mid)
            top_df["title"].append(title)
            top_df["year"].append(year)
            top_df["rating_avg"].append(avg_val)
            top_df["rating_count"].append(cnt_val)

        top_df = ops_obj.order_rows(top_df, ["rating_avg"], type="dsc", limit=top_n)

        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.dataframe(
            to_rows(
                top_df,
                cols=["movieId", "title", "year", "rating_avg", "rating_count"],
            )
        )

        st.caption(
            "Above: pure use of your engine — no pandas. "
            "We aggregate ratings per movie (avg + count), apply filters, then sort."
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 4: TAGS ---
    with tab_tags:
        st.markdown(
            '<p class="section-title">Tag Explorer</p>',
            unsafe_allow_html=True,
        )

        tag_stats = ops_obj.groupby(df_tags, ["tag"], ["movieId"], "count")
        tag_pairs = list(zip(tag_stats["tag"], tag_stats["movieId_count"]))
        tag_pairs.sort(key=lambda x: x[1], reverse=True)
        popular_tags = [t for t, _ in tag_pairs[:100]]

        st.markdown('<div class="app-card app-card--soft">', unsafe_allow_html=True)
        selected_tag = st.selectbox("Choose a popular tag", options=popular_tags)
        st.write(f"Showing movies tagged with **{selected_tag}**:")
        st.markdown('</div>', unsafe_allow_html=True)

        filtered_tags = ops_obj.filter(df_tags, ["tag"], ["="], [selected_tag])
        mt = ops_obj.join(df_movies, filtered_tags, ["movieId"], how="inner")
        mtr = ops_obj.join(mt, df_ratings, ["movieId"], how="inner")
        tag_avg = ops_obj.groupby(mtr, ["movieId"], ["rating"], "avg")
        tag_cnt = ops_obj.groupby(mtr, ["movieId"], ["rating"], "count")

        id_to_title = {}
        id_to_year = {}
        for i in range(dict_len(df_movies)):
            mid = df_movies["movieId"][i]
            id_to_title[mid] = df_movies["title"][i]
            id_to_year[mid] = df_movies["year"][i]

        final_df = {
            "movieId": [],
            "title": [],
            "year": [],
            "rating_avg": [],
            "rating_count": [],
        }

        for i in range(len(tag_avg["movieId"])):
            mid = tag_avg["movieId"][i]
            avg_val = tag_avg["rating_avg"][i]
            idx_cnt = tag_cnt["movieId"].index(mid)
            cnt_val = tag_cnt["rating_count"][idx_cnt]
            title = id_to_title.get(mid, "Unknown")
            year = id_to_year.get(mid, 0)
            final_df["movieId"].append(mid)
            final_df["title"].append(title)
            final_df["year"].append(year)
            final_df["rating_avg"].append(avg_val)
            final_df["rating_count"].append(cnt_val)

        final_df = ops_obj.order_rows(
            final_df, ["rating_avg"], type="dsc", limit=50
        )

        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.dataframe(
            to_rows(
                final_df,
                cols=["movieId", "title", "year", "rating_avg", "rating_count"],
            )
        )

        st.caption(
            "This tab chains together your **filter**, **join**, and **groupby** "
            "to let users explore the best movies for each tag."
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 5: QUERY BUILDER ---
    with tab_query:
        st.markdown(
            '<p class="section-title">Manual Query Builder</p>',
            unsafe_allow_html=True,
        )
        st.write(
            "Build your own query by choosing the dataset and which functions "
            "to apply: **joins**, **filter**, **group by / aggregation**, **projection**, and **sorting**."
        )

        # Step 0 -------------------------------------------------------------
        st.markdown(
            '<div class="step-chip"><span>0</span>Step 0 · Choose tables &amp; joins</div>',
            unsafe_allow_html=True,
        )

        BASE_OPTIONS = ["Movies", "Ratings", "Tags"]

        def get_df_and_suffix(name):
            if name == "Movies":
                return df_movies, "_movies"
            if name == "Ratings":
                return df_ratings, "_ratings"
            if name == "Tags":
                return df_tags, "_tags"
            raise ValueError("Unknown table")

        base_table = st.selectbox("Base table", BASE_OPTIONS, index=0)
        remaining_after_base = [t for t in BASE_OPTIONS if t != base_table]

        join1_enable = st.checkbox("Add first join", value=False)
        join1_table = None
        join1_type = None

        if join1_enable:
            join1_table = st.selectbox(
                "Join 1 – table",
                remaining_after_base,
                key="join1_table",
            )
            join1_type = st.selectbox(
                "Join 1 – type",
                ["inner", "left", "right", "full"],
                index=0,
                key="join1_type",
            )

        remaining_after_join1 = [
            t for t in remaining_after_base if t != join1_table
        ]

        join2_enable = False
        join2_table = None
        join2_type = None
        if join1_enable and remaining_after_join1:
            join2_enable = st.checkbox("Add second join", value=False)
            if join2_enable:
                join2_table = remaining_after_join1[0]
                st.write(f"Join 2 – table: **{join2_table}**")
                join2_type = st.selectbox(
                    "Join 2 – type",
                    ["inner", "left", "right", "full"],
                    index=0,
                    key="join2_type",
                )

        ops_local = functions()
        base_df_obj, base_suffix = get_df_and_suffix(base_table)
        working_df = base_df_obj

        if join1_enable and join1_table is not None:
            right_df, right_suffix = get_df_and_suffix(join1_table)
            working_df = ops_local.join(
                working_df,
                right_df,
                ["movieId"],
                how=join1_type,
                left_suffix="",
                right_suffix=right_suffix,
            )

        if join2_enable and join2_table is not None:
            right_df2, right_suffix2 = get_df_and_suffix(join2_table)
            working_df = ops_local.join(
                working_df,
                right_df2,
                ["movieId"],
                how=join2_type,
                left_suffix="",
                right_suffix=right_suffix2,
            )

        st.caption(
            "Current dataset = "
            + base_table
            + (f" {join1_type} join {join1_table}" if join1_enable and join1_table else "")
            + (f" {join2_type} join {join2_table}" if join2_enable and join2_table else "")
        )

        # Step 1 -------------------------------------------------------------
        st.markdown(
            '<div class="step-chip"><span>1</span>Step 1 · Filter rows (WHERE)</div>',
            unsafe_allow_html=True,
        )

        apply_filter = st.checkbox("Apply filter", value=False)

        columns = []
        conditions = []
        values = []
        seps = []

        if apply_filter:
            cols_available = list(working_df.keys())
            ops_list = ["=", "!=", ">", "<", ">=", "<="]

            # how many filter rows to show (stored in session_state)
            if "qb_num_conditions" not in st.session_state:
                st.session_state.qb_num_conditions = 1

            # buttons to add / reset filter rows
            btn_col_add, btn_col_reset = st.columns([1, 1])
            with btn_col_add:
                if st.button("➕ Add condition", key="qb_add_cond"):
                    st.session_state.qb_num_conditions += 1
            with btn_col_reset:
                if st.button("🧹 Reset conditions", key="qb_reset_cond"):
                    st.session_state.qb_num_conditions = 1

            # render each condition row
            for i in range(st.session_state.qb_num_conditions):
                c1, c2, c3, c4 = st.columns([3, 2, 3, 2])

                with c1:
                    col_name = st.selectbox(
                        f"Column {i + 1}",
                        options=cols_available,
                        key=f"qb_f_col_{i}",
                    )

                with c2:
                    op = st.selectbox(
                        f"Condition {i + 1}",
                        options=ops_list,
                        key=f"qb_f_op_{i}",
                    )

                with c3:
                    val_str = st.text_input(
                        f"Value {i + 1}",
                        key=f"qb_f_val_{i}",
                    )

                # first condition doesn't need a logical connector before it
                if i == 0:
                    sep = "and"
                    with c4:
                        st.markdown(
                            "<div style='opacity:0.4; font-size:0.85rem; padding-top:1.1rem;'>First condition</div>",
                            unsafe_allow_html=True,
                        )
                else:
                    with c4:
                        sep = st.selectbox(
                            "Combine with",
                            options=["and", "or"],
                            key=f"qb_f_sep_{i}",
                        )

                # only add if user entered a value
                if val_str.strip() != "":
                    columns.append(col_name)
                    conditions.append(op)
                    values.append(parse_value(col_name, val_str))
                    seps.append(sep)

        # apply filter if we collected any conditions
        if columns:
            working_df = ops_local.filter(working_df, columns, conditions, values, seps)
            working_df = engine_safe(working_df, "filter")
            if working_df is None:
                return  # stop query tab rendering here

        # Step 2 -------------------------------------------------------------
        st.markdown(
            '<div class="step-chip"><span>2</span>Step 2 · Group by &amp; aggregation (optional)</div>',
            unsafe_allow_html=True,
        )

        apply_group = st.checkbox("Apply aggregation", value=False)

        if apply_group:
            cols_after_filter = list(working_df.keys())
            agg_mode = st.radio(
                "Aggregation mode",
                options=["Group by column(s)", "Global aggregation over entire dataset"],
                horizontal=True,
            )

            if agg_mode == "Group by column(s)":
                gb_col = st.selectbox(
                    "Group by column", options=cols_after_filter, key="gb_col"
                )
                agg_candidates = [c for c in cols_after_filter if c != gb_col]
                agg_col = st.selectbox(
                    "Aggregation column", options=agg_candidates, key="agg_col"
                )
                agg_type = st.selectbox(
                    "Aggregation type",
                    options=["count", "sum", "avg", "min", "max"],
                    key="agg_type",
                )

                working_df = ops_local.groupby(working_df, [gb_col], [agg_col], agg_type)
                working_df = engine_safe(working_df, "groupby + aggregation")
                if working_df is None:
                    return
            else:
                cols_after_filter = list(working_df.keys())
                agg_col = st.selectbox(
                    "Aggregation column (entire dataset)",
                    options=cols_after_filter,
                    key="global_agg_col",
                )
                agg_type = st.selectbox(
                    "Aggregation type (entire dataset)",
                    options=["count", "sum", "avg", "min", "max"],
                    key="global_agg_type",
                )

                tmp_df = {k: v[:] for k, v in working_df.items()}
                tmp_df["_all"] = [1] * dict_len(working_df)

                tmp_df = ops_local.groupby(tmp_df, ["_all"], [agg_col], agg_type)
                tmp_df = engine_safe(tmp_df, "global aggregation")
                if tmp_df is None:
                    return

                working_df = tmp_df

        # Step 3 -------------------------------------------------------------
        st.markdown(
            '<div class="step-chip"><span>3</span>Step 3 · Projection &amp; sorting</div>',
            unsafe_allow_html=True,
        )

        cols_for_show = list(working_df.keys())
        show_cols = st.multiselect(
            "Columns to display", options=cols_for_show, default=cols_for_show
        )

        sort_col = st.selectbox(
            "Sort by (descending, uses order_rows)",
            options=["(no sorting)"] + cols_for_show,
        )

        max_rows_query = st.slider(
            "Max rows to display (query tab)",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            key="qb_max_rows",
        )

        if sort_col != "(no sorting)":
            working_df = ops_local.order_rows(
                working_df, [sort_col], type="dsc", limit=max_rows_query
            )

        st.markdown("### Query result")
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.dataframe(to_rows(working_df, cols=show_cols, limit=max_rows_query))

        st.caption(
            "This tab is a **manual query builder**. Depending on your choices, it "
            "chains together **joins** (inner / left / right / full between Movies, "
            "Ratings, and Tags), **filter**, **groupby / global aggregation**, "
            "**projection**, and **order_rows**."
        )
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
