import os
import sys
import streamlit as st

# ------------------------------------------------
# Make project root importable so "engine" works
# ------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # .../CineDash
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from engine.parser import csvreader
from engine.dataframe import dataframe
from engine.ops import functions



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



def main():
    st.set_page_config(
        page_title="CineDashboard – MovieLens Explorer",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Basic layout + section title styling
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1.2rem;
        }
        .section-title {
            font-size: 24px;
            font-weight: 700;
            margin-top: 12px;
            margin-bottom: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Vibrant title (solid + tiny shadow so it really pops)
    st.markdown(
        "<h1 style='text-align:center; font-size:50px; font-weight:900; "
        "margin-bottom:0.1rem; color:#ff4b4b; text-shadow:0 0 6px rgba(0,0,0,0.15);'>"
        "CineDashboard</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#666666; font-size:18px; "
        "margin-top:0;'>MovieLens analytics &amp; search powered by a custom SQL-style engine.</p>",
        unsafe_allow_html=True,
    )

    with st.spinner("Loading data with custom CSV parser and dataframe engine..."):
        df_movies, df_ratings, df_tags, movies_per_year, movies_ratings = load_data()

    ops_obj = functions()

    tab_overview, tab_movies, tab_ratings, tab_tags, tab_query = st.tabs(
        [
            "📊 Overview",
            "🎬 Movie Explorer",
            "⭐ Ratings & Top Movies",
            "🏷 Tags Explorer",
            "🔎 Query Builder",
        ]
    )


    with tab_overview:
        st.markdown(
            '<p class="section-title">Dataset Snapshot</p>',
            unsafe_allow_html=True,
        )

        total_movies = dict_len(df_movies)
        total_ratings = dict_len(df_ratings)
        unique_users = len(set(df_ratings["userId"]))

        # Ignore placeholder 0 years
        valid_years = [y for y in df_movies["year"] if isinstance(y, int) and y > 1800]
        min_year = min(valid_years)
        max_year = max(valid_years)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Movies", f"{total_movies:,}")
        col2.metric("Ratings", f"{total_ratings:,}")
        col3.metric("Unique Users", f"{unique_users:,}")
        col4.metric("Year Range", f"{min_year} — {max_year}")

        st.markdown(
            '<p class="section-title">Movies Released per Year</p>',
            unsafe_allow_html=True,
        )

        # Filter out year == 0 from chart
        years = []
        counts = []
        for y, c in zip(movies_per_year["year"], movies_per_year["movieId_count"]):
            if isinstance(y, int) and y > 1800:
                years.append(y)
                counts.append(c)

        if years and counts:
            chart_data = {"year": years, "movies": counts}
            st.line_chart(chart_data, x="year", y="movies",color="#28a745")
        else:
            st.info("No data available to plot after filtering.")


        st.caption(
            "Above: uses your custom groupby( year, movieId, 'count' ) to build this trend."
        )


    with tab_movies:
        st.markdown(
            '<p class="section-title">Interactive Movie Explorer</p>',
            unsafe_allow_html=True,
        )

        years = get_unique_values(df_movies, "year")
        years = [y for y in years if isinstance(y, int) and y > 1800]

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

        # Pre-build mapping movieId -> title/year
        id_to_title = {}
        id_to_year = {}
        for i in range(dict_len(df_movies)):
            mid = df_movies["movieId"][i]
            id_to_title[mid] = df_movies["title"][i]
            id_to_year[mid] = df_movies["year"][i]

        # 1) groupby movieId for avg rating
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

        # 4) filter by year and min avg rating using your filter
        current_df = combined

        if selected_year != "All Years":
            current_df = ops_obj.filter(current_df, ["year"], ["="], [selected_year])

        current_df = ops_obj.filter(
            current_df, ["rating_avg"], [">="], [min_avg_rating]
        )

        # 5) order rows by rating_avg desc
        current_df = ops_obj.order_rows(
            current_df, ["rating_avg"], type="dsc", limit=max_rows
        )

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


    with tab_ratings:
        st.markdown(
            '<p class="section-title">Top Rated Movies</p>',
            unsafe_allow_html=True,
        )

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

    with tab_tags:
        st.markdown(
            '<p class="section-title">Tag Explorer</p>',
            unsafe_allow_html=True,
        )

        # group tags by text, count how many times each tag occurs
        tag_stats = ops_obj.groupby(df_tags, ["tag"], ["movieId"], "count")

        tag_pairs = list(zip(tag_stats["tag"], tag_stats["movieId_count"]))
        tag_pairs.sort(key=lambda x: x[1], reverse=True)

        popular_tags = [t for t, _ in tag_pairs[:100]]

        selected_tag = st.selectbox("Choose a popular tag", options=popular_tags)

        st.write(f"Showing movies tagged with **{selected_tag}**:")

        # Filter tags for this tag
        filtered_tags = ops_obj.filter(df_tags, ["tag"], ["="], [selected_tag])

        # Join with movies
        mt = ops_obj.join(df_movies, filtered_tags, ["movieId"], how="inner")

        # Join with ratings to get avg rating per tagged movie
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


    with tab_query:
        st.markdown(
            '<p class="section-title">Manual Query Builder</p>',
            unsafe_allow_html=True,
        )
        st.write(
            "Build your own query by choosing the dataset and which functions "
            "to apply: **joins**, **filter**, **group by / aggregation**, **projection**, and **sorting**."
        )


        st.subheader("Step 0: Choose tables & joins")

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

        # First join
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

        # Build base dataframe according to join plan
        ops_local = functions()
        base_df_obj, base_suffix = get_df_and_suffix(base_table)
        current_df = base_df_obj 

        # Keep canonical 'movieId' from the left;
        # columns from joined tables get suffixes.
        if join1_enable and join1_table is not None:
            right_df, right_suffix = get_df_and_suffix(join1_table)
            current_df = ops_local.join(
                current_df,
                right_df,
                ["movieId"],
                how=join1_type,
                left_suffix="",          
                right_suffix=right_suffix,
            )

        if join2_enable and join2_table is not None:
            right_df2, right_suffix2 = get_df_and_suffix(join2_table)
            current_df = ops_local.join(
                current_df,
                right_df2,
                ["movieId"],              
                how=join2_type,
                left_suffix="",          
                right_suffix=right_suffix2,
            )

        working_df = current_df

        st.caption(
            "Current dataset = "
            + base_table
            + (f" {join1_type} join {join1_table}" if join1_enable and join1_table else "")
            + (f" {join2_type} join {join2_table}" if join2_enable and join2_table else "")
        )


        st.subheader("Step 1: Filter rows (WHERE)")

        apply_filter = st.checkbox("Apply filter", value=False)

        columns = []
        conditions = []
        values = []
        seps = []

        if apply_filter:
            cols_available = list(working_df.keys())
            ops_list = ["=", "!=", ">", "<", ">=", "<="]

            col1, col2, col3 = st.columns(3)
            with col1:
                f1_col = st.selectbox("Column 1", options=cols_available, key="f1_col")
            with col2:
                f1_op = st.selectbox("Condition 1", options=ops_list, key="f1_op")
            with col3:
                f1_val_str = st.text_input("Value 1", key="f1_val")

            if f1_val_str.strip() != "":
                columns.append(f1_col)
                conditions.append(f1_op)
                values.append(parse_value(f1_col, f1_val_str))
                seps.append("and")

            add_second = st.checkbox("Add second condition", value=False)
            if add_second:
                col4, col5, col6, col7 = st.columns(4)
                with col4:
                    f2_col = st.selectbox(
                        "Column 2", options=cols_available, key="f2_col"
                    )
                with col5:
                    f2_op = st.selectbox(
                        "Condition 2", options=ops_list, key="f2_op"
                    )
                with col6:
                    f2_val_str = st.text_input("Value 2", key="f2_val")
                with col7:
                    sep2 = st.selectbox(
                        "Combine with", options=["and", "or"], key="sep2"
                    )

                if f2_val_str.strip() != "":
                    columns.append(f2_col)
                    conditions.append(f2_op)
                    values.append(parse_value(f2_col, f2_val_str))
                    seps.append(sep2)

        if columns:
            working_df = ops_local.filter(working_df, columns, conditions, values, seps)
            working_df = engine_safe(working_df, "filter")
            if working_df is None:
                return  # stop query tab rendering here

        # ---------------- GROUP BY / GLOBAL AGG ----------------
        st.subheader("Step 2: Group by & aggregation (optional)")

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
                # Global aggregation: no group-by, aggregate over entire dataset
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

                # Implement as groupby on a constant column "_all"
                tmp_df = {k: v[:] for k, v in working_df.items()}
                tmp_df["_all"] = [1] * dict_len(working_df)

                tmp_df = ops_local.groupby(tmp_df, ["_all"], [agg_col], agg_type)
                tmp_df = engine_safe(tmp_df, "global aggregation")
                if tmp_df is None:
                    return

                working_df = tmp_df

        # ---------------- PROJECTION & SORT ----------------
        st.subheader("Step 3: Projection & sorting")

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
        st.dataframe(to_rows(working_df, cols=show_cols, limit=max_rows_query))

        st.caption(
            "This tab is a **manual query builder**. Depending on your choices, it "
            "chains together **joins** (inner / left / right / full between Movies, "
            "Ratings, and Tags), **filter**, **groupby / global aggregation**, "
            "**projection**, and **order_rows**."
        )


if __name__ == "__main__":
    main()
