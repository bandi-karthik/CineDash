# CineDash
A Lightweight we Application built using Streamlit on top of the movies and their rating datasets
it loads the available datasets, and parse them, making them ready for the analytics and data query for the users.

CineDash consists of the following 
-> A Data2APP model, purely wirtten in python from scratch to replicate the pandas features like

    1. Parser : reads the csv files

    2. Dataframe.py 
      which formats the parsed data into dictionaries in the form of key value pairs, and adds indexing for the fast querying of the data.
    
    3. function which used for the data querying like select_columns, orderby, groupby,aggregations like (sum,min,max,average), multi-joins, head, tail, limit.
    
    4. Operations (engine/ops.py) include,
        -> df_len(df) — count rows    
        -> head(df, rows=5) / tail(df, rows=5)
        -> select_columns(df, cols)
        -> set_index(df) — adds a simple index column
        -> filter(df, columns, conditions, values, seperators=[]) — supports multi-column AND/OR
        -> order_rows(df, type='asc', limit=None) — simple ascending/descending
        -> groupby(df, groupby_columns, agg_column, agg_type) — supports count/sum/min/max/avg
        
    5. deployed the functionality into an application using Streamlit.

### Datasets

MovieLens latest-small : https://grouplens.org/datasets/movielens/latest/

### Project Structure

CineDash/
├─ data/
│  ├─ movies.csv
│  ├─ ratings.csv
│  ├─ tags.csv
│  └─ links.csv
├─ engine/
│  ├─ parser.py        
│  ├─ dataframe.py     # dataframe creation from the parsed data , converts into dictionary of lists.
│  └─ ops.py           # all the operation like groupby, filter, orderby, projection, head,tail.
├─ webapp/
│  └─ streamlit_app.py # Streamlit UI 
├─ tests/
│  └─ tiny/...        
└─ README.md

### Launch the App

streamlit run webapp/streamlit_app.py


